import logging
import time

import requests
from flask_restful import reqparse
import werkzeug

from errors.api_errors import GENERIC, NOT_EXISTS_ID, FIELD_NOT_VALID
from models.models import Entry
from resources import Resource, Response
from translators import api_translators as translator
from validators import api_validators as validator

logger = logging.getLogger(__name__)

entry_parser = reqparse.RequestParser()
entry_parser.add_argument("value", type=str)
entry_parser.add_argument("date", type=str)

entry_parser.add_argument("user_file", type=werkzeug.datastructures.FileStorage, location="files")

JASON_API_KEY = "ARGONAUT.PUB.609B-4D9E-80B7"
JASON_SECRET_TOKEN = "3254E4-1E0D4A-922C6E-B3E631-9D3228"
FINISHED_RESPONSE_STATUS = "FINISHED"
SLEEP_TIME = 5


class EntryHandler:
    class Entries(Resource):
        def get(self):
            response = self.repository.get_all_entries()

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

            result = self.repository.add_entry(entry)

            if result:
                return Response.success({"internal_id": result})

            return Response.error(GENERIC)

    class Entry(Resource):
        def get(self, entry_id):
            response = self.repository.get_entry(entry_id)

            if response:
                return Response.success(translator.entry_translator(response))
            return Response.error(NOT_EXISTS_ID)

        def put(self, entry_id=None):
            args = entry_parser.parse_args()

            response = self.repository.get_entry(entry_id)
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

            response = self.repository.update_entry(entry_id, entry)

            if response:
                return Response.success({"internal_id": response})

            return Response.error(GENERIC)

        def delete(self, entry_id=None):
            response = self.repository.get_entry(entry_id)

            if response:
                result = self.repository.delete_entry(entry_id)
                if result:
                    return Response.success({"internal_id": result})
            return Response.error(NOT_EXISTS_ID)


ipinfotoken = "6f49f36f5c1a2b"


class GeolocationHandler:
    class IP(Resource):
        def get(self, ip):
            response = requests.get(f"https://www.ipinfo.io/{ip}?token={ipinfotoken}")

            if response:
                return Response.success(response.json())
            return Response.error(GENERIC)

    class GNSS(Resource):
        def post(self):
            args = entry_parser.parse_args()
            user_file = args["user_file"]

            # TODO: read position from file

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

            # TODO
            # Unzip result
            # Read position from file
            # Compare with provided position
            # If jason_position == provided position
            # Return True
            # Else
            # Return False

            return Response.success({"data": True})
