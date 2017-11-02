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
    en = 1
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
    #with open(f, "a") as myfile:
    #    myfile.write(s)
    return

def changeState(current, next):
    msg.printMsg("\n Changing from '{}' to '{}'...".format(current, next))
    return next

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
f = "./meres/20keres"+t+".txt"

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

            if (scanningID == "" and latestID not in finishedIDs):
                scanningID = latestID
            if (isScanning == True and scanningID != latestID):
                continue

            msg.printMsg("\n Edge detected, setting Reg500 to 1")
            client.write_register(dataReadyReg, 1)

            currentState = changeState(currentState,State.GetPosition)
            continue
    
    # Gets robot's current position data    
    elif (currentState == State.GetPosition):
        dataReady = client.read_holding_registers(newDataReadyReg,1)
        msg.printMsg("\n Checking if data is ready: {}".format(dataReady))
       
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
                    currentState = changeState(currentState,State.ReturnMovement)
                    continue

            currPos = [x,y]
            pointsx.append(float(x))
            pointsy.append(float(y))
            log("\n {},{}".format(x,y))
            pointDict[scanningID] = currPos
            #pointArray.append(currPos)
            msg.printMsg("\n Data ready signal changed to {}".format(dataReady))
            currentState = changeState(currentState,State.CheckPositionList)

            continue

    # Check if we already have two position data and can calculate next one
    elif (currentState == State.CheckPositionList):
        #print("{}, length: {} ".format(pointArray,len(pointArray)))
        if (isScanning):
            msg.printMsg("\n scanPoints length: {}".format(len(scanPoints)))               
            scanPoints.append(pointDict[scanningID])
            if (len(scanPoints) < 2):
                currentState = changeState(currentState,State.ReturnMovement
            else:
                scanPoints = []
                if (iterationCounter == maxIterations):
                    print("getting center")
                    currentState = changeState(currentState,State.CalculateCenter
                    continue
                currentState = changeState(currentState,State.CalculateNewPosition
        #if (len(pointArray) < 2):
        if (len(pointDict[scanningID]) < 2):
            currentState = changeState(currentState,State.ReturnMovement
        else:
            currentState = changeState(currentState,State.CalculateNewPositio

    # Need to find more points, return robot movement as it were
    elif (currentState == State.ReturnMovement):
        client.write_register(500,2)
        currentState = changeState(currentState,State.SignalWait

    # Calculates new position data and sends it to robot
    elif (currentState == State.CalculateNewPosition):
        newPointData = ujkeres(pointsx,pointsy,30)
        iterationCounter += 1
        newStart = newPointData["kezdo"]
        newEnd = newPointData["veg"]

        log("\n {},{}, start".format(newStart.astype(int)[0],newStart.astype(int)[1]))
        log("\n {},{}, end".format(newEnd.astype(int)[0],newEnd.astype(int)[1]))

        newSd = newStart - currPos
        newEd = newEnd - currPos

        nxd = newSd.astype(int)[0]
        nyd = newSd.astype(int)[1]

        nexd = newEd.astype(int)[0]
        neyd = newEd.astype(int)[1]
        

        print("Scan positions: {} -> {} ".format(newStart,newEnd))
        #print("nxd nyd {} {}".format(nxd,nyd))
        #print("nexd neyd {} {}".format(nexd,neyd))

        nxd = setNeg(nxd)
        nyd = setNeg(nyd)

        nexd = setNeg(nexd)
        neyd = setNeg(neyd)
        
        client.write_register(502, nxd)
        client.write_register(504, nyd)

        client.write_register(506, nexd)
        client.write_register(508, neyd)

        client.write_register(500, 0)
        isScanning = True
        currentState = changeState(currentState,State.WaitScanReady

    #Calculates and moves to center
    elif (currentState == State.CalculateCenter):
        c = findCircle(pointsx,pointsy)
        print("findcircle: {}, current pos: {}".format(c,currPos))
        c = np.array(c)       
        c = c - currPos

        cx = setNeg(c.astype(int)[0])
        cy = setNeg(c.astype(int)[1])

        client.write_register(512, cx)
        client.write_register(514, cy)
        time.sleep(0.5)
        client.write_register(500, 5)
        client.write_register(510, 1)
        currentState = changeState(currentState,State.Stop

    elif (currentState == State.Stop):
        var = raw_input("finished?")
        log("finished")
        file = open("idmeres.txt","w")
        file.write(pointDict)

    elif (currentState == State.WaitScanReady):
        dataReady = client.read_holding_registers(newDataReadyReg,1)
        dataReady = dataReady.registers[0]
        if (dataReady == 5):
            currentState = changeState(currentState,State.SignalWait
            stateMachine.event("ScanReady")

    #msg.printMsg("input: {} | filtered: {} | edge: {} ".format(input_v,signal,signalEdge))

client.close()

