#!/usr/bin/env python

import os, sys
import time
import math
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

fh = logging.Formatter("[%(asctime)s] %(levelname)s: %(filename)s:%(funcName)s:%(lineno)d - %(message)s")
ch.setFormatter(fh)
logger.addHandler(ch)

'''
Adapted from JavaScript code from NOAA:
 http://www.esrl.noaa.gov/gmd/grad/solcalc/main.js
'''

location = {
    'latitude'  : 39.63472221,  # 39 degrees 38' 5" North Latitude
    'longitude' : -119.89666667 # 119&deg; 53' 48" West Longitude
}

monthList = [
    { 'name': 'January',   'numdays': 31, 'abbr': 'Jan' },
    { 'name': 'February',  'numdays': 28, 'abbr': 'Feb' },
    { 'name': 'March',     'numdays': 31, 'abbr': 'Mar' },
    { 'name': 'April',     'numdays': 30, 'abbr': 'Apr' },
    { 'name': 'May',       'numdays': 31, 'abbr': 'May' },
    { 'name': 'June',      'numdays': 30, 'abbr': 'Jun' },
    { 'name': 'July',      'numdays': 31, 'abbr': 'Jul' },
    { 'name': 'August',    'numdays': 31, 'abbr': 'Aug' },
    { 'name': 'September', 'numdays': 30, 'abbr': 'Sep' },
    { 'name': 'October',   'numdays': 31, 'abbr': 'Oct' },
    { 'name': 'November',  'numdays': 30, 'abbr': 'Nov' },
    { 'name': 'December',  'numdays': 31, 'abbr': 'Dec' }
]

def calcTimeJulianCent(julianday):
    logger.debug("Entering...")
    t = (julianday - 2451545.0) / 36525.0
    logger.debug("Returning...")
    return t

def calcJulianDayFromJulianCent(t):
    logger.debug("Entering...")
    julianday = t * 36525.0 + 2451545.0
    logger.debug("Returning...")
    return julianday

def isLeapYear(year):
    logger.debug("Entering...")
    logger.debug("Returning...")
    return ((year % 4 == 0 and year % 100 != 0) or year % 400 == 0)

def calcDoyFromJulianDay(julianday):
    logger.debug("Entering...")
    z = math.floor(julianday + 0.5)
    f = (julianday + 0.5) - z
    a = z
    if z >= 2299161:
        alpha = math.floor((z - 1867216.25)/36524.25)
        a = z + 1 + alpha - math.floor(alpha/4)
    b = a + 1524
    c = math.floor((b-122.1)/365.25)
    d = math.floor(365.25*c)
    e = math.floor((b-d)/30.6001)
    day = b - d - math.floor(30.6001 * e) + f
    month = e - 13
    if e < 14:
        month = e - 1
    year = c - 4175
    if month > 2:
        year = c - 4716
    k = 2
    if isLeapYear(year) == True:
        k = 1
    doy = math.floor((275 * month)/9) - k * math.floor((month + 9)/12) + day - 30
    logger.info("Day of year: %s", str(doy))
    logger.debug("Returning...")
    return doy

def radToDeg(angleRad):
    logger.debug("Entering...")
    logger.debug("Returning...")
    return (180.0 * angleRad / math.pi)

def degToRad(angleDeg):
    logger.debug("Entering...")
    logger.debug("Returning...")
    return (math.pi * angleDeg / 180.0)

def calcGeomMeanLongSun(t):
    logger.debug("Entering...")
    l0 = 280.46646 + t * (36000.76983 + t*(0.0003032))
    while l0 > 360.0:
        l0 -= 360.0
    while l0 < 0.0:
        l0 += 360.0
    logger.debug("Returning...")
    return l0

def calcGeomMeanAnomalySun(t):
    logger.debug("Entering...")
    m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    logger.debug("Returning...")
    return m

def calcEccentricityEarthOrbit(t):
    logger.debug("Entering...")
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    logger.debug("Returning...")
    return e

def calcSunEqOfCenter(t):
    logger.debug("Entering...")
    m = calcGeomMeanAnomalySun(t)
    mrad = degToRad(m)
    sinm = math.sin(mrad)
    sin2m = math.sin(mrad+mrad)
    sin3m = math.sin(mrad+mrad+mrad)
    c = sinm * (1.914602 - t * (0.004817 + 0.000014 * t)) + sin2m * (0.019993 - 0.000101 * t) + sin3m * 0.000289
    logger.debug("Returning...")
    return c

def calcSunTrueLong(t):
    logger.debug("Entering...")
    l0 = calcGeomMeanLongSun(t)
    c = calcSunEqOfCenter(t)
    o = l0 + c
    logger.debug("Returning...")
    return o

def calcSunTrueAnomaly(t):
    logger.debug("Entering...")
    m = calcGeomMeanAnomalySun(t)
    c = calcSunEqOfCenter(t)
    v = m + c
    logger.debug("Returning...")
    return v

def calcSunRadVector(t):
    logger.debug("Entering...")
    v = calcSunTrueAnomaly(t)
    e = calcEccentricityEarthOrbit(t)
    r = (1.000001018 * (1 - e * e)) / (1 + e * math.cos(degToRad(v)))
    logger.debug("Returning...")
    return r

def calcSunApparentLong(t):
    logger.debug("Entering...")
    o = calcSunTrueLong(t)
    omega = 125.04 - 1934.136 * t
    lmda = o - 0.00569 - 0.00478 * math.sin(degToRad(omega))
    logger.debug("Returning...")
    return lmda

def calcMeanObliquityOfEcliptic(t):
    logger.debug("Entering...")
    seconds = 21.448 - t*(46.8150 + t*(0.00059 - t*(0.001813)))
    e0 = 23.0 + (26.0 + (seconds/60.0))/60.0
    logger.debug("Returning...")
    return e0

def calcObliquityCorrection(t):
    logger.debug("Entering...")
    e0 = calcMeanObliquityOfEcliptic(t)
    omega = 125.04 - 1934.136 * t
    e = e0 + 0.00256 * math.cos(degToRad(omega))
    logger.debug("Returning...")
    return e

def calcSunRtAscension(t):
    logger.debug("Entering...")
    e = calcObliquityCorrection(t)
    lmda = calcSunApparentLong(t)
    tananum = (math.cos(degToRad(e)) * math.sin(degToRad(lmda)))
    tanadenom = (math.cos(degToRad(lmda)))
    alpha = radToDeg(math.atan2(tananum, tanadenom))
    logger.debug("Returning...")
    return alpha

def calcSunDeclination(t):
    logger.debug("Entering...")
    e = calcObliquityCorrection(t)
    lmda = calcSunApparentLong(t)
    sint = math.sin(degToRad(e)) * math.sin(degToRad(lmda))
    theta = radToDeg(math.asin(sint))
    logger.debug("Returning...")
    return theta

def calcEquationOfTime(t):
    logger.debug("Entering...")
    epsilon = calcObliquityCorrection(t)
    l0 = calcGeomMeanLongSun(t)
    e = calcEccentricityEarthOrbit(t)
    m = calcGeomMeanAnomalySun(t)

    y = math.tan(degToRad(epsilon)/2.0)
    y *= y

    sin2l0 = math.sin(2.0 * degToRad(l0))
    sin4l0 = math.sin(4.0 * degToRad(l0))
    cos2l0 = math.cos(2.0 * degToRad(l0))
    sinm = math.sin(degToRad(m))
    sin2m = math.sin(2.0 * degToRad(m))

    etime = y * sin2l0 - 2.0 * e * sinm + 4.0 * e * y * sinm * cos2l0 - 0.5 * y * y * sin4l0 * - 1.25 * e * e *	sin2m
    logger.debug("Returning...")
    return radToDeg(etime)

def calcHourAngleSunrise(lat,solarDec):
    logger.debug("Entering...")
    latRad = degToRad(lat)
    sdRad = degToRad(solarDec)
    haArg = (math.cos(degToRad(90.833)) / (math.cos(latRad) * math.cos(sdRad)) - math.tan(latRad) * math.tan(sdRad))
    ha = math.acos(haArg)
    logger.debug("Returning...")
    return ha

def isNumber(inputVal):
    logger.debug("Entering...")
    logger.debug("Received input '%s'", repr(inputVal))
    oneDecimal = False
    logger.debug("Converting to string...")
    inputStr = "" + str(inputVal)
    logger.debug("Converted string is '%s' of length '%d'", inputStr, len(inputStr))
    logger.debug("Stepping character-by-character through string...")
    for i in range(0,len(inputStr)):
        oneChar = inputStr[i]
        logger.debug("Character at position %d is %s", i, oneChar)
        logger.debug("Checking for leading +/-...")
        if i == 0 and (oneChar == "-" or oneChar == "+"):
            logger.debug("Found leading +/-, continuing")
            continue
        logger.debug("Checking for decimal, and that there is just one decimal")
        if oneChar == "." and oneDecimal == False:
            logger.debug("Found first decimal, continuing")
            oneDecimal = True
            continue
        logger.debug("Checking that character is a number")
        if ord(oneChar) < 48 or ord(oneChar) > 57:
            logger.debug("Found that character is not a number. Input is not a number.")
            logger.debug("Returning...")
            return False
        logger.debug("Found that character is a number")
    logger.debug("Input appears to be a number")
    logger.debug("Returning...")
    return True

def zeroPad(n, digits):
    logger.debug("Entering...")
    n = str(n)
    while len(n) < digits:
        n = "0" + n
    logger.debug("Returning...")
    return n

def getJulianDay(year,month,day):
    logger.debug("Entering...")
    if isLeapYear(year) and month == 2:
        if day > 29:
            day = 29
    else:
        if day > monthList[month-1]['numdays']:
            day = monthList[month-1]['numdays']

    if month <= 2:
        year -= 1
        month += 12

    a = math.floor(year/100)
    b = 2 - a + math.floor(a/4)
    julianday = math.floor(365.25*(year+4716)) + math.floor(30.6001*(month+1)) + day + b - 1524.5
    logger.info("Julian day: %s", str(julianday))
    logger.debug("Returning...")
    return julianday

def getTimeLocal(hour,minute,second,postMeridian,dst):
    logger.debug("Entering...")
    if postMeridian == True and hour < 12:
        hour += 12
    if dst == True:
        hour -= 1
    logger.info("Hour: %s, Minute: %s, Second: %s", str(hour),str(minute),str(second))
    mins = hour * 60 + minute + second / 60
    logger.debug("Returning...")
    return mins

def calcAzEl(t, localtime, latitude, longitude, zone):
    logger.debug("Entering...")
    eqTime = calcEquationOfTime(t)
    theta = calcSunDeclination(t)
    solarTimeFix = eqTime + 4.0 * longitude - 60.0 * zone
    earthRadVec = calcSunRadVector(t)
    trueSolarTime = localtime + solarTimeFix
    while trueSolarTime > 1440:
        trueSolarTime -= 1440
    hourAngle = trueSolarTime / 4.0 - 180.0
    if hourAngle < -180:
        hourAngle += 360.0
    haRad = degToRad(hourAngle)
    csz = math.sin(degToRad(latitude)) * math.sin(degToRad(theta)) + math.cos(degToRad(latitude)) * math.cos(degToRad(theta)) * math.cos(haRad)
    if csz > 1.0:
        csz = 1.0
    elif csz < -1.0:
        csz = -1.0
    zenith = radToDeg(math.acos(csz))
    azDenom = math.cos(degToRad(latitude)) * math.sin(degToRad(zenith))
    if math.fabs(azDenom) > 0.001:
        azRad = (math.sin(degToRad(latitude)) * math.cos(degToRad(zenith)) - math.sin(degToRad(theta))) / azDenom
        if math.fabs(azRad) > 1.0:
            if azRad < 0:
                azRad = -1.0
            else:
                azRad = 1.0
        azimuth = 180.0 - radToDeg(math.acos(azRad))
        if hourAngle > 0.0:
            azimuth = -1.0 * azimuth
    else:
        if latitude > 0.0:
            azimuth = 180.0
        else:
            azimuth = 0.0
    if azimuth < 0.0:
        azimuth += 360.0
    exoatmElevation = 90.0 - zenith

    # Atmospheric Refraction correction
    refractionCorrection = 0.0
    if exoatmElevation <= 85.0:
        te = math.tan(degToRad(exoatmElevation))
        if exoatmElevation > 5.0:
            refractionCorrection = 58.1 / te - 0.07 / (te*te*te) + 0.000086 / (te*te*te*te*te)
        elif exoatmElevation > -0.575:
            refractionCorrection = 1735.0 + exoatmElevation * (-518.2 + exoatmElevation * (103.4 + exoatmElevation * (-12.79 + exoatmElevation * 0.711) ))
        else:
            refractionCorrection = -20.774 / te
        refractionCorrection = refractionCorrection / 3600.0

    solarZen = zenith - refractionCorrection

    logger.debug("Returning...")
    return azimuth

def calcSolNoon(julianday,longitude, timezone, dst):
    logger.debug("Entering...")
    tnoon = calcTimeJulianCent(julianday - longitude/360.0)
    eqTime = calcEquationOfTime(tnoon)
    solNoonOffset = 720.0 - (longitude*4) - eqTime
    newt = calcTimeJulianCent(julianday + solNoonOffset/1440.0)
    eqTime = calcEquationOfTime(newt)
    solNoonLocal = 720.0 - (longitude*4) - eqTime + (timezone*60.0)
    if dst == True:
        solNoonLocal += 60.0
    while solNoonLocal < 0.0:
        solNoonLocal += 1440.0
    while solNoonLocal >= 1440.0:
        solNoonLocal -= 1440.0
    logger.debug("Returning...")
    return solNoonLocal

def dayTuple(julianday):
    logger.debug("Entering...")
    f = z = 0.0
    if julianday < 900000 or julianday > 2817000:
        logger.error("Error: Julian day out-of-bounds: 900000 < %s < 2817000", str(julianday))
        return None
    else:
        z = math.floor(julianday + 0.5)
        f = (julianday + 0.5) - z
    a = z
    if z >= 2299161:
        alpha = math.floor((z - 1867216.25)/36524.25)
        a = z + 1 + alpha - math.floor(alpha/4)
    b = a + 1524
    c = math.floor((b - 122.1)/365.25)
    d = math.floor(365.25 * c)
    e = math.floor((b - d)/30.6001)
    day = int(b - d - math.floor(30.6001 * e) + f)
    month = int(e - 13)
    if e < 14:
        month = int(e - 1)
    year = int(c - 4715)
    if month > 2:
        year = int(c - 4716)

    logger.info("Year: %s, Month: %s, Day: %s", str(year), str(month), str(day))
    logger.debug("Returning...")
    return (year,month,day)

def dayString(julianday,next,flag):
    logger.debug("Entering...")
    output = ""
    (year,month,day) = dayTuple(julianday)
    if year is None:
        return "Error"
    logger.debug("Abbreviated month name %s", monthList[month-1]['abbr'])
    if flag == 2:
        output = zeroPad(day,2) + " " + monthList[month-1]['abbr']
    if flag == 3:
        output = zeroPad(day,2) + " " + monthList[month-1]['abbr'] + " " + str(year)
    if flag == 4:
        output = zeroPad(day,2) + " " + monthList[month-1]['abbr'] + " " + str(year)
        if next == True:
            output += " next"
        else:
            output += " prev"

    logger.debug("Returning...")
    return output

def timeTuple(minutes):
    logger.debug("Entering...")
    if minutes >= 0 and minutes < 1440:
        floatHour = minutes / 60.0
        hour = int(math.floor(floatHour))
        floatMinute = 60.0 * (floatHour - math.floor(floatHour))
        minute = int(math.floor(floatMinute))
        floatSec = 60.0 * (floatMinute - math.floor(floatMinute))
        second = int(math.floor(floatSec + 0.5))
        if second > 59:
            second = 0
            minute += 1

        if minute > 59:
            minute = 0
            hour += 1
        logger.info("Hour: %s, Minute: %s, Second: %s", str(hour),str(minute),str(second))
        logger.debug("Returning...")
        return (hour,minute,second)
    else:
        logger.error("Error: minutes value out-of-bounds: 0 <= %s < 1440", str(minutes))
        return None

def timeString(minutes,flag):
    logger.debug("Entering...")
    (hour,minute,second) = timeTuple(minutes)
    if hour is None:
        return "Error"
    if flag == 2 and second >= 30:
        minute += 1
    output = zeroPad(hour,2) + ":" + zeroPad(minute,2)
    if flag > 2:
        output = output + ":" + zeroPad(second,2)
    logger.debug("Returning...")
    return output

def timeDateTuple(julianday,minutes):
    (year,month,day) = dayTuple(julianday)
    (hour,minute,second) = timeTuple(minutes)
    return (year,month,day,hour,minute,second)

def timeDateString(julianday,minutes):
    logger.debug("Entering...")
    output = timeString(minutes,3) + " " + dayString(julianday,0,3)
    logger.debug("Returning...")
    return output

def calcSunriseSetUTC(rise,julianday,latitude,longitude):
    logger.debug("Entering...")
    t = calcTimeJulianCent(julianday)
    eqTime = calcEquationOfTime(t)
    solarDec = calcSunDeclination(t)
    hourAngle = calcHourAngleSunrise(latitude,solarDec)
    if rise == 0:
        hourAngle = hourAngle * -1.0
    delta = longitude + radToDeg(hourAngle)
    timeUTC = 720 - (4.0*delta) - eqTime
    logger.debug("Returning...")
    return timeUTC

def calcJDofNextPrevRiseSet(next,rise,julianday,latitude,longitude,timezone,dst):
    logger.debug("Entering...")
    increment = -1.0
    if next == True:
        increment = 1.0

    time = calcSunriseSetUTC(rise, julianday, latitude, longitude)
    while isNumber(time) == False:
        julianday += increment
        time = calcSunriseSetUTC(rise, julianday, latitude, longitude)

    timeLocal = time + tz * 60.0
    if dst == True:
        timeLocal += 60.0
    while timeLocal < 0.0 or timeLocal >= 1440.0:
        incr = -1
        if timeLocal < 0:
            incr = 1
        timeLocal += incr * 1440.0
        julianday -= incr

    logger.debug("Returning...")
    return julianday;

def calcSunriseSet(rise, julianday, latitude, longitude, timezone, dst):
    logger.debug("Entering...")
    logger.debug("Calculating first rise/set UTC...")
    timeUTC = calcSunriseSetUTC(rise,julianday,latitude,longitude)
    logger.debug("Got first rise/set UTC: %s", timeUTC)
    logger.debug("Calculating second rise/set UTC...")
    newTimeUTC = calcSunriseSetUTC(rise,julianday + timeUTC/1440.0,latitude,longitude)
    logger.debug("Got second rise/set UTC: %s", newTimeUTC)
    jday = julianday
    logger.debug("Checking if second rise/set UTC is a number...")
    if isNumber(newTimeUTC):
        logger.debug("Second rise/set UTC is a number...")
        timeLocal = newTimeUTC + (timezone * 60.0)
        if dst == True:
            timeLocal += 60.0
        if timeLocal > 0.0 and timeLocal < 1440.0:
            logger.debug("Returning...")
            #return timeString(timeLocal,2)
            return timeDateString(jday,timeLocal)
        else:
            increment = -1
            if timeLocal < 0:
                increment = 1
            while timeLocal < 0.0 or timeLocal > 1440.0:
                timeLocal += increment * 1440.0
                jday -= increment
            logger.debug("Returning...")
            return timeDateString(jday,timeLocal)
    else:
        logger.debug("Second rise/set UTC is not a number: %s", isNumber(newTimeUTC))
        doy = calcDoyFromJulianDay(julianday)
        if (latitude > 66.4 and doy > 79 and doy < 267) or (latitude < -66.4 and doy < 83 and doy > 263):
            if rise == True:
                jdy = calcJDofNextPrevRiseSet(0, rise, julianday, latitude, longitude, timezone, dst)
            else:
                jdy = calcJDofNextPrevRiseSet(1, rise, julianday, latitude, longitude, timezone, dst)
        else:
            if rise == True:
                jdy = calcJDofNextPrevRiseSet(0, rise, julianday, latitude, longitude, timezone, dst)
            else:
                jdy = calcJDofNextPrevRiseSet(1, rise, julianday, latitude, longitude, timezone, dst)
        logger.debug("Returning...")
        return dayString(jdy,0,3)
        


if __name__ == "__main__":
    timestamp = time.localtime()
    julianday = getJulianDay(timestamp[0],timestamp[1],timestamp[2])
    tzoffset = time.timezone / (60*60) * -1
    dst = False
    if timestamp[8] == 1:
        dst = True
    postMeridian = False
    if timestamp[3] > 12:
            postMeridian = True
    tl = getTimeLocal(timestamp[3],timestamp[4],timestamp[5],postMeridian,dst)
    total = julianday + tl/1440.0 - tzoffset/24.0
    t = calcTimeJulianCent(total)
    azEl = calcAzEl(t,tl,location['latitude'],location['longitude'],tzoffset)
    logger.info("Azimuth/elevation: %s", str(azEl))
    solNoon = calcSolNoon(julianday,location['longitude'],tzoffset,dst)
    logger.info("Solar noon: %s", str(solNoon))

    sunrise = calcSunriseSet(1,julianday,location['latitude'],location['longitude'],tzoffset,dst)
    sunset = calcSunriseSet(0,julianday,location['latitude'],location['longitude'],tzoffset,dst)
    logger.info("Sunrise: %s", sunrise)
    logger.info("Sunset: %s", sunset)

