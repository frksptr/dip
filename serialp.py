import sys
import serial

import RPi.GPIO as GPIO

def readID(port):
    line = port.readline()
    return line.replace("\x02","").replace("\x03","")


serialPort = serial.Serial('/dev/ttyS0',9600)



while(True):
    a = raw_input(": ")
    if (str(a) == "a"):       
        latestID = readID(serialPort)
        print(latestID)
    