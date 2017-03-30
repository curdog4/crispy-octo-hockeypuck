#!/usr/bin/env python 

import os, sys
import time
import logging

from RPi import GPIO

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

fh = logging.Formatter("[%(asctime)s] %(levelname)s: %(filename)s:%(funcName)s:%(lineno)d - %(message)s")
ch.setFormatter(fh)
logger.addHandler(ch)

photocellPin = 37
photocellReading = 0

def loop():
    #photocellReading = GPIO.input(photocellPin)
    photocellReading = rcTime(photocellPin)
    logger.info("Photocell reading: %s",repr(photocellReading))
    lightLevel = "Undefined"
    if photocellReading >= 30000:
        lightLevel = "Timed out: nothing connected"
    elif photocellReading >= 35:
        lightLevel = "Dark"
    elif photocellReading >= 20:
        lightLevel = "Dim"
    elif photocellReading >= 1:
        lightLevel = "Light"
    else:
        lightLevel = "Bright"
    logger.info("Qualitative analysis: the light level is '%s'",lightLevel)
    time.sleep(1.0)

def rcTime(rcPin):
    reading = 0
    # set pin as output and pull to LOW
    GPIO.setup(rcPin,GPIO.OUT)
    GPIO.output(rcPin,GPIO.LOW)

    # now change pin to input and wait to go high
    GPIO.setup(rcPin,GPIO.IN)
    while GPIO.input(rcPin) == GPIO.LOW:
        reading += 1

        if reading >= 30000:
            # if we got this high, likely nothing connected
            break
    return reading

if __name__ == "__main__":
    GPIO.setmode(GPIO.BOARD)
    #GPIO.setup(photocellPin,GPIO.IN,GPIO.PUD_DOWN)
    #GPIO.setup(photocellPin,GPIO.IN)
    while True:
        try:
            loop()
        except KeyboardInterrupt:
            break
            GPIO.cleanup()
    GPIO.cleanup()
    sys.exit(0)
