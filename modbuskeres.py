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
    StopAll = 9


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
    line = port.readline().rstrip().replace("\x02","").replace("\x03","")
    if (len(line)==12):
        return line
    else:
        return ""

def log(s):
    with open(f, "a+") as myfile:
        myfile.write(s)
    return

def changeState(current, next):
    msg.printMsg("\n Changing from '{}' to '{}'...".format(current, next))
    return next

###############################################################################################

# Raspberry config
GPIO.setmode (GPIO.BCM)
GPIO.setup(4, GPIO.IN)
serialPort = serial.Serial('/dev/ttyS0', 9600, timeout = 0.4)

# Communication registers
dataReadyReg = 500
dataXReg = 1000
dataYReg = 1002
newDataReadyReg = 1006
scanReadyReg = 1008
dataRead = 0

id1RegX = 520
id1RegY = 522
id2RegX = 524
id2RegY = 526
startIdSwayReg = 530


ip = '192.168.0.104'
client = ModbusTcpClient(ip, 502)
conn = client.connect()
 
SignalFilter = Filter(16)
SignalEdge = Edge()
ReadyEdge = Edge()
msg = Msg()

edgeDetected = 0
dataReadyEdgeDetected = 0

currPos = []



t = datetime.now().time().strftime("%H%M%S")
f = "./meres/40keresKozep"+t+".txt"

idsToSearch = 2

scanPoints = []
isScanning = False
pointsx = defaultdict(list)
pointsy = defaultdict(list)
iterationCounter = 0
maxIterations = 1
pointDict = defaultdict(list)
centerDict = defaultdict(list)

latestID = ""
scanningID = ""
finishedIDs = []

currentState = State.SignalWait

client.write_register(500, 0)
client.write_register(510, 0)
client.write_register(530, 0)
client.write_register(1008,0)
client.write_register(1006,0)

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
            if (signalEdge['type'] == "rising"):
                print("rising edge")
                latestID = readID(serialPort)
                print("latest id: {}".format(latestID))
                print("scanning id: {}".format(scanningID))
                print("finishedIDs: {}".format(finishedIDs))

                if (scanningID == "" and latestID not in finishedIDs and latestID != ""):
                    scanningID = latestID
                if (isScanning == True and scanningID != latestID):
                    continue

            if (signalEdge['type'] == "falling"):
                print("falling edge")
                if (len(finishedIDs) == 1 and (scanningID == "" or scanningID in finishedIDs)):
                    continue

            msg.printMsg("\n Edge detected, setting Reg500 to 1")
            client.write_register(newDataReadyReg, 0)
            client.write_register(dataReadyReg, 1)

            currentState = changeState(currentState,State.GetPosition)
            continue
    
    # Gets robot's current position data    
    elif (currentState == State.GetPosition):
        dataReady = client.read_holding_registers(newDataReadyReg,1)
        #msg.printMsg("\n Checking if data is ready: {}".format(dataReady))
       
        if (dataReady == None):
            msg.printMsg("dataready none")
            continue
        dataReady = dataReady.registers[0]

        readyEdge = ReadyEdge.chk(dataReady)

        #if (readyEdge['value'] == 1 and readyEdge['type'] == "rising"):
        if (dataReady == 1):
            client.write_register(newDataReadyReg,0)
            time.sleep(0.5)

            xy = client.read_holding_registers(dataXReg,4)
            x =  getSigned16bit(xy.registers[0])
            y = getSigned16bit(xy.registers[2])

            # If the point is too close to the latest one, disregard
            if (len(currPos)>0):
                d = np.linalg.norm(np.array([x,y])-np.array(currPos))
                if (d < 40):
                    currentState = changeState(currentState,State.ReturnMovement)
                    continue

            currPos = [x,y]
            pointsx[scanningID].append(float(x))
            pointsy[scanningID].append(float(y))
            log("\n {},{}".format(x,y))
            pointDict[scanningID].append(currPos)
            #pointArray.append(currPos)
            msg.printMsg("\n Data ready signal changed to {}".format(dataReady))

            #
            client.write_register(newDataReadyReg,0)

            currentState = changeState(currentState,State.CheckPositionList)
            continue

    # Check if we already have two position data and can calculate next one
    elif (currentState == State.CheckPositionList):
        msg.printMsg("\n Scanning: {}".format(isScanning))
        #print("{}, length: {} ".format(pointArray,len(pointArray)))
        if (isScanning):
            msg.printMsg("\n scanPoints length: {}".format(len(scanPoints)))               
            msg.printMsg("\n pointDict[{}][-1:][0]: {}".format(scanningID,pointDict[scanningID][-1:][0]))
            scanPoints.append(pointDict[scanningID][-1:][0])
            msg.printMsg("\n len(scanPoints): {}".format(len(scanPoints)))
            if (len(scanPoints) < 2):
                currentState = changeState(currentState,State.ReturnMovement)
            else:
                scanPoints = []
                msg.printMsg("\nIterationCounter: {} | max iterations: {}".format(iterationCounter,maxIterations))
                if (iterationCounter >= maxIterations):
                    iterationCounter = 0
                    print("getting center")
                    currentState = changeState(currentState, State.CalculateCenter)
                    continue
        #if (len(pointArray) < 2):
        msg.printMsg("\n len(pointDict[scanningID]) {}".format(len(pointDict[scanningID])))
        if (len(pointDict[scanningID]) < 2 or len(scanPoints) % 2 == 1):
            currentState = changeState(currentState, State.ReturnMovement)
        else:
            currentState = changeState(currentState, State.CalculateNewPosition)

    # Need to find more points, return robot movement as it were
    elif (currentState == State.ReturnMovement):
        client.write_register(500,2)
        currentState = changeState(currentState,State.SignalWait)

    # Calculates new position data and sends it to robot
    elif (currentState == State.CalculateNewPosition):
        newPointData = ujkeres(pointsx[scanningID],pointsy[scanningID],30)
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
        client.write_register(newDataReadyReg,0)
        isScanning = True
        currentState = changeState(currentState,State.WaitScanReady)

    
    #Calculates and moves to center
    elif (currentState == State.CalculateCenter):
        c = findCircle(pointsx[scanningID],pointsy[scanningID])
        print("findcircle: {}, current pos: {}".format(c,currPos))
        c = np.array(c)       
        cd = c - currPos

        cx = setNeg(cd.astype(int)[0])
        cy = setNeg(cd.astype(int)[1])

        client.write_register(512, cx)
        client.write_register(514, cy)
        time.sleep(0.5)
        #client.write_register(500, 5)
        #client.write_register(510, 1)
        
        centerDict[scanningID].append(c)
        finishedIDs.append(scanningID)
        scanningID = ""
        
        if (len(centerDict) == 1):
            client.write_register(500, 3)
            currentState = changeState(currentState, State.SignalWait)
        else:
            currentState = changeState(currentState, State.Stop)
            


    elif (currentState == State.Stop):

        id1 = finishedIDs[0]
        id2 = finishedIDs[1]
        
        #print("\nIDs:\n\t{}\n\t{}".format(id1,
        c1 = centerDict[id1][0]
        c2 = centerDict[id2][0]
        log("\nCenters: {} - {}".format(c1,c2))
        
        c1 = c1 - currPos
        c2 = c2 - currPos

        c1x = setNeg(c1.astype(int)[0])
        c1y = setNeg(c1.astype(int)[1])
        
        c2x = setNeg(c2.astype(int)[0])
        c2y = setNeg(c2.astype(int)[1])
        
        client.write_register(id1RegX, c1x)
        client.write_register(id1RegY, c1y)
        client.write_register(id2RegX, c2x)
        client.write_register(id2RegY, c2y)
     
        client.write_register(500, 3)
        client.write_register(startIdSwayReg, 1)
        currentState = changeState(currentState,State.StopAll)
        
    elif (currentState == State.StopAll):
        jkl = 0
        

    elif (currentState == State.WaitScanReady):
        dataReady = client.read_holding_registers(1008,1)
        dataReady = dataReady.registers[0]
        if (dataReady == 2):
            client.write_register(1008, 0)
            client.write_register(newDataReadyReg, 0)
            currentState = changeState(currentState,State.SignalWait)
            #stateMachine.event("ScanReady")

    #msg.printMsg("input: {} | filtered: {} | edge: {} ".format(input_v,signal,signalEdge))

client.close()


