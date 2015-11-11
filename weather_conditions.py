#!/usr/bin/env python

import os, sys
import urllib2
import time
import logging
import json
from string import Template

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

fh = logging.Formatter("[%(asctime)s] %(levelname)s: %(filename)s:%(funcName)s:%(lineno)d - %(message)s")
ch.setFormatter(fh)
logger.addHandler(ch)

'''
Using the weath API made available by Weather Underground:
 http://www.wunderground.com/weather/api/d/docs
'''

config = {
    'apikey': '35dd69aac64cd95c',
    'servicename': 'geolookup/conditions',
    'countryname': 'Indonesia',
    'cityname': 'Jakarta'
}

tmpl = Template('http://api.wunderground.com/api/${apikey}/${servicename}/q/${countryname}/${cityname}.json')

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

