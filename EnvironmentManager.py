#!/usr/bin/env python

import os, sys
import time
import logging
import ConfigParser
import json
from argparse import ArgumentParser

import Adafruit_DHT
from rcswitch import RCSwitch
import solarcalc

argParser = ArgumentParser(description='Monitor and attemt to manage an environment')
argParser.add_argument("-v","--verbose",dest="verbose",action="store_true",default=False,
                    help="output verbose log messages")
argParser.add_argument("-d","--debug",dest="debug",action="store_true",default=False,
                    help="output debug log messages")
argParser.add_argument("-c","--config",dest="config",default="EnvironmentManager.cfg",
                    metavar="CONFIG",help="use configuration from CONFIG file (ConfigParser compatible)")
argParser.add_argument("-l","--logfile",dest="logfile",default="EnvironmentManager.log",
                    metavar="LOGFILE",help="output logging to LOGFILE")

options = argParser.parse_args()

if options.debug == True:
    logLevel = logging.DEBUG
elif options.verbose == True:
    logLevel = logging.INFO
else:
    logLevel = logging.WARN

logger = logging.getLogger()
logger.setLevel(logLevel)

logFd = None
try:
    logFd = open(options.logfile,"w",0)
except Exception as e:
    sys.stderr.write("Unable to open logfile '%s': %s\n"%(options.logfile,e))
    sys.exit(1)
if logFd is None:
    sys.stderr.write("Unabled to get logfile file descriptor. Aborting.\n")
    sys.exit(1)
ch = logging.StreamHandler(logFd)
ch.setLevel(logLevel)

fh = logging.Formatter("[%(asctime)s] %(levelname)s: %(filename)s:%(funcName)s:%(lineno)d - %(message)s")
ch.setFormatter(fh)
logger.addHandler(ch)

cfgParser = ConfigParser.ConfigParser()
config = None
if options.config is not None:
    try:
        config = cfgParser.read(options.config)
    except Exception as e:
        logger.error("Enable to read config file '%s': %s",options.config,e)
else:
    logger.error("No configuration file specified and default not found. Aborting.")
    sys.exit(1)

class EnvironmentManager():

    def __init__(self,config):
        self.config = config
        self.updateTimes()
        pass

    def updateTimes(self):
        newtime = time.localtime()
        newdate = time.mktime((newtime[0],newtime[1],newtime[2],0,0,0,newtime[6],newtime[7],newtime[8]))
        doUpdate = False
        if hasattr(self,'time') is False or self.time is None:
            doUpdate = True
        if hasattr(self,'date') and self.date < newdate:
            doUpdate = True
        if doUpdate is True:
            self.time = newtime
            self.date = newdate
            dst = False
            if newtime[8] == 1:
                dst = True
            tzoffset = time.timezone / (60*60) * -1
            julianday = solarcalc.getJulianDay(newtime[0],newtime[1],newtime[2])
            lat = float(self.config.get('location','latitude'))
            long = float(self.config.get('location','longitude'))
            logger.info("location: %.03f, %.03f",lat,long)
            self.sunrise = solarcalc.calcSunriseSet(1,julianday,lat,long,tzoffset,dst)
            self.sunrise = solarcalc.calcSunriseSet(0,julianday,lat,long,tzoffset,dst)



if __name__ == "__main__":
    manager = EnvironmentManager(cfgParser)
    logger.info("To be continued...")
    sys.stdout.write("To be continued...\n")
    sys.exit(0)
