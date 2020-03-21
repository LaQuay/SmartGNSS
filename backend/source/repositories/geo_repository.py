# -*- coding: utf-8 -*-
import requests
from requests.auth import HTTPBasicAuth

# IPINFO
ipinfotoken = "6f49f36f5c1a2b"

# WIGLE
wigle_username = 'AID9948069cf19b06660140b30dfebc3fb4'
wigle_password = '8420f580c5541b8fac2a556327258450'


class GeoRepository:
    @staticmethod
    def get_location_from_ip(ip):
        return requests.get(f"https://www.ipinfo.io/{ip}?token={ipinfotoken}")

    @staticmethod
    def get_location_from_wifi(wifi_name):
        payload = {'ssidlike': wifi_name}

        response = requests.get(url='https://api.wigle.net/api/v2/network/search',
                                params=payload,
                                auth=HTTPBasicAuth(wigle_username, wigle_password)).json()

        return response
