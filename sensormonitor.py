#!/usr/bin/env python 

import os, sys
import time
import logging
import numpy

from RPi import GPIO
import Adafruit_DHT

sys.stdout.write("Setting up logging...\n")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

#fh = logging.Formatter("[%(asctime)s] %(levelname)s: %(filename)s:%(funcName)s:%(lineno)d - %(message)s")
fh = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
ch.setFormatter(fh)
logger.addHandler(ch)
logger.debug("Logging setup complete. Preparing to enter main.")
photocellPin = 37
photocellReading = 0
metrics_queue = {}

def loop(metrics_queue):
    logger.debug("Getting temperature and humidity reading...")
    (temperature,humidity) = (0.0,0.0)
    probe_start = time.time()
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302,'4')
    if not temperature or not humidity:
        logger.error("Unable to get temperature or humidity from sensor. Aborting.")
        sys.exit(1)
    logger.debug("Got temperature=%s, humidity=%s", temperature, humidity)
    metrics_queue["th_probe_time"].append( time.time() - probe_start )
    tempf = 9.0 * temperature / 5.0 + 32.0
    #photocellReading = GPIO.input(photocellPin)
    logger.debug("Getting light sensor charge level...")
    probe_start = time.time()
    photocellReading = rcTime(photocellPin)
    metrics_queue["ls_probe_time"].append( time.time() - probe_start )
    logger.debug("Photocell reading: %s",repr(photocellReading))
    lightLevel = "Undefined"
    if photocellReading >= 30000:
        lightLevel = "Timed out: nothing connected"
    elif photocellReading >= 0.005:
        lightLevel = "Dark"
    elif photocellReading >= 0.0005:
        lightLevel = "Dim"
    elif photocellReading >= 0.00005:
        lightLevel = "Light"
    else:
        lightLevel = "Bright"
    logger.debug("Qualitative analysis: the light level is '%s' (%7.6f us), temperature is '%4.1fC/%4.1fF', humidity is '%4.1f'",
                 lightLevel,photocellReading,temperature,tempf,humidity)
    metrics_queue["temperature"].append(temperature)
    metrics_queue["humidity"].append(humidity)
    metrics_queue["light"].append(photocellReading)
    metrics_queue["count"] += 1
    time.sleep(1.0)

def rcTime(rcPin):
    reading = 0.0
    # set pin as output and pull to LOW
    GPIO.setup(rcPin,GPIO.OUT)
    GPIO.output(rcPin,GPIO.LOW)

    # now change pin to input and wait to go high
    t0 = time.clock()
    GPIO.setup(rcPin,GPIO.IN)
    while GPIO.input(rcPin) == GPIO.LOW:
        reading += 1

        if reading >= 30000:
            # if we got this high, likely nothing connected
            break
    t1 = time.clock()
    reading = (t1 - t0)
    return reading

if __name__ == "__main__":
    logger.debug("Preparing GPIO...")
    GPIO.setmode(GPIO.BOARD)
    #GPIO.setup(photocellPin,GPIO.IN,GPIO.PUD_DOWN)
    #GPIO.setup(photocellPin,GPIO.IN)
    logger.debug("GPIO setup complete. Preparing to enter sensor capture loop.")
    metrics_queue = { "temperature":[],"humidity":[], "th_probe_time":[],"light":[],"ls_probe_time":[],"count":0 }

    t_start = int(time.time())
    t_end = int(time.time())
    while True:
        t_elapsed = t_end - t_start
        if t_elapsed >= 60:
            t_avg = numpy.mean(metrics_queue.get("temperature"))
            metrics_queue.get("temperature").sort()
            h_avg = numpy.mean(metrics_queue.get("humidity"))
            metrics_queue.get("humidity").sort()
            th_probe_avg = numpy.mean(metrics_queue.get("th_probe_time"))
            metrics_queue.get("th_probe_time").sort()
            l_avg = numpy.mean(metrics_queue.get("light"))
            metrics_queue.get("light").sort()
            ls_probe_avg = numpy.mean(metrics_queue.get("ls_probe_time"))
            metrics_queue.get("ls_probe_time").sort()
            logger.info("One-minute statistics, based on %d readings:", metrics_queue.get("count"))
            logger.info("  Temperature -- Min %4.1fC/%4.1fF, Avg %4.1fC/%4.1fF, Max %4.1fC/%4.1fF",
                        metrics_queue.get("temperature")[0], 9.0 * metrics_queue.get("temperature")[0] / 5.0 + 32.0,
                        t_avg, 9.0 * t_avg / 5.0 + 32.0,
                        metrics_queue.get("temperature")[-1], 9.0 * metrics_queue.get("temperature")[-1] / 5.0 + 32.0)
            logger.info("     Humidity -- Min %4.1f, Avg %4.1f, Max %4.1f",
                        metrics_queue.get("humidity")[0],
                        h_avg,
                        metrics_queue.get("humidity")[-1])
            logger.info("  Light level -- Min %7.6f, Avg %7.6f, Max %7.6f",
                        metrics_queue.get("light")[0],
                        l_avg,
                        metrics_queue.get("light")[-1])
            logger.info("  Probe time (T/H) -- Min %7.6f, Avg %7.6f, Max %7.6f",
                        metrics_queue.get("th_probe_time")[0],
                        th_probe_avg,
                        metrics_queue.get("th_probe_time")[-1])
            logger.info("  Probe time (L/S) -- Min %7.6f, Avg %7.6f, Max %7.6f",
                        metrics_queue.get("ls_probe_time")[0],
                        ls_probe_avg,
                        metrics_queue.get("ls_probe_time")[-1])
            metrics_queue = { "temperature":[],"humidity":[],"th_probe_time":[],"light":[],"ls_probe_time":[],"count":0 }
            t_start = int(time.time())
        try:
            loop(metrics_queue)
        except KeyboardInterrupt:
            break
            GPIO.cleanup()
        t_end = int(time.time())
    GPIO.cleanup()
    sys.exit(0)
