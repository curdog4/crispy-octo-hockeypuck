#!/usr/bin/env python

import os, sys
import time
import math
import logging
from datejs import Date

'''
Adapted from JavaScript taken from:
 https://github.com/mourner/suncalc
TH I E V E S
  H O N O R
THHIOENVOERS
ThH!03n^03r$
'''

location = {
    'latitude'  : 39.63472221,  # 39 degrees 38' 5" North Latitude
    'longitude' : -119.89666667 # 119&deg; 53' 48" West Longitude
}

##
# date/time constants and functions
##
dayMs = 1000 * 60 * 60 * 24
julianYear1970 = 2440588
julianYear2000 = 2451545

def toJulian(date):
    return date.valueOf() / dayMs - 0.5 + julianYear1970

def fromJulian(julianDay):
    return Date((julianDay + 0.5 - julianYear1970) * dayMs)

def toDays(date):
    return toJulian(date) - julianYear2000

##
# general calculations for position
##

earthObliquity = math.pi / 180 * 23.4397

def rightAscension(longitude, bearing):
    return math.atan2(math.sin(longitude) * math.cos(earthObliquity) - math.tan(bearing) * math.sin(earthObliquity), math.cos(longitude))

def declination(longitude, bearing):
    return math.asin(math.sin(bearing) * math.cos(earthObliquity) + math.cos(bearing) * math.sin(earthObliquity) * math.sin(longitude))

def azimuth(h, phi, dec):
    return math.atan2(math.sin(h), math.cos(h) * math.sin(phi) - math.tan(dec) * math.cos(phi))

def altitude(h, phi, dec):
    return math.asin(math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(h))

def siderealTime(d, lw):
    return math.pi / 180 * (280.16 + 360.9856235 * d) - lw

##
# general sun calculations
##

def solarMeanAnomaly(d):
    return math.pi / 180 * (357.5291 + 0.98560028 * d)

def eclipticLongitude(m):
    center = math.pi / 180 * (1.9148 * math.sin(m) + 0.02 * math.sin(2 * m) + 0.0003 * math.sin(3 * m)) # equation of center
    perihelion = math.pi / 180 * 102.9372 # perihelion of the Earth

    return m + center + perihelion + math.pi

def sunCoords(d):
    m = solarMeanAnomaly(d)
    l = eclipticLongitude(m)
    return {'dec': declination(l,0), 'ra': rightAscension(l,0)}

times = [
    [ -0.833, 'sunrise', 'sunset' ],
    [ -0.3, 'sunriseEnd', 'sunsetStart' ],
    [ -6, 'dawn', 'dusk' ],
    [ -12, 'nauticalDawn', 'nauticalDusk' ],
    [ -18, 'nightEnd', 'night' ],
    [ 6, 'goldenHourEnd', 'goldenHour' ]
]

##
# calculations for sun times
##

julianYear0 = 0.0009

def julianCycle(d,lw):
    #return math.round(d - julianYear0 - lw / (2 * math.pi))
    return d - julianYear0 - lw / (2 * math.pi)

def approxTransit(ht,lw,n):
    return julianYear0 + (ht + lw) / (2 * math.pi) + n

def solarTransitJulian(ds,m,l):
    return julianYear2000 + ds + 0.0053 * math.sin(m) - 0.0069 * math.sin(2 * l)

def hourAngle(h,phi,d):
    return math.acos((math.sin(h) - math.sin(phi) * math.sin(d))/(math.cos(phi) * math.cos(d)))

def getSetJulian(h,lw,phi,dec,n,m,l):
    ''' Returns set time for the given sun altitude '''
    w = hourAngle(h,phi,dec)
    a = approxTransit(w,lw,n)
    return solarTransitJulian(a,m,l)
##
# calculations for moon times
# based on http://aa.quae.nl/en/reken/hemelpositie.html formulas
##

def getMoonCoords(d):
    ''' Geocentric ecliptic coordinates of the moon '''
    el = math.pi / 180 * (218.316 + 13.176396 * d) # ecliptic longitude
    m = math.pi / 180 * (134.963 + 13.064993 * d)  # mean anomaly
    f = math.pi / 180 * (93.272 + 13.229350 * d)   # mean distance
    l = el + math.pi / 180 * 6.289 * math.sin(m)   # longitude
    b = math.pi / 180 * 5.128 * math.sin(f)        # latitude
    dt = 385001 - 20905 * math.cos(m)              # distance to the moon in km
    return {'ra': rightAscension(l,b), 'dec': declination(l,b), 'dist': dt}

def hoursLater(date,h):
    return Date(date.valueOf() + h * daysMs / 24)

class SunCalc():
    def __init__(self):
        self.times = times

    def getPosition(self,date,latitude,longitude):
        ''' Calculates sun position for a given date and latitude/longitude '''
        lw = math.pi / 180 * -longitude
        phi = math.pi / 180 * latitude
        d = toDays(date)
        c = sunCoords(d)
        h = siderealTime(d,lw) - c['ra']
        return {'azimuth': azimuth(h, phi, c['dec']), 'altitude': altitude(h, phi, c['dec'])}

    def addTime(self,angle,riseName,setName):
        ''' Add custom time to times config '''
        self.times.append([angle,riseName,setName])

    def getTimes(self,date,latitude,longitude):
        ''' Calculates sun times for a given date and latitude/longitude '''
        lw = math.pi / 180 * -longitude
        phi = math.pi / 180 * latitude
        d = toDays(date)
        n = julianCycle(d,lw)
        ds = approxTransit(0,lw,n)
        m = solarMeanAnomaly(ds)
        l = eclipticLongitude(m)
        dec = declination(l,0)
        julianNoon = solarTransitJulian(ds,m,l)
        result = {'solarNoon': fromJulian(julianNoon), 'nadir': fromJulian(julianNoon - 0.5)}
        for i in range(len(self.times)):
            time = self.times[i]
            julianSet = getSetJulian(time[0] * math.pi / 180,lw,phi,dec,n,m,l)
            julianRise = julianNoon - (julianSet - julianNoon)
            result[time[1]] = fromJulian(julianRise)
            result[time[2]] = fromJulian(julianSet)

        return result

    def getMoonPosition(self,date,latitude,longitude):
        lw = math.pi / 180 * -longitude
        phi = math.pi / 180 * latitude
        d = toDays(date)
        c = moonCoords(d)
        h = siderealTime(d,lw) - c['ra']
        a = altitude(h,phi,c['dec'])
        # altitude correction or refraction
        a = a + math.pi / 180 * 0.017 / math.tan(a + math.pi / 180 * 10.26 / (a + math.pi / 180 * 5.10))
        return {'azimuth': azimuth(h,phi,c['dec']), 'altitude': a, 'distance': c['dist']}

    def getMoonIllumination(self,date):
        '''Calculations for illumination parameters of the moon,
           based on http://idlastro.gsfc.nasa.gov/ftp/pro/astro/mphase.pro formulas and
           Chapter 48 of "Astronomical Algorithms" 2nd edition by Jean Meeus (Willmann-Bell, Richmond) 1998.
        '''
        d = toDays(date)
        s = sunCoords(d)
        m = moonCoords(d)
        sdist = 149598000 # distance from earth to sun in km
        phi = math.acos(math.sin(s['dec']) * math.sin(m['dec']) + math.cos(s['dec']) * math.cos(m['dec']) * math.cos(s['ra'] - m['ra']))
        inc = math.atan2(sdist * math.sin(phi), m['dist'] - s['dist'] * math.cos(phi))
        angle = math.atan2(math.cos(s['dec']) * math.sin(s['ra'] - m['ra']),
                          math.sin(s['dec']) * math.cos(m['dec']) - math.cos(['dec']) * math.sin(m['dec']) * math.cos(s['ra'] - m['ra']))
        b = 1
        if angle < 0:
            b = -1
        return {'fraction': (1 + math.cos(inc))/2, 'phase': 0.5 + 0.5 * inc * b / math.pi, 'angle': angle}

    def getMoonTimes(self,date,latitude,longitude):
        ''' calculations for moon rise/set times
            based on http://www.stargazing.net/kepler/moonrise.html article
        '''
        # need to set hour = minute = second = 0
        t = Date(date.valueOf())
        t.setHours(0)
        t.setMinutes(0)
        t.setSeconds(0)
        t.setMilliseconds(0)

        hc = 0.133 * math.pi / 180
        p = self.getMoonPosition(t,latitude,longitude)
        h0 = p['altitude'] - hc
        rise, set = None, None
        for i in range(1,25,2):
            p1 = self.getMoonPosition(hoursLater(t,i),latitude,longitude)
            h1 = p1['altitude'] - hc
            p2 = self.getMoonPosition(hoursLater(t,i+1),latitude,longitude)
            h2 = p2['altitude'] - hc
            a = (h0 + h2) / 2 - h1
            b = (h2 - h0) / 2
            xe = -b / (2 * a)
            ye = (a * xe + b) * xe + h1
            d = b * b - 4 * a * h1
            roots = 0
            if d >= 0:
                dx = math.sqrt(d) / (math.yabs(a) * 2)
                x1 = xe - dx
                x2 = xe + dx
                if math.yabs(x1) <= 1:
                    roots += 1
                if math.yabs(x2) <= 1:
                    roots += 1
                if x1 < -1:
                    x1 = x2
            if roots == 1:
                if h0 < 0:
                    rise = i + x1
                else:
                    set = i + x1
            elif roots == 2:
                if ye < 0:
                    rise = i + x2
                    set = i + x1
                else:
                    rise = i + x1
                    set = i + x2
            if rise is not None and set is not None:
                break
            h0 = h2
        result = {'rise': None, 'set': None, 'alwaysUp': False, 'alwaysDown': False}
        if rise is not None:
            result['rise'] = hoursLater(t, rise)
        if set is not None:
            result['set'] = hoursLater(t, set)
        if rise is None and set is None:
            if ye > 0:
                result['alwaysUp'] = True
            else:
                result['alwaysDown'] = True

        return result

if __name__ == "__main__":
    times = SunCalc().getTimes(Date(), location['latitude'], location['longitude'])
    for k in times.keys():
        print "{0:13s} : {1:s}".format(k, times[k].toTimeString())
