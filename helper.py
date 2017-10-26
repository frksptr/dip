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