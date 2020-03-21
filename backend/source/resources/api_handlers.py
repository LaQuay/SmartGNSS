import logging

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
            response = self.geo_repository.get_location_from_ip(ip)
            print(response)

            if response:
                return Response.success(response.json())
            return Response.error(GENERIC)

    class WIFI(Resource):
        def get(self, wifi_name):
            response = self.geo_repository.get_location_from_wifi(wifi_name)

            print(response)
            if response:
                return Response.success(response)
            return Response.error(GENERIC)
