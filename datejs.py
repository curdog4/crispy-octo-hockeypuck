#!/usr/bin/env python

import os, sys
import time
import math
import json

class Date():
    def __init__(self,dt=None):
        if dt is None:
            dt = time.time()
        self.dt = dt / 1000.0
        self.date_local = time.localtime(dt)
        self.date_utc = time.gmtime(dt)

    def getDate(self):
        return self.date_local[2]

    def getDay(self):
        return self.date_local[6]

    def getFullYear(self):
        return self.date_local[0]

    def getHours(self):
        return self.date_local[3]

    def getMilliseconds(self):
        return (self.dt - math.floor(self.dt)) * 1000.0

    def getMinutes(self):
        return self.date_local[4]

    def getMonth(self):
        return self.date_local[1]

    def getSeconds(self):
        return int(self.date_local[5])

    def getTime(self):
        return self.dt * 1000.0

    def getTimezoneOffset(self):
        return time.timezone / 60

    def getUTCDate(self):
        return self.date_utc[2]

    def getUTCDay(self):
        return self.date_utc[6]

    def getUTCFullYear(self):
        return self.date_utc[0]

    def getUTCHours(self):
        return self.date_utc[3]

    def getUTCMilliseconds(self):
        return self.getMilliseconds()

    def getUTCMinutes(self):
        return self.date_utc[4]

    def getUTCMonth(self):
        return self.date_utc[1]

    def getUTCSeconds(self):
        return int(self.date_utc[5])

    def getYear(self):
        return self.getFullYear()

    def parse(self,strTime,strFormat):
        return time.mktime(time.strptime(strTime,strFormat))

    def setDate(self,mday):
        self.dt = time.mktime( (self.date_local[0],  # year
                                self.date_local[1],  # month
                                mday,                # day of month
                                self.date_local[3],  # hour
                                self.date_local[4],  # minute
                                self.date_local[5],  # second
                                self.date_local[6],  # weekday
                                self.date_local[7],  # julian day (day of year)
                                self.date_local[8])) # DST flag: 0 == regular timezone, 1 == daylight savings timezone, -1 == guess based on day and time
        self.date_local = time.localtime(self.dt)
        self.date_utc = time.gmtime(self.dt)

    def setFullYear(self,year):
        self.dt = time.mktime( (year,                # year
                                self.date_local[1],  # month
                                self.date_local[2],  # day of month
                                self.date_local[3],  # hour
                                self.date_local[4],  # minute
                                self.date_local[5],  # second
                                self.date_local[6],  # weekday
                                self.date_local[7],  # julian day (day of year)
                                self.date_local[8])) # DST flag: 0 == regular timezone, 1 == daylight savings timezone, -1 == guess based on day and time
        self.date_local = time.localtime(self.dt)
        self.date_utc = time.gmtime(self.dt)

    def setHours(self,hour):
        self.dt = time.mktime( (self.date_local[0],  # year
                                self.date_local[1],  # month
                                self.date_local[2],  # day of month
                                hour,                # hour
                                self.date_local[4],  # minute
                                self.date_local[5],  # second
                                self.date_local[6],  # weekday
                                self.date_local[7],  # julian day (day of year)
                                self.date_local[8])) # DST flag: 0 == regular timezone, 1 == daylight savings timezone, -1 == guess based on day and time
        self.date_local = time.localtime(self.dt)
        self.date_utc = time.gmtime(self.dt)

    def setMilliseconds(self,milliseconds):
        self.dt = math.floor(self.dt) + milliseconds / 1000.0
        self.date_local = time.localtime(self.dt)
        self.date_utc = time.gmtime(self.dt)

    def setMinutes(self,minute):
        self.dt = time.mktime( (self.date_local[0],  # year
                                self.date_local[1],  # month
                                self.date_local[2],  # day of month
                                self.date_local[3],  # hour
                                minute,              # minute
                                self.date_local[5],  # second
                                self.date_local[6],  # weekday
                                self.date_local[7],  # julian day (day of year)
                                self.date_local[8])) # DST flag: 0 == regular timezone, 1 == daylight savings timezone, -1 == guess based on day and time
        self.date_local = time.localtime(self.dt)
        self.date_utc = time.gmtime(self.dt)

    def setMonth(self,month):
        self.dt = time.mktime( (self.date_local[0],  # year
                                month,               # month
                                self.date_local[2],  # day of month
                                self.date_local[3],  # hour
                                self.date_local[4],  # minute
                                self.date_local[5],  # second
                                self.date_local[6],  # weekday
                                self.date_local[7],  # julian day (day of year)
                                self.date_local[8])) # DST flag: 0 == regular timezone, 1 == daylight savings timezone, -1 == guess based on day and time
        self.date_local = time.localtime(self.dt)
        self.date_utc = time.gmtime(self.dt)

    def setSeconds(self,second):
        self.dt = time.mktime( (self.date_local[0],  # year
                                self.date_local[1],  # month
                                self.date_local[2],  # day of month
                                self.date_local[3],  # hour
                                self.date_local[4],  # minute
                                second,              # second
                                self.date_local[6],  # weekday
                                self.date_local[7],  # julian day (day of year)
                                self.date_local[8])) # DST flag: 0 == regular timezone, 1 == daylight savings timezone, -1 == guess based on day and time
        self.date_local = time.localtime(self.dt)
        self.date_utc = time.gmtime(self.dt)

    def setTime(self,dt):
        self.dt = dt / 1000.0
        self.date_local = time.localtime(self.dt)
        self.date_utc = time.gmtime(self.dt)

    def setUTCDate(self,mday):
        # TODO
        return None

    def setUTCFullYear(self,year):
        # TODO
        return None

    def setUTCHours(self,hour):
        # TODO
        return None

    def setUTCMilliseconds(self,millisecond):
        # TODO
        return None

    def setUTCMinute(self,minute):
        # TODO
        return None

    def setUTCMonth(self,month):
        # TODO
        return None

    def setUTCSeconds(self,second):
        # TODO
        return None

    def setYear(self,year):
        self.setFullYear(year)

    def toDateString(self):
        return time.strftime("%a %b %d %Y",self.date_local)

    def toGMTString(self):
        return self.toUTCString()

    def toISOString(self):
        return time.strftime("%FT%TZ")

    def toJSON(self):
        # TODO
        #return json.dumps({'time':self.dt,'localtime':self.date_local,'utctime':self.date_utc})
        return None

    def toLocaleDateString(self):
        return time.strftime("%x",self.date_local)

    def toLocaleTimeString(self):
        return time.strftime("%X",self.date_local)

    def toString(self):
        return self.toDateString() + " " + self.toTimeString()

    def toTimeString(self):
        return time.strftime("%H:%M:%S GMT%z (%Z)",self.date_local)

    def toUTCString(self):
        return time.strftime("%a, %d %b %Y %H:%M:%S GMT",self.date_utc)

    def UTC(self):
        return (self.dt - time.timezone) * 1000.0

    def valueOf(self):
        return self.dt * 1000.0

if __name__ == "__main__":
    dt = Date()
    print "Month day: " + str(dt.getDate())
    print "Day of week: " + str(dt.getDay())
    print "Year: " + str(dt.getFullYear())
    print "Hour: " + str(dt.getHours())
    print "Millisecond: " + str(dt.getMilliseconds())
    print "Minute: " + str(dt.getMinutes())
    print "Month: " + str(dt.getMonth())
    print "Second: " + str(dt.getSeconds())
    print "Time: " + str(dt.getTime())
    print "Timezone offset: " + str(dt.getTimezoneOffset())
    print "UTC month day: " + str(dt.getUTCDate())
    print "UTC day of week: " + str(dt.getUTCDay())
    print "UTC year: " + str(dt.getUTCFullYear())
    print "UTC hour: " + str(dt.getUTCHours())
    print "UTC millisecond: " + str(dt.getUTCMilliseconds())
    print "UTC minute: " + str(dt.getUTCMinutes())
    print "UTC month: " + str(dt.getUTCMonth())
    print "UTC second: " + str(dt.getUTCSeconds())
    print "Year: " + str(dt.getYear())
    #print dt.parse()
    #print dt.setDate()
    #print dt.setFullYear()
    #print dt.setHours()
    #print dt.setMilliseconds()
    #print dt.setMinutes()
    #print dt.setMonth()
    #print dt.setSeconds()
    #print dt.setTime()
    #print dt.setUTCDate()
    #print dt.setUTCFullYear()
    #print dt.setUTCHours()
    #print dt.setUTCMilliseconds()
    #print dt.setUTCMinute()
    #print dt.setUTCMonth()
    #print dt.setUTCSeconds()
    #print dt.setYear()
    print "Date string: " + dt.toDateString()
    print "GMT string: " + dt.toGMTString()
    print "ISO string: " + dt.toISOString()
    print "JSON: " + str(dt.toJSON())
    print "Locale date string: " + dt.toLocaleDateString()
    print "Locale time string: " + dt.toLocaleTimeString()
    print "String: " + dt.toString()
    print "Time string: " + dt.toTimeString()
    print "UTC string: " + dt.toUTCString()
    print "UTC: " + str(dt.UTC())
    print "Value of: " + str(dt.valueOf())
