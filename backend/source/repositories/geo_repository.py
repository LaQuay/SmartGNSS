# -*- coding: utf-8 -*-
import json
import os
import time
import urllib.request

import requests
from haversine import haversine
from requests.auth import HTTPBasicAuth

import utils
from repositories import geo_fixture

# IPINFO

ipinfotoken = "6f49f36f5c1a2b"

# WIGLE
wigle_username = 'AIDab983b5aaf3057154bd3e54400b69fca'
wigle_password = 'd8510792dba5603a5789576ec298ebd7'
fake_wigle = True

# JASON
JASON_API_KEY = "ARGONAUT.PUB.609B-4D9E-80B7"
JASON_SECRET_TOKEN = "1DD6EB-D09E73-17FEB2-41952F-5BB20C"
FINISHED_RESPONSE_STATUS = "FINISHED"
SLEEP_TIME = 5

# SCORES
MIN_SCORE = 0
MAX_SCORE = 10000


class GeoRepository:
    @staticmethod
    def get_info_from_ip(ip):
        return requests.get(f"https://www.ipinfo.io/{ip}?token={ipinfotoken}")

    @staticmethod
    def get_info_from_wifi(wifi_name):
        payload = {'ssidlike': wifi_name}

        if fake_wigle:
            return geo_fixture.eduroam

        response = requests.get(url='https://api.wigle.net/api/v2/network/search',
                                params=payload,
                                auth=HTTPBasicAuth(wigle_username, wigle_password)).json()

        return response

    @staticmethod
    def get_locations_from_ip(ip):
        response = requests.get(f"https://www.ipinfo.io/{ip}?token={ipinfotoken}")

        locations = response.json()["loc"]

        if isinstance(locations, list):
            return locations
        return [locations]

    @staticmethod
    def get_locations_from_wifi(wifi_name):
        payload = {'ssidlike': wifi_name}

        if fake_wigle:
            response = geo_fixture.eduroam
        else:
            response = requests.get(url='https://api.wigle.net/api/v2/network/search',
                                    params=payload,
                                    auth=HTTPBasicAuth(wigle_username, wigle_password)).json()

        locations = []
        for result in response["results"]:
            locations.append(f"{result['trilat']},{result['trilong']}")

        return locations

    @staticmethod
    def get_locations_from_gnss(user_file):
        user_file_filename = user_file.filename
        user_file.save(user_file_filename)

        os.system(f"curl -X POST  "
                  f"-H 'accept: application/json' "
                  f"-H 'Content-Type: multipart/form-data' "
                  f"-H 'ApiKey: {JASON_API_KEY}' "
                  f"-F token={JASON_SECRET_TOKEN} "
                  f"-F type=GNSS "
                  f"-F 'rover_file=@{user_file_filename}' "
                  f"'http://api-argonaut.rokubun.cat/api/processes/' > tmp")

        request_id = json.loads(open("tmp").read())["id"]
        os.system("rm tmp")

        headers = {
            'accept': 'application/json',
            'Content-Type': 'multipart/form-data',
            'ApiKey': f'{JASON_API_KEY}'
        }

        while True:
            response = requests.get(
                f'http://api-argonaut.rokubun.cat/api/processes/{request_id}?token='
                f'{JASON_SECRET_TOKEN}',
                headers=headers)
            request_status = response.json()["process"]["status"]
            if request_status == FINISHED_RESPONSE_STATUS:
                results = response.json()["results"]
                for result in results:
                    if result["process_id"] == request_id:
                        result_url = result["url"]
                break
            time.sleep(SLEEP_TIME)

        # Unzip result
        result_zip = urllib.request.urlretrieve(result_url)
        utils.unzip_result(result_zip[0])

        # Read position from file
        csv_filename = user_file_filename.split(".")[0] + "_position_spp.csv"
        coords = utils.jason_csv_to_coords(f"data/{csv_filename}")

        return coords

    @staticmethod
    def get_ip_scores(ip_locations, user_gps_location):
        scores = []
        for ip_location in ip_locations:
            first_gps_latlon = [float(ip_location.split(",")[0]),
                                float(ip_location.split(",")[1])]
            second_gps_latlon = [float(user_gps_location.split(",")[0]),
                                 float(user_gps_location.split(",")[1])]

            score = haversine(first_gps_latlon, second_gps_latlon) / MAX_SCORE
            scores.append(round(score, 4))

        return scores

    @staticmethod
    def get_wifi_scores(wifi_locations, user_gps_location):
        scores = []
        for wifi_location in wifi_locations:
            first_gps_latlon = [float(wifi_location.split(",")[0]),
                                float(wifi_location.split(",")[1])]
            second_gps_latlon = [float(user_gps_location.split(",")[0]),
                                 float(user_gps_location.split(",")[1])]

            score = haversine(first_gps_latlon, second_gps_latlon) / MAX_SCORE
            scores.append(round(score, 4))

        return scores

    @staticmethod
    def get_gnss_score(user_gps_location_from_file, user_gps_location):
        first_gps_latlon = [float(user_gps_location_from_file.split(",")[0]),
                            float(user_gps_location_from_file.split(",")[1])]
        second_gps_latlon = [float(user_gps_location.split(",")[0]),
                             float(user_gps_location.split(",")[1])]
        distance = haversine(first_gps_latlon, second_gps_latlon)
        score = distance / MAX_SCORE

        return round(score, 4)
