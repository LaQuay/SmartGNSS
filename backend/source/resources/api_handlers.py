import logging

import werkzeug
from flask_restful import reqparse

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
location_parser.add_argument("user_file", type=werkzeug.datastructures.FileStorage,
                             location="files")
location_parser.add_argument("gps_latlon", type=str)
location_parser.add_argument("ip_address", type=str)
location_parser.add_argument("wifi_ssid", type=str)


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
        def post(self):
            raw_gnss_args = location_parser.parse_args()
            user_file = raw_gnss_args["user_file"]

            user_location_from_file = self.geo_repository.get_locations_from_gnss(user_file)

            return Response.success(user_location_from_file)

    class WIFI(Resource):
        def get(self, wifi_name):
            response = self.geo_repository.get_info_from_wifi(wifi_name)

            print(response)
            if response:
                return Response.success(response)
            return Response.error(GENERIC)

    class Location(Resource):
        def post(self):
            args = location_parser.parse_args()

            gps_latlon = args["gps_latlon"]
            ip_address = args["ip_address"]
            wifi_ssid = args["wifi_ssid"]
            user_file = args["user_file"]

            print("Obtaining IP Locations")
            ip_locations = self.geo_repository.get_locations_from_ip(ip_address)
            print(f"IP Locations: {ip_locations}")

            print("Obtaining WiFi SSID locations")
            wifi_locations = self.geo_repository.get_locations_from_wifi(wifi_ssid)
            print(f"WiFi SSID Locations: {wifi_locations}")

            print("Obtaining GNSS location")
            gnss_location = self.geo_repository.get_locations_from_gnss(user_file)
            print(f"GNSS Location: {gnss_location}")

            score_ip = self.geo_repository.get_ip_scores(ip_locations, gps_latlon)
            score_wifi = self.geo_repository.get_wifi_scores(wifi_locations, gps_latlon)
            score_gnss = self.geo_repository.get_gnss_score(gnss_location, gps_latlon)

            return Response.success({
                "info": {
                    "info": f"Score obtained for location {gps_latlon}",
                    "help": "Score between 0 and 1 (max). From correlating the different inputs "
                            "given by the user",
                    "available_inputs": ["gps, gnss, ip, wifi"]
                },
                "gnss": {
                    "locations": [gnss_location],
                    "score": score_gnss
                },
                "ip": {
                    "locations": ip_locations,
                    "score": score_ip
                },
                "wifi": {
                    "locations": wifi_locations,
                    "score": score_wifi
                }
            })
