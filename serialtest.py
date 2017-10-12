import serial
import RPi.GPIO as GPIO

class Filter:
    f = 0
    o = 0
    bit = 0
    def __init__(self, bit):
        self.bit = bit
        
    def step(self, inV):
        self.f = (self.f<<1) % pow(2,self.bit) + inV
        if (self.f == 0):
            self.o = 0
        elif (self.f == pow(2,self.bit)-1):
            self.o = 1
        return self.o

class Edge:
    prev = 0
    t = "rising"
    def chk(self, inV):
        self.o = inV ^ self.prev
        if (self.o):
            if (self.prev == 0):
                self.t = "rising"
            else:
                self.t = "falling"
        self.prev = inV
        return {'value': self.o, 'type': self.t}

SignalEdge = Edge()
SignalFilter = Filter(16)

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN)

port = serial.Serial('/dev/ttyS0',9600)

while True:
    t = GPIO.input(4)
    print(t)
    #signal = SignalFilter.step(t)
    #edge = SignalEdge.chk(signal)
    
    #if (edge['value']==1):
      #  line = port.readline()
      #  print(line)
        