# SmartGNSS

## Geolocation

### Via GNSS RAW
_To be filled_

### Via IP
Using `ipinfo.io` within its free tier. Sending an IP address.

### Via WiFi
[WiGLE Documentation](https://api.wigle.net/swagger#/) 

Using `wigle.net` within its free tier. Sending the SSID of a WiFi
router.

There is the possibility of sending coordinates to reduce the search
area.

_NOTE: Response is hardcoded since they have a limitation of 5 queries
per day._

## API Calls

### Get score for user information

#### Send
```
POST /geolocate/ HTTP/1.1
Host: localhost:5000
Content-Type: multipart/form-data; boundary=--------------------------016850107323449250282000
Content-Length: 267119
Connection: keep-alive
Content-Disposition: form-data; name="user_file"; 
filename="user_log_1.txt"
Content-Disposition: form-data; name="gps_latlon"
37.386,-122.1
Content-Disposition: form-data; name="ip_address"
8.8.8.8
Content-Disposition: form-data; name="wifi_ssid"
eduroam
```

#### Response
```
HTTP/1.0 200 OK
Content-Type: application/json
Server: Werkzeug/1.0.0 Python/3.7.2
```

```json
{
    "data": {
        "info": {
            "info": "Score obtained for location 37.386,-122.1",
            "help": "Score between 0 and 1 (max). From correlating the different inputs given by the user",
            "available_inputs": [
                "gps, gnss, ip, wifi"
            ]
        },
        "gnss": {
            "locations": [
                "41.3716595259, 2.13015067745"
            ],
            "score": 0.9587
        },
        "ip": {
            "locations": [
                "37.3860,-122.0838"
            ],
            "score": [
                0.0001
            ]
        },
        "wifi": {
            "locations": [
                "41.390132,2.112898",
                "41.381432,2.139105"
            ],
            "score": [
                0.9585,
                0.9587
            ]
        }
    },
    "error": null
}
```

### Geolocate a GNSS Raw Data

#### Send 
```
POST /geolocate/gnss/ HTTP/1.1
Host: localhost:5000
Content-Type: multipart/form-data; boundary=--------------------------016850107323449250282000
Content-Length: 266766
Connection: keep-alive
Content-Disposition: form-data; name="user_file"; 
filename="user_log_1.txt"
```

#### Response
```
HTTP/1.0 200 OK
Content-Type: application/json
Server: Werkzeug/1.0.0 Python/3.7.2
```

```json
{"data": "41.379515, 2.141006", "error": null}
```

### Geolocate an IP

#### Send 
```
GET /geolocate/ip/8.8.8.8 HTTP/1.1
Host: localhost:5000
```

#### Response
```
HTTP/1.0 200 OK
Content-Type: application/json
Server: Werkzeug/1.0.0 Python/3.7.2
```
```json
{
    "data": {
        "ip": "8.8.8.8",
        "hostname": "dns.google",
        "city": "Mountain View",
        "region": "California",
        "country": "US",
        "loc": "37.3860,-122.0838",
        "org": "AS15169 Google LLC",
        "postal": "94035",
        "timezone": "America/Los_Angeles"
    },
    "error": null
}
```

### Geolocate a WiFi SSID

#### Send
```
GET /geolocate/wifi/eduroam HTTP/1.1
Host: localhost:5000
```

#### Response
```
HTTP/1.0 200 OK
Content-Type: application/json
Server: Werkzeug/1.0.0 Python/3.7.2
```
```json
{
    "data": {
        "success": true,
        "totalResults": 1,
        "first": 1,
        "last": 2,
        "resultCount": 2,
        "results": [
            {
                "trilat": 41.390132,
                "trilong": 2.112898,
                "ssid": "eduroam",
                "qos": 0,
                "transid": "20191222-00000",
                "firsttime": "2019-12-01T08:00:00.000Z",
                "lasttime": "2019-12-01T16:00:00.000Z",
                "lastupdt": "2019-12-01T16:00:00.000Z",
                "netid": "00:02:F3:37:F8:A6",
                "name": "UPC - Campus Nord",
                "type": "infra",
                "comment": null,
                "wep": "2",
                "bcninterval": 0,
                "freenet": "?",
                "dhcp": "?",
                "paynet": "?",
                "userfound": false,
                "channel": 1,
                "encryption": "wpa2",
                "country": "ES",
                "region": "CAT",
                "city": "Barcelona",
                "housenumber": "2, 4",
                "road": "Carrer de Dulcet",
                "postalcode": "08034"
            },
            ...
        ],
        "searchAfter": "14262474899",
        "search_after": 14262474899
    },
    "error": null
}
```