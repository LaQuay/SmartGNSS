import os
from flask import Flask, request, render_template
import requests
import werkzeug

app = Flask(__name__)



from flask_restful import reqparse


entry_parser = reqparse.RequestParser()
entry_parser.add_argument("value", type=str)
entry_parser.add_argument("date", type=str)

entry_parser.add_argument("user_file", type=werkzeug.datastructures.FileStorage, location="files")

@app.route('/handle_form', methods=['POST'])
def handle_form():

    key="fileUpload"
    #key="upload"

    print(request.headers)
    print(request)
    print(type(request))
    print(request.files.keys())
    print(request.content_length)

    print("**1")
    raw_gnss_args = entry_parser.parse_args()
    user_file = raw_gnss_args["user_file"]
    print("**2")
    print(user_file)

    print(request.files[key])
    print(type(request.files[key]))
    file = request.files[key]
    # L'unica manera que veig el fitxer es guardantlo. Els reads no emfuncionen (si l'envio des de l'android no va, i faig un curl si que van els reads)
    file.save('/tmp/foo')
    print(file.read())



    #print("Posted file: {}".format(request.files['file']))
    #file = request.files['file']
    return ""

@app.route("/")
def index():
    return render_template("index.html");   


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)

