#!/usr/bin/env python

import os, sys
import urllib2
import time
import logging
import json
import ConfigParser
from string import Template
from argparse import ArgumentParser

cfgParser = ConfigParser.ConfigParser()

parser = ArgumentParser(description='Communicate with the WeatherUnderground API')
parser.add_argument("-v","--verbose",dest="verbose",action="store_true",default=False,
                    help="output verbose log messages")
parser.add_argument("-d","--debug",dest="debug",action="store_true",default=False,
                    help="output debug log messages")
parser.add_argument("-c","--config",dest="config",default=None,
                    metavar="CONFIG",help="use configuration from CONFIG file (ConfigParser compatible)")
parser.add_argument("-k","--api-key",dest="apikey",default=None,
                    metavar="APIKEY",help="use APIKEY when authenticating with the WeatherUnderground API")
parser.add_argument("-s","--service-name",dest="servicenames",default=[],action="append",
                    metavar="SERVICE",help="use SERVICE service from the WeatherUnderground API")
parser.add_argument("-l","--location",dest="location",default=None,
                    metavar="LOCATION",help="query WeatherUnderground for location LOCATION (US City/State | US Zipcode | Country/City | Latitude,Longitude | Airport Code | PWS ID)")

options = parser.parse_args()

if options.debug == True:
    logLevel = logging.DEBUG
elif options.verbose == True:
    logLevel = logging.INFO
else:
    logLevel = logging.WARN

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logLevel)

fh = logging.Formatter("[%(asctime)s] %(levelname)s: %(filename)s:%(funcName)s:%(lineno)d - %(message)s")
ch.setFormatter(fh)
logger.addHandler(ch)

(fileConfig, apikey, servicenames, location) = (None, None, [], None)
if options.config is not None:
    try:
        fileConfig = cfgParser.read(options.config)
    except Exception as e:
        logger.error("Problem reading configuration from '%s'. Aborting.", options.config)
        sys.exit(1)
if options.apikey is None:
    if fileConfig is not None:
        try:
            apikey = cfgParser.get('default','apikey')
        except Exception as e:
            logger.error("Unable to find key 'apikey' in section 'default' from config file '%s': %s",
                         options.config, e)
            sys.exit(1)
    else:
        logger.error("No API key provided. Unable to continue.")
        sys.exit(1)
else:
    apikey = options.apikey
if len(options.servicenames) == 0:
    if fileConfig is not None:
        try:
            servicenames = cfgParser.get('default','servicenames').split()
        except Exception as e:
            logger.error("Unable to find key 'servicenames' in section 'default' from config file '%s': %s",
                         options.config, e)
            sys.exit(1)
    else:
        logger.error("No service names provided to query. Unable to continue.")
        sys.exit(1)
else:
    servicenames = options.servicenames
if options.location is None:
    if fileConfig is not None:
        try:
            location = cfgParser.get('default','location')
        except Exception as e:
            logger.error("Unable to find key 'location' in section 'default' from config file '%s': %s",
                         options.config, e)
            sys.exit(1)
    else:
        logger.error("No location provided. Unable to continue.")
        sys.exit(1)
else:
    location = options.location

'''
Using the weath API made available by Weather Underground:
 http://www.wunderground.com/weather/api/d/docs
'''

config = {
    'apikey': apikey,
    'feature': '/'.join(servicenames),
    'query': location
}

tmpl = Template('http://api.wunderground.com/api/${apikey}/${feature}/q/${query}.json')

url = tmpl.substitute(config)
logger.info("Requesting URL '%s'", url)

response = None

try:
    response = urllib2.urlopen(url)
except Exception as e:
    logger.error("Error connecting to URL '%s': %s", url, e)
    sys.exit(1)

data = response.read()
logger.info("Request return HTTP %d %s", response.code, response.msg)
response.close()
logger.info("Response data:\n%s", data)

