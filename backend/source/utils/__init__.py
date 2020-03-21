import logging
import json
from datetime import datetime
import statistics
import zipfile


logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            # For consistency with the API, we add the timezone marker Z
            return o.isoformat() + "Z"
        else:
            return json.JSONEncoder.default(self, o)


class JSONDecoder:
    def decode(self, text):
        return json.loads(text)


def construct_db_uri(db_configuration):
    return "postgresql://%s:%s@%s:%s/%s" % (
        db_configuration["user"], db_configuration["password"],
        db_configuration["host"], db_configuration["port"],
        db_configuration["database"])


# TODO Move to ENV
db_uri = construct_db_uri(
    {
        "user": "postgres",
        "password": "",
        "host": "postgres",
        "port": "5432",
        "database": "api_db"
    }
)


def jason_csv_to_coords(jason_csv):
    lats = []
    lons = []
    for line in jason_csv:
        line_split = line.split(",")
        lats.append(line_split[2])
        lons.append(line_split[3])
    return [statistics.mean(lats), statistics.mean(lons)]


def unzip_result(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall("data")
