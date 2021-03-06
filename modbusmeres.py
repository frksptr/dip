import sys
import serial
import numpy as np
import RPi.GPIO as GPIO
import time

from pymodbus.client.sync import ModbusTcpClient
from helper import Edge, Filter
from statemachine import StateMapElement, StateMachine
from datetime import datetime
from ujkeres import ujkeres
from korkeres import findCircle
from enum import Enum
from collections import defaultdict

#######################################################################################################

class Msg:
    msg = ""
    cnt = 0
    cursorup = '\033[F'
    erase = '\033[K'
    en = 0
    def printMsg(self, msg):
        if (self.en == 0):
            return
        print(msg)
        #if (self.msg is msg):
         #   if (self.cnt > 1) :
          #      print(self.cursorup+self.erase)
           # self.cnt += 1
            #print(msg + " ({})".format(self.cnt))
        #else:
         #  self.cnt = 0
           #self.msg = msg
           #print(msg)


#y 30 110
#x 360 440
        
#z 25

#406-33

class State(Enum):
    SignalWait = 1
    GetPosition = 2
    CheckPositionList = 3
    CalculateNewPosition = 4
    WaitScanReady = 5
    ReturnMovement = 6
    CalculateCenter = 7
    Stop = 8


def setNeg(n):
    if (n < 0):
        return n+pow(2,16)
    else:
        return n

def getSigned16bit(a):
    if (a >> 15) & 1:
        return a - (1 << 16)
    return a

def readID(port):
    line = port.readline()
    return line.replace("\x02","").replace("\x03","")

def log(s):
    with open(f, "a+") as myfile:
        myfile.write(s)
    return

###############################################################################################

# Raspberry config
GPIO.setmode (GPIO.BCM)
GPIO.setup(4, GPIO.IN)

serialPort = serial.Serial('/dev/ttyS0',9600)

# Communication registers
dataReadyReg = 500
dataXReg = 1000
dataYReg = 1002
newDataReadyReg = 1006
dataRead = 0

client = ModbusTcpClient('192.168.0.104', 502)
conn = client.connect()

SignalFilter = Filter(16)
SignalEdge = Edge()
ReadyEdge = Edge()
msg = Msg()

edgeDetected = 0
dataReadyEdgeDetected = 0

pointArray = []
currPos = []



t = datetime.now().time().strftime("%H%M%S")
f = "meres/30seb8tav"+t+".txt"

idsToSearch = 2

scanPoints = []
isScanning = False
pointsx = []
pointsy = []
iterationCounter = 0
maxIterations = 3
pointDict = defaultdict(list)

latestID = ""
scanningID = ""
finishedIDs = []

currentState = State.SignalWait

client.write_register(500, 0)
client.write_register(510, 0)

while 1:
    signalType = ""

    # Waits for RFID signal edge
    if (currentState == State.SignalWait):
        input_v = GPIO.input(4)    
        signal = SignalFilter.step(input_v)

        signalEdge = SignalEdge.chk(signal)
        signalType = signalEdge['type']

        # Notify robot of RFID signal change
        if (signalEdge['value'] == 1):
            latestID = readID(serialPort)
            client.write_register(dataReadyReg, 1)
            currentState = State.GetPosition
            continue
    
    # Gets robot's current position data    
    elif (currentState == State.GetPosition):
        dataReady = client.read_holding_registers(newDataReadyReg,1)
        #msg.printMsg("\n Checking if data is ready: {}".format(dataReady))
       
        if (dataReady == None):
            msg.printMsg("dataready none")
            continue

        dataReady = dataReady.registers[0]

        readyEdge = ReadyEdge.chk(dataReady)['value']

        if (readyEdge):
            time.sleep(0.5)

            xy = client.read_holding_registers(dataXReg,4)
            x =  getSigned16bit(xy.registers[0])
            y = getSigned16bit(xy.registers[2])

            # If the point is too close to the latest one, disregard
            if (len(currPos)>0):
                d = np.linalg.norm(np.array([x,y])-np.array(currPos))
                if (d < 10):
                    currentState = State.ReturnMovement
                    continue

            currPos = [x,y]
            pointsx.append(float(x))
            pointsy.append(float(y))
            log("\n{},{},{}".format(latestID, x, y))
            pointDict[scanningID].append(currPos)
            #pointArray.append(currPos)
            msg.printMsg("\n Data ready signal changed to {}".format(dataReady))
            currentState = State.ReturnMovement
            continue


    # Need to find more points, return robot movement as it were
    elif (currentState == State.ReturnMovement):
        client.write_register(500,2)
        currentState = State.SignalWait
   

client.close()

