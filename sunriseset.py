#!/usr/bin/env python

import os, sys
import requests
import time
import logging
import logging.handlers
import json
import configparser
from string import Template
from argparse import ArgumentParser

cfgParser = configparser.ConfigParser()

parser = ArgumentParser(description='Communicate with the Sunrise-Sunset.org API')
parser.add_argument("-c","--config",dest="config",default=None,
                    metavar="CONFIG",help="use configuration from CONFIG file (configparser compatible)")
parser.add_argument("-d","--debug",dest="debug",action="store_true",default=False,
                    help="output debug log messages")
parser.add_argument("-g","--longitude",dest="longitude",default=None,
                    metavar="LONGITUDE",help="query using longitude LONGITUDE")
parser.add_argument("-l","--logfile",dest="logfile",default=None,
                    metavar="LOGFILE",help="write logging output to LOGFILE")
parser.add_argument("-s","--savefile",dest="savefile",default=None,
                    metavar="SAVEFILE",help="save query results to SAVEFILE")
parser.add_argument("-t","--latitude",dest="latitude",default=None,
                    metavar="LATITUDE",help="query using latitude LATITUDE")
parser.add_argument("-v","--verbose",dest="verbose",action="store_true",default=False,
                    help="output verbose log messages")

options = parser.parse_args()

if options.debug == True:
    logLevel = logging.DEBUG
elif options.verbose == True:
    logLevel = logging.INFO
else:
    logLevel = logging.WARN

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

fh = logging.Formatter("[%(asctime)s] %(levelname)s: %(filename)s:%(lineno)d - %(message)s")
ch = logging.StreamHandler()
if options.logfile is not None:
    ch = None
    try:
        ch = logging.handlers.RotatingFileHandler(filename=options.logfile,maxBytes=1024000)
    except IOError as e:
        logger.warn("Unable to open file '%s' for writing: %s. Will continue without.")
ch.setLevel(logLevel)
ch.setFormatter(fh)
logger.addHandler(ch)

(fileConfig, apikey, servicenames, location) = (None, None, [], None)
if options.config is not None:
    try:
        fileConfig = cfgParser.read(options.config)
        logLevelCfg = cfgParser.get('default','loglevel').upper()
        if logLevelCfg is not None and hasattr(logging,logLevelCfg):
            logger.setLevel(getattr(logging,logLevelCfg))
            ch.setLevel(getattr(logging,logLevelCfg))
    except Exception as e:
        logger.error("Problem reading configuration from '%s': %s. Aborting.", options.config, e)
        sys.exit(1)

(latitude,longitude) = (0.0,0.0)
if options.latitude is None:
    if fileConfig is not None:
        try:
            latitude = cfgParser.get('default','latitude')
        except Exception as e:
            logger.error("Unable to find key 'latitude' in section 'default' from config file '%s': %s",
                         options.config, e)
            sys.exit(1)
    else:
        logger.error("No latitude provided. Unable to continue.")
        sys.exit(1)
else:
    latitude = options.latitude

if options.longitude is None:
    if fileConfig is not None:
        try:
            longitude = cfgParser.get('default','longitude')
        except Exception as e:
            logger.error("Unable to find key 'longitude' in section 'default' from config file '%s': %s",
                         options.config, e)
            sys.exit(1)
    else:
        logger.error("No longitude provided. Unable to continue.")
        sys.exit(1)
else:
    longitude = options.longitude

'''
Using the API made available by Sunrise-Sunset.org:
 http://www.sunrise-sunset.org/api/
'''

config = {
    'formatted': 0,
    'latitude': latitude,
    'longitude': longitude
}

tmpl = Template('http://api.sunrise-sunset.org/json?lat=${latitude}&lng=${longitude}&formatted=${formatted}')

url = tmpl.substitute(config)
logger.info("Requesting URL '%s'", url)

response = None

try:
    response = requests.get(url)
except Exception as e:
    logger.error("Error connecting to URL '%s': %s", url, e)
    sys.exit(1)

#data = response.json()
obj = response.json()
logger.info("Request return HTTP %d", response.status_code)
response.close()
#obj = None
#try:
#    obj = json.loads(data)
#except Exception as e:
#    logger.error("Problem parsing received data as JSON: %s", e)
#    sys.exit(1)
logger.debug("Response data:\n%s", json.dumps(obj, sort_keys=True, indent=4, separators=(',',': ')))

eventSequence = (
    'astronomical_twilight_begin',
    'nautical_twilight_begin',
    'civil_twilight_begin',
    'sunrise',
    'solar_noon',
    'sunset',
    'civil_twilight_end',
    'nautical_twilight_end',
    'astronomical_twilight_end'
)

saveData = {}
for e in eventSequence:
    if obj.get('results') is None:
        logger.error("Result object has no 'results' key")
        sys.exit(1)
    if obj.get('results').get(e) is None:
        logger.error("Results object has no '%s' key", e)
        sys.exit(1)
    nowMark = ''
    v = obj.get('results').get(e)
    v = v.replace("+00:00"," UTC")
    utcTuple = time.strptime(v,"%Y-%m-%dT%H:%M:%S %Z")
    utcEpoch = time.mktime(utcTuple)
    localEpoch = utcEpoch - time.timezone
    localTuple = time.localtime(localEpoch)
    logger.info("%27s: %s %s", e, time.asctime(localTuple), nowMark)
    #logger.info("%s: %s", e, v)
    saveData[e] = localEpoch

if options.savefile is not None:
    fh = None
    try:
        fh = open(options.savefile, "w")
        json.dump(saveData,fh)
        fh.close()
    except Exception as e:
        logger.error("Unable to write to file '%s': %s", options.savefile, e)
        sys.exit(1)


