#!/usr/bin/env python

import os, sys
import subprocess
import errno
import fcntl
import psutil
import requests
import time
import datetime
import logging
import logging.handlers
import json
from string import Template
from argparse import ArgumentParser

lockFile = "/tmp/LightsManager.lock"
lockFd = None
lastPid = None
if os.path.exists(lockFile):
    try:
        lockFd = open(lockFile,'r')
    except IOError as e:
        sys.stderr.write("Error: unable to open lock file '%s' for reading: %s\n" % (lockFile, e))
        sys.exit(1)

    lastPid = lockFd.read()
    if len(lastPid) > 0:
        lastPid = int(lastPid.strip())
    lockFd.close()

try:
    lockFd = open(lockFile,'w')
except IOError as e:
    sys.stderr.write("Error: unable to open lock file '%s' for writing: %s.\n" % (lockFile, e))
    sys.exit(1)
##
# TODO: still need to finish locking logic
#
try:
    rv = fcntl.flock(lockFd, fcntl.LOCK_EX|fcntl.LOCK_NB)
except OSError as e:
    sys.stderr.write("Warning: lock file last held by '%d'. Checking to see if that PID still running.\n" % (lastPid))
    if lastPid and psutil.pid_exists(lastPid):
        sys.stderr.write("Warning: PID '%d' found to be running. Checking to see if that is us.\n" % (lastPid))
        for process in psutil.process_iter():
            if process.pid == lastPid:
                if sys.argv[1] == process.cmdline()[1]:
                    sys.stderr.write("Error: unable to lock lock file '%s': %s. Still held by '%d' (%s).\n" % (lockFile, e, process.pid, process.cmdline()[1]))
                    sys.exit(1)
                else:
                    sys.stderr.write("Warning: PID '%d' is not us: %s != %s\n" % (process.pid, process.cmdline()[1], sys.argv[1]))
                break
        pass
    else:
        pass
lockFd.write(str(os.getpid()))

##
# Process command-line options
#
parser = ArgumentParser(description='Manage configured lights')
parser.add_argument("-c","--config",dest="config",default=None,
                    metavar="CONFIG",help="use configuration from CONFIG file (JSON serialized)")
parser.add_argument("-d","--debug",dest="debug",action="store_true",default=False,
                    help="output debug log messages")
parser.add_argument("-t","--latitude",dest="latitude",default=None,
                    metavar="LATITUDE",help="query using latitude LATITUDE")
parser.add_argument("-g","--longitude",dest="longitude",default=None,
                    metavar="LONGITUDE",help="query using longitude LONGITUDE")
parser.add_argument("-l","--logfile",dest="logfile",default=None,
                    metavar="LOGFILE",help="write logging output to LOGFILE")
parser.add_argument("-v","--verbose",dest="verbose",action="store_true",default=False,
                    help="output verbose log messages")

options = parser.parse_args()

##
# Configure logging
#
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

##
# Attempt to load configuration from file
#
(fileConfig, apikey, servicenames, location) = (None, None, [], None)
if options.config is not None:
    try:
        fileConfigHandle = open(options.config,"r")
        fileConfig = json.load(fileConfigHandle)
    except Exception as e:
        logger.error("Problem reading configuration from '%s': %s. Aborting.", options.config, e)
        sys.exit(1)
    logLevelCfg = fileConfig.get('logging').get('loglevel').upper()
    if logLevelCfg is not None and hasattr(logging,logLevelCfg):
        logger.setLevel(getattr(logging,logLevelCfg))
        ch.setLevel(getattr(logging,logLevelCfg))

(latitude,longitude) = (0.0,0.0)
if options.latitude is None:
    if fileConfig is not None:
        try:
            latitude = fileConfig.get('location').get('latitude')
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
            longitude = fileConfig.get('location').get('longitude')
        except Exception as e:
            logger.error("Unable to find key 'longitude' in section 'default' from config file '%s': %s",
                         options.config, e)
            sys.exit(1)
    else:
        logger.error("No longitude provided. Unable to continue.")
        sys.exit(1)
else:
    longitude = options.longitude

##
# Attempt to get sunrise/sunset times based on locality
#
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
obj = {}
cacheFilename = '/root/var/SunRiseSetTimes.json'
try:
    response = requests.get(url)
    #data = response.json()
    obj = response.json()
    logger.info("Request return HTTP %d", response.status_code)
    response.close()
    logger.debug("Response data:\n%s", json.dumps(obj, sort_keys=True, indent=4, separators=(',',': ')))
    hCachefile = open(cacheFilename, 'w')
    hCachefile.write(json.dumps(obj, sort_keys=True, indent=4))
    hCachefile.close()
except Exception as e:
    logger.error("Error connecting to URL '%s': %s. Attempt to load from cache file.", url, e)
    fInfo = os.stat(cacheFilename)
    if datetime.datetime.now() - datetime.datetime.fromtimestamp(fInfo.st_mtime) > datetime.timedelta(days=7):
        logger.error('Error: Cache file is over a week old. Aborting.')
        sys.exit(1)
    hCachefile = open(cacheFilename, 'r')
    obj = json.load(hCachefile)
    hCachefile.close()

eventkeys = (
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

if obj.get('results') is None:
    logger.error("Result object has no 'results' key")
    sys.exit(1)
timedata = {}
for e in eventkeys:
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
    timedata[e] = localEpoch

##
# Attempt to switch lights on/off based upon sunrise/sunset times
#
#from RPi import GPIO
#from rcswitch import RCSwitch
#with RCSwitch() as rcswitch:
try:
    #rcswitch = RCSwitch()
    #rcswitch.setRepeatTransmit(6)

    cmdbin = '/usr/bin/codesend'

    txpin = fileConfig.get("lights").get("txpin")
    pulsestart = fileConfig.get("lights").get("pulse").get("start")
    pulsestop = fileConfig.get("lights").get("pulse").get("end")
    pulsewait = fileConfig.get("lights").get("pulse").get("spacing")
    channels = fileConfig.get("lights").get("channels")
    logger.info("Radio config: Pulse { start: %d, stop: %d, wait: %f }, TXPin %d.", pulsestart, pulsestop, pulsewait, txpin)
    logger.info("Channel config: %s.", channels)
    #logger.info("Now mode is: %s", repr(GPIO.getmode()))
    #logger.info("Current channel function: %s", repr(GPIO.gpio_function(txpin)))

    waittime = timedata.get('sunrise') - time.time()
    while waittime < 0:
        # this happens if loading from cache...
        waittime += 60 * 60 * 24
    #waittime = 10
    logger.info("Sleep until '%s' (%d seconds) before turning lights on.", time.asctime(time.localtime(timedata.get('sunrise'))), waittime)
    time.sleep(waittime)
    logger.info("Sleep over. Let's turn on dem lights...")

    # Send on code
    for i in range(len(channels)):
        channel = channels[i]
        logger.info("Processing channel %d '%s'", i+1, repr(channel))
        if channel["manage"] is not True:
            logger.info("Skipping unmanaged channel %d.", i+1)
            continue
        for pulse in range(pulsestart,pulsestop+1):
            #logger.info("Setting pulse length to '%d'", pulse)
            #try:
            #    rcswitch.setPulseLength(pulse)
            #except Exception as e:
            #    logger.error("Error setting pulse length to %d: %s", pulse, e)
            #    GPIO.cleanup()
            #    sys.exit(1)
    
            #logger.info("Setting transmit pin to '%d'", txpin)
            #try:
            #    rcswitch.enableTransmit(txpin)
            #except Exception as e:
            #    logger.error("Error enabling transmit: %s", e)
            #    GPIO.cleanup()
            #    sys.exit(1)
            #logger.info("Now channel function is: %s", repr(GPIO.gpio_function(txpin)))

            logger.info("Attempting to transmit code '%d'...", channel["on"])
            cmdargs = [cmdbin, '-l', str(pulse), str(channel["on"])]
            try:
                #rcswitch.send(str(channel["on"]),24)
                rc = subprocess.call(cmdargs)
                if rc > 0:
                    logger.warn("Subprocess returned '%d' from '%s'", rc, cmdargs)
                else:
                    logger.info("Successfully executed '%s'", cmdargs)
            except Exception as e:
                logger.error("Error sending code: %s", e)
            #    GPIO.cleanup()
                raise
                sys.exit(1)
  
            #logger.info("Disabling transmit")
            #try:
            #    rcswitch.disableTransmit()
            #except Exception as e:
            #    logger.error("Error disabling transmit: %s", e)
            #    GPIO.cleanup()
            #    sys.exit(1)
            #logger.info("Now channel function is: %s", repr(GPIO.gpio_function(txpin)))

        logger.info("Pausing for %d seconds", pulsewait)
        time.sleep(pulsewait)

    waittime = timedata.get('sunset') - time.time()
    #waittime = 10
    logger.info("Sleep until '%s' (%d seconds) before turning lights off.", time.asctime(time.localtime(timedata.get('sunset'))), waittime)
    time.sleep(waittime)
    logger.info("Sleep over. Let's turn dem lights off...")

    # Send off code
    for i in range(len(channels)):
        channel = channels[i]
        logger.info("Processing channel %d '%s'", i+1, repr(channel))
        if channel["manage"] is not True:
            logger.info("Skipping unmanaged channel %d.", i+1)
            continue
        for pulse in range(pulsestart,pulsestop+1):
            #logger.info("Setting pulse length to '%d'", pulse)
            #try:
            #    rcswitch.setPulseLength(pulse)
            #except Exception as e:
            #    logger.error("Error setting pulse length to %d: %s", pulse, e)
            #    GPIO.cleanup()
            #    sys.exit(1)

            #logger.info("Setting transmit pin to '%d'", txpin)
            #try:
            #    rcswitch.enableTransmit(txpin)
            #except Exception as e:
            #    logger.error("Error enabling transmit: %s", e)
            #    GPIO.cleanup()
            #    sys.exit(1)
            #logger.info("Now channel function is: %s", repr(GPIO.gpio_function(txpin)))

            logger.info("Attempting to transmit off code '%d'...", channel["off"])
            cmdargs = [cmdbin, '-l', str(pulse), str(channel["off"])]
            try:
                #rcswitch.send(str(channel["off"]),24)
                rc = subprocess.call(cmdargs)
                if rc > 0:
                    logger.warn("Subprocess returned '%d' from '%s'", rc, cmdargs)
                else:
                    logger.info("Successfully executed '%s'", cmdargs)
            except Exception as e:
                logger.error("Error sending channel off code: %s", e)
            #    GPIO.cleanup()
                sys.exit(1)

            #logger.info("Disabling transmit")
            #try:
            #    rcswitch.disableTransmit()
            #except Exception as e:
            #    logger.error("Error disabling transmit: %s", e)
            #    GPIO.cleanup()
            #    sys.exit(1)
            #logger.info("Now channel function is: %s", repr(GPIO.gpio_function(txpin)))

        logger.info("Pausing for %d seconds", pulsewait)
        time.sleep(pulsewait)
except:
    raise
    sys.exit(1)

try:
    rv = fcntl.flock(lockFd, fcntl.LOCK_UN)
except OSError as e:
    logging.warn("Exception releasing lock on '%s': %s", lockFile, e)
logger.info("All done. Cleaning up and exiting.")
#GPIO.cleanup()
sys.exit(0)
