# -*- coding: utf-8 -*-
import requests
from requests.auth import HTTPBasicAuth

from repositories import geo_fixture
from utils import math

# IPINFO
ipinfotoken = "6f49f36f5c1a2b"

# WIGLE
wigle_username = 'AIDab983b5aaf3057154bd3e54400b69fca'
wigle_password = 'd8510792dba5603a5789576ec298ebd7'

fake_wigle = True

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
    def get_ip_score(ip_locations, user_gps_location):
        # TODO It just takes the first location
        first_lon = ip_locations[0].split(",")[1]
        first_lat = ip_locations[0].split(",")[0]
        second_lon = user_gps_location.split(",")[1]
        second_lat = user_gps_location.split(",")[0]

        distance = math.haversine(first_lon, first_lat, second_lon, second_lat)

        return distance / MAX_SCORE

    @staticmethod
    def get_wifi_score(wifi_locations, user_gps_location):
        # TODO It just takes the first location
        first_lon = wifi_locations[0].split(",")[1]
        first_lat = wifi_locations[0].split(",")[0]
        second_lon = user_gps_location.split(",")[1]
        second_lat = user_gps_location.split(",")[0]

        distance = math.haversine(first_lon, first_lat, second_lon, second_lat)

        return distance / MAX_SCORE
