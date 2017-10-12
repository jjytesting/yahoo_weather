# -*- coding:utf8 -*-
# !/usr/bin/env python
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook(): 
    req = request.get_json(silent=True, force=True) 

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req) #jj: This function is for requesting to google

    res = json.dumps(res, indent=4) #jj: It create json file with yahoo returned result
    # print(res)
    r = make_response(res) #jj: I guess it make jason file as sending format (?)
    r.headers['Content-Type'] = 'application/json' #jj: I don't know what it is..
    return r #jj: I guess this actually return the result


def processRequest(req):
    if req.get("result").get("action") != "yahooWeatherForecast": #jj: this keyword is for the api.ai action name predefined by bot maker
        return {} #jj: why does it return empty dictionary?
    baseurl = "https://query.yahooapis.com/v1/public/yql?" #jj: this seems call rest api beginning part to use yahoo api
    yql_query = makeYqlQuery(req) # jj: It seems parsing json format to url query.
    if yql_query is None: #jj: I understood it is failed to make url query.. why does it return empty dictionary?
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json" #jj: if the makeYqlQuery made url query well, it combine url query to call yahoo api... but when I type it on the browser address area.. I can not get the result..
    result = urlopen(yql_url).read() # jj: this seems calling yahoo api and get result from it
    data = json.loads(result) # jj: and it seems convert result to json format again
    res = makeWebhookResult(data) # jj: I think it makes the result format to fit api.ai require..
    return res


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWebhookResult(data):
    # jj: I think this function is for parsing yahoo result.. and the bot maker only want to have location, condition(temp), units(for temp unit) in whole query result from yahoo
    # jj: And it is in the result section > channel section > "location", "item > condition", "units"

    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    # jj: I guess this makes full speech text to send api.ai
    speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    #jj: so this part is for making final format of result what I see in api.ai fullfillment documentation.
    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000)) #jj: I don't understand this part

    print("Starting app on port %d" % port) #jj: where does it print? and why?

    app.run(debug=False, port=port, host='0.0.0.0') #jj: I don't understand this part.
