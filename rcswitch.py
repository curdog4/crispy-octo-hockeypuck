#!/usr/bin/env python

import os, sys
import time
from RPi import GPIO

RCSWITCH_MAX_CHANGES = 67

class RCSwitch():
    def __init__(self,receiverInterrupt=-1,transmitterPin=-1,pulseLength=350,repeatTransmit=10,
                 protocol=1,receiveTolerance=60,receivedValue=None,receivedBitLength=0,
                 receivedDelay=0,receivedProtocol=0,timings=[]):
        #GPIO.cleanup()
        GPIO.setmode(GPIO.BOARD)
        self.receiverInterrupt = receiverInterrupt
        self.transmitterPin = transmitterPin
        self.setPulseLength(pulseLength)
        self.setRepeatTransmit(repeatTransmit)
        self.setProtocol(protocol)
        self.setReceiveTolerance(receiveTolerance)
        self.receivedValue = receivedValue
        self.receivedBitLength = receivedBitLength
        self.receivedDelay = receivedDelay
        self.receivedProtocol = receivedProtocol
        self.timings = timings
        self.changeCount = 0
        self.lastTime = 0
        self.repeatCount = 0

    def __enter__(self):
        return self

    def __exit__(self,exc_type,exc_value,traceback):
        GPIO.cleanup()

    #def __del__(self):
    #    GPIO.cleanup()

    #@public
    def switchOn(self,group=-1,groupNumber=-1,groupName=None,family=None,switchNumber=-1,device=-1):
        if family >= 0 and group >= 0 and device >= 0:
            self.sendTriState( self.getCodeWordC(family,group,device,True) )
        elif groupNumber >= 0 and switchNumber >= 0:
            self.sendTriState( self.getCodeWordB(groupNumber,switchNumber,True) )
        elif group >= 0 and switchNumber >= 0:
            self.sendTriState( self.getCodeWordA(group,switchNumber,True) )
        return None

    def switchOff(self,group=-1,groupNumber=-1,groupName=None,family=None,switchNumber=-1,device=-1):
        '''
        Three ways to invoke this:
        1. family, group, and device (type C Intertechno)
          - family: FamilyCode (a..f)
          - group: group number (1..4)
          - device: device number (1..4)
        2. groupNumber and switchNumber (type B with 2 rotary/sliding switches)
          - groupNumber: number of the switch group (1..4)
          - switchNumber: number of the switch (1..4)
        3. groupName and switchNumber (type A with 10 pole DIP switches)
          - groupName: code of the switch group (position of DIP switches, 1 == on, 0 == off; so all on == '11111')
          - switchNumber: number of the switch (1..4)
        '''
        if family >= 0 and group >= 0 and device >= 0:
            self.sendTriState( self.getCodeWordC(family,group,device,False) )
        elif groupNumber >= 0 and switchNumber >= 0:
            self.sendTriState( self.getCodeWordB(groupNumber,switchNumber,False) )
        elif groupName is not None and switchNumber >= 0:
            self.sendTriState( self.getCodeWordA(groupName,switchNumber,False) )
        return None

    def sendTriState(self,code=None):
        for n in range(self.repeatTransmit):
            for i in range(len(code)):
                if code[i] == '0':
                    self.send0()
                elif code[i] == 'F':
                    self.sendF()
                elif code[i] == '1':
                    self.send1()
            self.sendSync()
        return None

    def send(self,code=None,length=0):
        if type(code) == type(0):
            sys.stdout.write("Converting integer code '%d' to string\n"%(code))
            if length == 0:
                length = len(code)
            code = dec2binWzerofill(code,length)
            sys.stdout.write("Code is now string '%s'\n"%(code))
        if type(code) == type('s'):
            for n in range(self.repeatTransmit):
                #sys.stdout.write("Loop '%d' of '%d' (repeatTransmit)\n"%(n,self.repeatTransmit))
                for i in range(len(code)):
                    #sys.stdout.write("Looping through code: %d of %d. Character is '%s'.\n"%(i,len(code),repr(code[i])))
                    if code[i] == '0':
                        #sys.stdout.write("Sending '0'...\n")
                        self.send0()
                    elif code[i] == '1':
                        #sys.stdout.write("Sending '1'...\n")
                        self.send1()
                self.sendSync()
        return None

    def enableReceived(self,interrupt=-1):
        '''
        Methods to discover: wiringPiISR()
        '''
        if interrupt >= 0:
            self.receiverInterrupt = interrupt
            self.receivedValue = None
            self.receivedBitLength = 0
            #wiringPiISR(self.receiverInterrupt, INT_EDGE_BOTH, self.handleInterrupt)
            GPIO.add_event_detect(self.transmitterPin, GPIO.BOTH, self.handleInterrupt)
        return None

    def disableReceive(self):
        self.receiverInterrupt = -1
        GPIO.remove_event_detect(self.transmitterPin)
        return None

    def available(self):
        return self.receivedValue != None

    def resetAvailable(self):
        self.receivedValue = None
        return None

    def getReceivedValue(self):
        return self.receivedValue

    def getReceivedBitLength(self):
        return self.receivedBitLength

    def getReceivedDelay(self):
        return self.receivedDelay

    def getReceivedProtocol(self):
        return self.receivedProtocol

    def getReceivedRawData(self):
        return self.timings

    def enableTransmit(self,transmitterPin=-1):
        '''
        Methods to discover: pinMode()
        '''
        if transmitterPin >= 0:
            self.transmitterPin = transmitterPin
            #pinMode(self.transmitterPin,GPIO.OUT)
            GPIO.setup(self.transmitterPin,GPIO.OUT)
        return None

    def disableTransmit(self):
        self.transmitterPin = -1
        return None

    def setPulseLength(self,pulseLength=-1):
        if pulseLength >= 0:
            self.pulseLength = pulseLength
        return None

    def setRepeatTransmit(self,repeatTransmit=-1):
        if repeatTransmit >= 0:
            self.repeatTransmit = repeatTransmit
        return None

    def setReceiveTolerance(self,receiveTolerance=-1):
        if receiveTolerance >= 0:
            self.receiveTolerance = receiveTolerance
        return None

    def setProtocol(self,protocol=0,pulseLength=-1):
        self.protocol = protocol
        if protocol == 1:
            if pulseLength >= 0:
                self.setPulseLength(pulseLength)
            else:
                self.setPulseLength(350)
        elif protocol == 2:
            if pulseLength >= 0:
                self.setPulseLength(pulseLength)
            else:
                self.setPulseLength(650)
        return None

    #@private
    def getCodeWordB(self,groupNumber=0,switchNumber=0,status=False):
        returnPos = 0
        returnVal = ""
        code = [ 'FFFF', '0FFF', 'F0FF', 'FF0F', 'FFF0' ]
        if groupNumber < 1 or groupNumber > 4 or switchNumber < 1 or switchNumber > 4:
            return chr(0)
        for i in range(4):
            returnVal[returnPos] = code[groupNumber][i]
            returnPos += 1
        for i in range(4):
            returnVal[returnPos] = code[switchNumber][i]
            returnPos += 1
        for i in range(3):
            returnVal[returnPos] = 'F'
            returnPos += 1
        if status == True:
            returnVal[returnPos] = 'F'
        else:
            returnVal[returnPos] = '0'
        returnPos += 1
        returnVal[returnPos] = chr(0)
        return returnVal

    def getCodeWordA(self,groupName=None,switchNumber=0,status=False):
        returnPos = 0
        returnVal = ""
        code = [ 'FFFFF', '0FFFFF', 'F0FFF', 'FF0FF', 'FFF0F', 'FFFF0' ]
        if switchNumber < 1 or switchNumber > 5:
            return chr(0)
        for i in range(5):
            if groupName[i] == '0':
                returnVal[returnPos] = 'F'
                returnPos += 1
            elif groupName[i] == '1':
                returnVal[returnPos] = '0'
                returnPos += 1
            else:
                return chr(0)
        for i in range(5):
            returnVal[returnPos] = code[switchNumber][i]
            returnPos += 1
        if status == True:
            returnVal[returnPos] = '0'
            returnPos += 1
            returnVal[returnPos] = 'F'
            returnPos += 1
        else:
            returnVal[returnPos] = 'F'
            returnPos += 1
            returnVal[returnPos] = '0'
            returnPos += 1
        returnVal[returnPos] = chr(0)
        return returnVal

    def getCodeWordC(self,family=None,group=0,device=0,status=False):
        returnPos = 0
        returnVal = ""
        if family < 97 or family > 112 or group < 1 or group > 4 or device < 1 or device > 4:
            return chr(0)
        deviceGroupCode = dec2binWzerofill( device - 1 + (group - 1) * 4, 4)
        code = [ '0000', 'F000', '0F00', 'FF00', '00F0', 'F0F0', '0FF0', 'FFF0', '000F', 'F00F', '0F0F', 'FF0F', '00FF', 'F0FF', '0FFF', 'FFFF' ]
        for i in range(4):
            returnVal[returnPos] = code[family-97][i]
            returnPos += 1
        for i in range(4):
            if deviceGroupCode[i] == '1':
                returnVal[returnPos] = 'F'
            else:
                returnVal[returnPos] = '0'
            returnPos += 1
        returnVal[returnPos] = '0'
        returnPos += 1
        returnVal[returnPos] = 'F'
        returnPos += 1
        returnVal[returnPos] = 'F'
        returnPos += 1
        if status == True:
            returnVal[returnPos] = 'F'
        else:
            returnVal[returnPos] = '0'
        returnPos += 1
        returnVal[returnPos] = chr(0)
        return returnVal

    def sendT0(self):
        self.transmit(1,3)
        self.transmit(1,3)
        return None

    def sendT1(self):
        self.transmit(3,1)
        self.transmit(3,1)
        return None

    def sendTF(self):
        self.transmit(1,3)
        self.transmit(3,1)
        return None

    def send0(self):
        if self.protocol == 1:
            self.transmit(1,3)
        elif self.protocol == 2:
            self.transmit(1,2)
        return None

    def send1(self):
        if self.protocol == 1:
            self.transmit(3,1)
        elif self.protocol == 2:
            self.transmit(2,1)
        return None

    def sendSync(self):
        if self.protocol == 1:
            self.transmit(1,31)
        elif self.protocol == 2:
            self.transmit(1,10)
        return None

    def transmit(self,highPulses=0,lowPulses=0):
        '''
        Methods to discover: digitalWrite(), delayMicroseconds()
        '''
        disabledReceive = False
        receiverInterrupt_backup = self.receiverInterrupt
        if self.receiverInterrupt != -1:
            self.disableReceive()
            disabledReceive = True
        #digitalWrite(self.transmitterPin, GPIO.HIGH)
        GPIO.output(self.transmitterPin, GPIO.HIGH)
        delayMicroseconds(self.pulseLength * highPulses)
        #digitalWrite(self.transmitterPin, GPIO.LOW)
        GPIO.output(self.transmitterPin, GPIO.LOW)
        delayMicroseconds(self.pulseLength * lowPulses)
        if disabledReceive == True:
            self.enableReceive(receiverInterrup_backup)
        return None

    def handleInterrupt(self):
        '''
        Methods to discover: micros()
        '''
        t = micros()
        duration = time - lastTime
        if duration > 5000 and duration > self.timings[0] - 200 and duration < self.timings[0] + 200:
            self.repeatCount += 1
            self.changeCount -= 1
            if self.repeatCount == 2:
                if self.receiveProtocol1(self.changeCount) == False:
                    if self.receiveProtocol2(self.changeCount) == False:
                        # Failed
                        pass
                self.repeatCount = 0
            self.changeCount = 0
        elif duration > 5000:
            self.changeCount = 0
        if self.changeCount >= RCSWITCH_MAX_SWITCHES:
            self.changeCount = 0
            self.repeatCount = 0
        self.changeCount += 1
        self.timings[self.changeCount] = duration
        self.lastTime = time
        return None

    def receiveProtocol1(self,changeCount=0):
        code = 0
        delay = self.timings[0] / 31
        delayTolerance = delay * self.receiveTolerance * 0.01
        for i in range(0,changeCount,2):
            if self.timings[i] > delay - delayTolerance and self.timings[i] < delay + delayTolerance and self.timings[i+1] > delay * 3 - delayTolerance and self.timings[i+1] < delay * 3 + delayTolerance:
                code = code << 1
            elif self.timings[i] > delay * 3 - delayTolerance and self.timings[i] < delay * 3 + delayTolerance and self.timings[i+1] > delay - delayTolerance and self.timings[i+1] < delay + delayTolerance:
                code += 1
                code = code << 1
            else:
                # Failed
                i = changeCount
                code = 0
        code = code >> 1
        if changeCount > 6:
            self.receivedValue = code
            self.receivedBitLength = changeCount / 2
            self.receivedDelay = delay
            self.receivedProtocol = 1
        if code == 0:
            return False
        elif code != 0:
            return True

    def receiveProtocol2(self,changeCount=0):
        code = 0
        delay = self.timings[0] / 10
        delayTolerance = delay * self.receiveTolerance * 0.01
        for i in range(0,changeCount,2):
            if self.timings[i] > delay - delayTolerance and self.timings[i] < delay + delayTolerance and self.timings[i+1] > delay * 2 - delayTolerance and self.timings[i+1] < delay * 2 + delayTolerance:
                code = code << 1
            elif self.timings[i] > delay * 2 - delayTolerance and self.timings[i] < delay * 2 + delayTolerance and self.timings[i+1] > delay - delayTolerance and self.timings[i+1] < delay + delayTolerance:
                code += 1
                code = code << 1
            else:
                # Failed
                i = changeCount
                code = 0
        code = code >> 1
        if changeCount > 6:
            self.receivedValue = code
            self.receivedBitLength = changeCount / 2
            self.receivedDelay = delay
            self.receivedProtocol = 2
        if code == 0:
            return False
        elif code != 0:
            return True

def pinMode(pin,mode):
    GPIO.setup(pin,mode)

def digitalWrite(pin,value):
    GPIO.output(pin,value)

def delayMicroseconds(duration):
    time.sleep( float(duration) / 1000000.0)

def wiringPiISR(pin,edge,callback):
    GPIO.add_event_detect(pin,edge,callback)

def micros():
    return time.time() * 1000000

def dec2binWzerofill(dec=0,length=0):
    binVal = bytearray(64)
    i = 0
    while dec > 0:
        if dec & 1 > 0:
            binVal[32+i] = '1'
        else:
            binVal[32+i] = '0'
        i += 1
        dec = dec >> 1
    for j in range(length):
        if j >= length - i:
            binVal[j] = binVal[ 31 + i - (j - (length - i)) ]
        else:
            binVal[j] = '0'
    binVal[length] = chr(0)
    return str(binVal)

def map_gpio_val(val):
    '''Map values for RPi.GPIO DATA
    BCM = 11
    BOARD = 10
    BOTH = 33
    FALLING = 32
    HARD_PWM = 43
    HIGH = 1
    I2C = 42
    IN = 1
    LOW = 0
    OUT = 0
    PUD_DOWN = 21
    PUD_OFF = 20
    PUD_UP = 22
    RISING = 31
    RPI_INFO = {'MANUFACTURER': 'Embest', 'P1_REVISION': 3, 'PROCESSOR': '...
    RPI_REVISION = 3
    SERIAL = 40
    SPI = 41
    UNKNOWN = -1
    '''
    if val == -1:
        return 'UNKNOWN'
    elif val == 0:
        return 'OUT'
    elif val == 1:
        return 'IN'
    elif val == 10:
        return 'BOARD'
    elif val == 11:
        return 'BCM'
    elif val == 20:
        return 'PUD_OFF'
    elif val == 21:
        return 'PUD_DOWN'
    elif val == 22:
        return 'PUD_UP'
    elif val == 31:
        return 'RISING'
    elif val == 32:
        return 'FALLING'
    elif val == 33:
        return 'BOTH'
    elif val == 40:
        return 'SERIAL'
    elif val == 41:
        return 'SPI'
    elif val == 42:
        return 'I2C'
    elif val == 43:
        return 'HARD_PWM'
    else:
        return None

if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-c", "--code", dest="code", type='str',
                      help="send code CODE", metavar="CODE")
    parser.add_option("-p", "--pulse", dest="pulse", type='int',
                      help="use pulse length of PULSE", metavar="PULSE")
    parser.add_option("-t", "--txpin", dest="txpin", type='int',
                      help="use pin TXPIN for transmit", metavar="TXPIN")
    (options, args) = parser.parse_args()
    rcswitch = None

    sys.stdout.write("Current mode: %s\n"%(map_gpio_val(GPIO.getmode())))

    with RCSwitch() as rcswitch:
        rcswitch = RCSwitch()
        rcswitch.setRepeatTransmit(6)

        sys.stdout.write("Now mode is: %s\n"%(map_gpio_val(GPIO.getmode())))
        sys.stdout.write("Current channel function: %s\n"%(map_gpio_val(GPIO.gpio_function(options.txpin))))

        for pulse in range(options.pulse - 2, options.pulse + 3):
            sys.stdout.write("Setting pulse length to %d\n" % (pulse))
            try:
                rcswitch.setPulseLength(pulse)
            except Exception as e:
                sys.stderr.write("Error setting pulse length to %d: %s\n"%(pulse,e))
                GPIO.cleanup()
                sys.exit(1)

            sys.stdout.write("Enabling transmit on %d\n"%(options.txpin))
            try:
                rcswitch.enableTransmit(options.txpin)
            except Exception as e:
                sys.stderr.write("Error enabling transmit: %s\n"%(e))
                GPIO.cleanup()
                sys.exit(1)
            sys.stdout.write("Now channel function is: %s\n"%(map_gpio_val(GPIO.gpio_function(options.txpin))))

            sys.stdout.write("Attempting to transmit code %s...\n"%(options.code))
            try:
                rcswitch.send(options.code,24)
            except Exception as e:
                sys.stderr.write("Error sending channel on code: %s\n"%(e))
                GPIO.cleanup()
                sys.exit(1)

            sys.stdout.write("Disabling transmit\n")
            try:
               rcswitch.disableTransmit()
            except Exception as e:
                sys.stderr.write("Error disabling transmit: %s\n"%(e))
                GPIO.cleanup()
                sys.exit(1)
            sys.stdout.write("Now channel function is: %s\n"%(map_gpio_val(GPIO.gpio_function(options.txpin))))

    sys.stdout.write("All done. Cleaning up and exiting.\n")
    #GPIO.cleanup()
    sys.exit(0)
