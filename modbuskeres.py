import sys
import numpy as np
import RPi.GPIO as GPIO
import serial
import time
from pymodbus.client.sync import ModbusTcpClient
from helper import Edge, Filter
from statemachine import StateMapElement, StateMachine
from datetime import datetime
from ujkeres import ujkeres
from korkeres import findCircle
from collections import defaultdict

class Msg:
    msg = ""
    cnt = 0
    cursorup = '\033[F'
    erase = '\033[K'
    en = 0;
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


def getSigned16bit(a):
    if (a >> 15) & 1:
        return a - (1 << 16)
    return a


GPIO.setmode (GPIO.BCM)
GPIO.setup(4, GPIO.IN)
serialPort = serial.Serial('/dev/ttyS0',9600)

dataReadyReg = 500
dataXReg = 1000
dataYReg = 1002
newDataReadyReg = 1006
dataRead = 0
client = ModbusTcpClient('192.168.0.104',502)
conn = client.connect()

SignalFilter = Filter(16)
SignalEdge = Edge()
ReadyEdge = Edge()
msg = Msg()


edgeDetected = 0
dataReadyEdgeDetected = 0

stateMap = [
    StateMapElement("SignalRise","SignalWait","GetPosition"),
    StateMapElement("RobotPositionReady","GetPosition","CheckPositionList"),
    StateMapElement("FalsePosition","GetPosition","ReturnMovement"),
    StateMapElement("GetMoreInitialPos","CheckPositionList","ReturnMovement"),
    StateMapElement("GetNextPos","CheckPositionList","CalculateNewPosition"),
    StateMapElement("RetMov","ReturnMovement","SignalWait"),
    StateMapElement("NewPositionSet","CalculateNewPosition","WaitScanReady"),
    StateMapElement("ScanReady","WaitScanReady","SignalWait"),
    StateMapElement("ReturnScanning","CheckPositionList","ReturnMovement"),
    StateMapElement("IterationOver","CheckPositionList","CalculateCenter"),
    StateMapElement("Finished","CalculateCenter","Stop"),
    StateMapElement("RetMov","SignalWait","SignalWait")
]

stateMachine = StateMachine(stateMap)

pointArray = []
currPos = []

client.write_register(dataReadyReg, 0)
client.write_register(510, 0)


def setNeg(n):
    if (n < 0):
        return n+pow(2,16)
    else:
        return n

t = datetime.now().time().strftime("%H%M%S")
f = "./meres/20keres"+t+".txt"

def log(s):
    with open(f, "a") as myfile:
        myfile.write(s)
    return

scanPoints = []
scanning = 0
iterationCounter = 0
maxIterations = 2
maxScanDiff = 0.5

pointDict = defaultdict(list)

scanningID = ""

def getExpectedCenterPoints(points):
    # ! handle radius dependency on distance from tag
    r = 4
    a = points[0]
    b = points[1]

    distance = np.linalg.norm(a-b)

    mid = (a+b)/2

    m =  sqrt(pow(r,2)-pow(distance/2,2))

    diff = a-b

    if (diff[0] == 0):
        mmeroleges = 0
        iranyvektor = np.array([0,1])
    else:
        m = diff[1]/diff[0]
        if (m == 0):
            iranyvektor = np.array([0,1])
        else:
            mmeroleges = -1/m
            iranyvektor = np.array([1,mmeroleges] / np.sqrt(1+mmeroleges**2))

    center1 = mid - iranyvektor * m
    center2 = mid + iranyvektor * m

while 1:
    signalType = ""

    cs = stateMachine.currentState

    # Waits for RFID signal edge
    if (cs == "SignalWait"):
        input_v = GPIO.input(4)    

        signal = SignalFilter.step(input_v)
        
        signalEdge = SignalEdge.chk(signal)
        signalType = signalEdge['type']

        # Notify robot of RFID signal change
        if (signalEdge['value'] == 1):
            line = serialPort.readLine()

            # !!! ?handle timeout? !!!
            newID = line.replace("\x02","").replace("\x03","")
            if (scanningID == "")
                scanningID = newID
            if (scanning == 1 and scanningID != newID) 
                stateMachine.event("RetMov")

            msg.printMsg("\n Edge detected, setting RegdataReadyReg to 1")
            client.write_register(dataReady, 1)
            stateMachine.event("SignalRise")
            continue
    
    # Gets robot's current position data    
    elif (cs == "GetPosition"):
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
            x = getSigned16bit(xy.registers[0])
            y = getSigned16bit(xy.registers[2])

            if (len(currPos)>0):
                # Filter positions too close to each other
                d = np.linalg.norm(np.array([x,y])-np.array(currPos))
                if (d < 10):
                    stateMachine.event("FalsePosition")
                    continue

            currPos = [x,y]
            log("\n {},{}".format(x,y))

            pointDict[scanningID].append(currPos)

            msg.printMsg("\n Data ready signal changed to {}".format(dataReady))
            stateMachine.event("RobotPositionReady")
            continue

    # Check if we already have two position data and can calculate next one
    # Check if the two points are where they are supposed to be, if not, there
    # was probably a tag overlap
    elif (cs == "CheckPositionList"):
        #print("{}, length: {} ".format(pointArray,len(pointArray)))
        if (scanning == 1):
            scanPoints.append(currPos)
            if (len(scanPoints) < 2):
                stateMachine.event("ReturnScanning")
            else:
                #scanPoints = []
                if (iterationCounter == maxIterations):
                    print("getting center")
                    stateMachine.event("IterationOver")
                    continue
                
                scanMiddle = (scanPoints[0]+scanPoints[1]) / 2
                
                currentPointList = pointDict[scanningID]

                expectedCenters = getExpectedCenterPoints(currentPointList[-2:])

                if (np.linalg.norm(expectedCenters[0] - scanMiddle) > maxScanDiff or
                np.linalg.norm(expectedCenters[1] - scanMiddle) > maxScanDiff )
                    # átfedés lekezelése
                    
                scanPoints = []
                stateMachine.event("GetNextPos")
                
        if (len(pointArray) < 2):
            stateMachine.event("GetMoreInitialPos")
        else:
            stateMachine.event("GetNextPos")

    # Need to find more points, return robot movement as it were
    elif (cs == "ReturnMovement"):
        client.write_register(dataReady,2)
        stateMachine.event("RetMov")
        

    # Calculates new position data and sends it to robot
    elif (cs == "CalculateNewPosition"):
        currPoints = pointDict[currentID]
        currXs = [p[0] for p in currPoints]
        currYs = [p[1] for p in currPoints] 
        newPointData = ujkeres(currXs, currYs, 30)
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

        client.write_register(dataReady, 0)
        scanning = 1
        stateMachine.event("NewPositionSet")

    #Calculates and moves to center
    elif (cs == "CalculateCenter"):
        currPoints = pointDict[currentID]
        currXs = [p[0] for p in currPoints]
        currYs = [p[1] for p in currPoints] 

        c = findCircle(currXs, currYs)

        print("findcircle: {}, current pos: {}".format(c,currPos))
        c = np.array(c)       
        c = c - currPos

        cx = setNeg(c.astype(int)[0])
        cy = setNeg(c.astype(int)[1])

        client.write_register(512, cx)
        client.write_register(514, cy)
        time.sleep(0.5)
        client.write_register(dataReady, 5)
        client.write_register(510, 1)
        stateMachine.event("Finished")

    elif (cs == "Stop"):
        var = raw_input("finished?")
        log("finished")
        

    elif (cs == "WaitScanReady"):
        dataReady = client.read_holding_registers(newDataReadyReg,1)
        dataReady = dataReady.registers[0]
        if (dataReady == 5):
            stateMachine.event("ScanReady")

    #msg.printMsg("input: {} | filtered: {} | edge: {} ".format(input_v,signal,signalEdge))
client.close()