#!/usr/bin/env python3

from argparse import ArgumentParser
import datetime
import errno
import fcntl
import json
import logging
import logging.handlers
import os
import pytz
import requests
import subprocess
import sys
from string import Template
import time

import psutil

F_RESPONSE = 'response.json'
LOCKFILE = '/tmp/LightsManager.lock'
LOGGER = logging.getLogger('LightsManager')
CMDBIN = '/usr/bin/codesend'


def cycle_lights(config, key):
    txpin = config.get("lights").get("txpin")
    pulsestart = config.get("lights").get("pulse").get("start")
    pulsestop = config.get("lights").get("pulse").get("end")
    pulsewait = config.get("lights").get("pulse").get("spacing")
    retransmit = config.get("lights").get("pulse").get("retransmit")
    channels = config.get("lights").get("channels")
    LOGGER.info("Radio config: Pulse { start: %d, stop: %d, wait: %f }, TXPin %d.",
                pulsestart, pulsestop, pulsewait, txpin)
    LOGGER.info("Channel config: %s.", channels)

    # Send requested 'key' code on each channel
    errors = 0
    for i in range(len(channels)):
        channel = channels[i]
        code = channel.get(key)
        if not code:
            LOGGER.warning('Skipping channel "%s" with no "%s" key', channel, key)
        LOGGER.info("Processing channel %d '%s'", i+1, repr(channel))
        if channel["manage"] is not True:
            LOGGER.info("Skipping unmanaged channel %d.", i+1)
            continue
        for pulse_len in range(pulsestart, pulsestop):
            LOGGER.info("Using pulse length %d", pulse_len)
            for xmt in range(retransmit):
                LOGGER.info("Attempting to transmit code '%d'...", code)
                cmdargs = [CMDBIN, str(code), '-l', str(pulse_len)]
                try:
                    rc = subprocess.call(cmdargs)
                    if rc > 0:
                        LOGGER.warn("Subprocess returned '%d' from '%s'", rc, cmdargs)
                    else:
                        LOGGER.info("Successfully executed '%s'", cmdargs)
                except Exception as err:
                    LOGGER.error("Error sending code: %s", err)
                    errors += 1
  
            LOGGER.info("Pausing for %d seconds", pulsewait)
            time.sleep(pulsewait)
    if errors:
        LOGGER.warning('Cycle completed with %d errors', errors)
    return errors


def get_config(options):
    fileConfig = None
    if options.config is not None:
        try:
            fileConfigHandle = open(options.config,"r")
            fileConfig = json.load(fileConfigHandle)
            LOGGER.debug('Config: %s', fileConfig)
            logLevelCfg = fileConfig.get('logging', {}).get('loglevel', '').upper()
            if logLevelCfg and hasattr(logging, logLevelCfg):
                LOGGER.setLevel(getattr(logging, logLevelCfg))
                for handler in LOGGER.handlers:
                    handler.setLevel(getattr(logging, logLevelCfg))
        except Exception as err:
            LOGGER.error("Problem reading configuration from '%s': %s.", options.config, err)
    return fileConfig

def get_location(options, config):
    location = {'latitude': None, 'longitude': None}
    (fileConfig, apikey, servicenames) = (None, None, [])
    if options.latitude is None:
        if config is not None:
            latitude = config.get('location', {}).get('latitude')
            if latitude is not None:
                location.update({'latitude': latitude})
            else:
                LOGGER.error("Unable to find key 'latitude' in section 'location' from config file '%s'",
                             options.config)
    else:
        location.update({'latitude': options.latitude})

    if options.longitude is None:
        if config is not None:
            longitude = config.get('location').get('longitude')
            if longitude is not None:
                location.update({'longitude': longitude})
            else:
                LOGGER.error("Unable to find key 'longitude' in section 'location' from config file '%s'",
                             options.config)
    else:
        location.update({'longitude': options.longitude})
    return location


def get_lock():
    last_pid = None
    lock_handle = None
    if os.path.exists(LOCKFILE):
        try:
            lock_handle = open(LOCKFILE, 'r')
        except IOError as err:
            LOGGER.error('Unable to open lockfile %s for reading: %s', LOCKFILE, err)
            return None
        last_pid = lock_handle.read()
        if len(last_pid) > 0:
            last_pid = int(last_pid.strip())
        lock_handle.close()
    try:
        lock_handle = open(LOCKFILE, 'w')
    except IOError as err:
        LOGGER.error('Unable to open lockfile %s for writing: %s', LOCKFILE, err)
        return None
    try:
        rv = fcntl.flock(lock_handle, fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError as err:
        LOGGER.error('Lock file last held by %d. Checking to see if PID still running.', last_pid)
        if last_pid and psutil.pid_exists(last_pid):
            LOGGER.error('PID %d found to be running. Checking to see if that is this process.', last_pid)
            success = True
            for process in psutil.process_iter():
                if process.pid == last_pid:
                    if sys.argv[1] == process.cmdline()[1]:
                        LOGGER.error('Unable to lock file %s: %s. Still held by %d (%s).', LOCKFILE, err, process.pid,
                                     process.cmdline()[1])
                        success = False
                    else:
                        LOGGER.error('PID %d is not us: %s != %s', process.pid, process.cmdline()[1], sys.argv[1])
                        success = False
                    break
            if not success:
                return None
        else:
            LOGGER.error('Could not match last PID %s with any running process', last_pid)
            return None
    lock_handle.write(str(os.getpid()))
    return lock_handle


def get_response(location):
    '''
    Attempt to get sunrise/sunset times based on locality
    Using the API made available by Sunrise-Sunset.org:
        http://www.sunrise-sunset.org/api/
    '''

    params = {
        'formatted': 0,
        'lat': location.get('latitude'),
        'lng': location.get('longitude')
    }

    url = 'http://api.sunrise-sunset.org/json'
    LOGGER.info("Requesting URL '%s'", url)

    response = None
    obj = {}
    cacheFilename = 'SunRiseSetTimes.json'
    try:
        response = requests.get(url, params=params)
        obj = response.json()
        LOGGER.info("Request return HTTP %d", response.status_code)
        response.close()
        LOGGER.debug("Response data:\n%s", json.dumps(obj, sort_keys=True, indent=4, separators=(',',': ')))
        with open(cacheFilename, 'w') as hCachefile:
            hCachefile.write(json.dumps(obj, sort_keys=True, indent=4))
            hCachefile.close()
    except Exception as e:
        LOGGER.error("Error connecting to URL '%s': %s. Attempt to load from cache file.", url, e)
        fInfo = os.stat(cacheFilename)

        if datetime.datetime.now() - datetime.datetime.fromtimestamp(fInfo.st_mtime) > datetime.timedelta(days=7):
            LOGGER.error('Error: Cache file is over a week old. Aborting.')
            return None
        with open(cacheFilename, 'r') as hCachefile:
            utc_now = pytz.utc.localize(datetime.datetime.utcnow())
            obj = json.load(hCachefile)
            cached_sunrise = datetime.datetime.fromisoformat(obj.get('results').get('sunrise'))
            today_sunrise = pytz.utc.localize(datetime.datetime.combine(utc_now.date(), cached_sunrise.time()))
            LOGGER.warning('Attempt to fast-forward cached sunrise %s to today: %s', cached_sunrise, today_sunrise)
            cached_sunset = datetime.datetime.fromisoformat(obj.get('results').get('sunset'))
            today_sunset = pytz.utc.localize(datetime.datetime.combine(utc_now.date(), cached_sunset.time()))
            LOGGER.warning('Attempt to fast-forward cached sunset %s to today: %s', cached_sunset, today_sunset)
            obj['result'].update({'sunrise': today_sunrise.isoformat(),
                                  'sunset': today_sunset.isoformat()})
            hCachefile.close()

    if obj.get('results') is None:
        LOGGER.warning("Result object has no 'results' key")
    return obj


def get_timedeltas(data):
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    day_seconds = 60 * 60 * 24  # seconds in one day, generically
    LOGGER.info('Now: %s', utc_now)
    deltas = {}
    sunrise = datetime.datetime.fromisoformat(data.get('sunrise'))
    LOGGER.info('Sunrise: %s', sunrise)
    deltas.setdefault('sunrise', (sunrise - utc_now).total_seconds())
    if utc_now < sunrise:
        LOGGER.info('Delta to sunrise: %s seconds', deltas['sunrise'])
    else:
        LOGGER.info('Delta to sunrise: %s seconds ago', deltas['sunrise'] * -1)
    sunset = datetime.datetime.fromisoformat(data.get('sunset'))
    LOGGER.info('Sunset: %s', sunset)
    deltas.setdefault('sunset', (sunset - utc_now).total_seconds())
    if utc_now < sunset:
        LOGGER.info('Delta to sunset: %s seconds', deltas['sunset'])
    else:
        LOGGER.info('Delta to sunset: %s seconds ago', deltas['sunset'] * -1)

    return deltas


def release_lock(lock_handle):
    try:
        rv = fcntl.flock(lock_handle, fcntl.LOCK_UN)
    except OSError as err:
        LOGGER.error('Exception releasing lock on %s: %s', LOCKFILE, err)
        return 255
    return 0


def main():
    LOGGER.info('Begin')
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

    if options.debug == True:
        logLevel = logging.DEBUG
    elif options.verbose == True:
        logLevel = logging.INFO
    else:
        logLevel = logging.WARN

    LOGGER.setLevel(logLevel)

    handler = None
    if options.logfile is not None:
        try:
            handler = logging.handlers.RotatingFileHandler(filename=options.logfile,maxBytes=1024000)
        except IOError as err:
            sys.stderr.write('Unable to open file %s for writing: %s. Will continue without.', options.logfile, err)
            handler = logging.StreamHandler()
    else:
        handler = logging.StreamHandler()
    handler.setLevel(logLevel)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(filename)s %(funcName)s[%(lineno)d] - %(message)s',
                                  datefmt='%F %T')
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
    LOGGER.debug('Options: %s', options)

    LOGGER.info('Getting process lock')
    lock_handle = get_lock()
    if not lock_handle:
        LOGGER.error('Unable to acquire run lock. Aborting.')
        return 255

    LOGGER.info('Loading configuration')
    config = get_config(options)
    LOGGER.info('Configuration: %s', config)

    LOGGER.info('Setting location')
    location =  get_location(options, config)
    LOGGER.info('Location: %s', location)
    if not location.get('latitude') or not location.get('longitude'):
        LOGGER.error('No location information provided. Unable to continue.')
        return release_lock(lock_handle)

    data = get_response(location).get('results')
    LOGGER.info('Data: %s', data)
    time_deltas = get_timedeltas(data)

    if time_deltas.get('sunrise') > 0:
        LOGGER.info("Sleep %d seconds before turning lights on.", time_deltas.get('sunrise'))
        time.sleep(time_deltas.get('sunrise'))
        LOGGER.info('Sleep over. Cycle lights.')
    cycle_lights(config, 'on')

    if time_deltas.get('sunset') > 0:
        LOGGER.info("Sleep %d seconds before turning lights off.", time_deltas.get('sunset'))
        time.sleep(time_deltas.get('sunset'))
        LOGGER.info('Sleep over. Cycle lights.')
    cycle_lights(config, 'off')

    return release_lock(lock_handle)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        LOGGER.warning('Caught keyboard interrupt. Exiting.')
        sys.exit(1)
