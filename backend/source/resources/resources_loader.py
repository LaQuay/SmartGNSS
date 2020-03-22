# -*- coding: utf-8 -*-
from flask_cors import CORS

from resources.api_handlers import EntryHandler, GeolocationHandler


class Resources:
    def init_cors(app):
        cors_origins = [
            "http://localhost:3000", "http://192.168.1.64:3000"]
        CORS(app, resources=r'/entries/*, /geolocate/*', origins=cors_origins)

    @staticmethod
    def load_resources(api):
        api.add_resource(EntryHandler.Entries, '/entries/',
                         strict_slashes=False)

        api.add_resource(EntryHandler.Entry, '/entries/<string:entry_id>',
                         strict_slashes=False)

        api.add_resource(GeolocationHandler.Location, '/geolocate/',
                         strict_slashes=False)

        api.add_resource(GeolocationHandler.IP, '/geolocate/ip/<string:ip>',
                         strict_slashes=False)

        api.add_resource(GeolocationHandler.GNSS, '/geolocate/gnss/',
                         strict_slashes=False)
        
        api.add_resource(GeolocationHandler.WIFI, '/geolocate/wifi/<string:wifi_name>',
                         strict_slashes=False)
