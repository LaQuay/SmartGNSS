import logging
import time
import urllib.request

from flask_restful import reqparse
import werkzeug
from haversine import haversine

import utils
from errors.api_errors import GENERIC, NOT_EXISTS_ID, FIELD_NOT_VALID
from models.models import Entry
from resources import Resource, Response
from translators import api_translators as translator
from validators import api_validators as validator

logger = logging.getLogger(__name__)

entry_parser = reqparse.RequestParser()
entry_parser.add_argument("value", type=str)
entry_parser.add_argument("date", type=str)

location_parser = reqparse.RequestParser()
location_parser.add_argument("gps", type=dict)
location_parser.add_argument("ip", type=dict)
location_parser.add_argument("wifi", type=dict)

entry_parser.add_argument("user_file", type=werkzeug.datastructures.FileStorage, location="files")

JASON_API_KEY = "ARGONAUT.PUB.609B-4D9E-80B7"
JASON_SECRET_TOKEN = "3254E4-1E0D4A-922C6E-B3E631-9D3228"
FINISHED_RESPONSE_STATUS = "FINISHED"
SLEEP_TIME = 5



class EntryHandler:
    class Entries(Resource):
        def get(self):
            response = self.api_repository.get_all_entries()

            return Response.success(
                [translator.entry_translator(entry) for entry in response])

        def post(self):
            args = entry_parser.parse_args()

            # Get Entry arguments
            if validator.is_value_valid(args["value"]):
                value = args["value"]
            else:
                return Response.error(FIELD_NOT_VALID)

            if validator.is_date_valid(args["date"]):
                date = args["date"]
            else:
                return Response.error(FIELD_NOT_VALID)

            entry = Entry(value=value, date=date)

            result = self.api_repository.add_entry(entry)

            if result:
                return Response.success({"internal_id": result})

            return Response.error(GENERIC)

    class Entry(Resource):
        def get(self, entry_id):
            response = self.api_repository.get_entry(entry_id)

            if response:
                return Response.success(translator.entry_translator(response))
            return Response.error(NOT_EXISTS_ID)

        def put(self, entry_id=None):
            args = entry_parser.parse_args()

            response = self.api_repository.get_entry(entry_id)
            if not response:
                return Response.error(NOT_EXISTS_ID)

            # Get Entry arguments
            if validator.is_value_valid(args["value"]):
                value = args["value"]
            else:
                return Response.error(FIELD_NOT_VALID)

            if validator.is_date_valid(args["date"]):
                date = args["date"]
            else:
                return Response.error(FIELD_NOT_VALID)

            entry = {
                "value": value,
                "date": date
            }

            response = self.api_repository.update_entry(entry_id, entry)

            if response:
                return Response.success({"internal_id": response})

            return Response.error(GENERIC)

        def delete(self, entry_id=None):
            response = self.api_repository.get_entry(entry_id)

            if response:
                result = self.api_repository.delete_entry(entry_id)
                if result:
                    return Response.success({"internal_id": result})
            return Response.error(NOT_EXISTS_ID)


class GeolocationHandler:
    class IP(Resource):
        def get(self, ip):
            response = self.geo_repository.get_info_from_ip(ip)
            print(response)

            if response:
                return Response.success(response.json())
            return Response.error(GENERIC)

    class GNSS(Resource):
        def post(self, gps):
            gps_latlon = gps.split(",")

            raw_gnss_args = entry_parser.parse_args()
            user_file = raw_gnss_args["user_file"]

            headers = {
                'accept': 'application/json',
                'Content-Type': 'multipart/form-data',
                'ApiKey': f'{JASON_API_KEY}',
            }
            files = {
                'type': (None, 'GNSS'),
                'rover_file': ('user_file.txt', user_file),
            }
            response = requests.post(f'http://api-argonaut.rokubun.cat/api/processes?token={JASON_SECRET_TOKEN}', headers=headers, files=files)
            request_id = response.json()["id"]

            while True:
                response = requests.get(f'http://api-argonaut.rokubun.cat/api/processes/{request_id}?token={JASON_SECRET_TOKEN}',
                                        headers=headers, files=files)
                request_status = response["process"]["status"]
                if request_status == FINISHED_RESPONSE_STATUS:
                    result_url = response["process"]["url"]
                    break
                time.sleep(SLEEP_TIME)

            # Unzip result
            result_zip = urllib.request.urlretrieve(result_url)
            results_folder = (result_zip.split("/")[-1]).split(".")[0]
            utils.unzip_result(result_zip)

            # Read position from file
            coords = utils.jason_csv_to_coords(f"data/{results_folder}")

            d = haversine(coords, gps_latlon)

            return Response.success({"data": d/10000})

    class WIFI(Resource):
        def get(self, wifi_name):
            response = self.geo_repository.get_info_from_wifi(wifi_name)

            print(response)
            if response:
                return Response.success(response)
            return Response.error(GENERIC)

    class Location(Resource):
        def get(self):
            args = location_parser.parse_args()

            gps_info = args.get("gps", None)
            gps_latlon = gps_info.get("latlon", None)

            ip_info = args.get("ip", None)
            ip_address = None
            if ip_info is not None:
                ip_address = ip_info.get("address", None)

            wifi_info = args.get("wifi", None)
            wifi_ssid = None
            if wifi_info is not None:
                wifi_ssid = wifi_info.get("ssid", None)

            ip_locations = self.geo_repository.get_locations_from_ip(ip_address)
            wifi_locations = self.geo_repository.get_locations_from_wifi(wifi_ssid)

            score_ip = self.geo_repository.get_ip_score(ip_locations, gps_latlon)

            score_wifi = self.geo_repository.get_wifi_score(wifi_locations, gps_latlon)

            return Response.success({
                "info": {
                    "info": f"Score obtained for location {gps_latlon}",
                    "help": "Score between 0 and 1 (max). From correlating the different inputs "
                            "given by the user",
                    "available_inputs": ["gps, ip, wifi"]
                },
                "ip": {
                    "locations": ip_locations,
                    "score": round(score_ip, 4)
                },
                "wifi": {
                    "locations": wifi_locations,
                    "score": round(score_wifi, 4)
                }
            })
