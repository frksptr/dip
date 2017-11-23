from pymodbus.client.sync import ModbusTcpClient
import sys

dataReadyReg = 1006
scanReadyReg = 1008
dataXReg = 1000
dataYReg = 1002

def getSigned16bit(a):
    if (a >> 15) & 1:
        return a - (1 << 16)
    return a

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
 
    return False


try:
    #ip = '192.168.0.42'
    ip = '152.66.159.75'
    client = ModbusTcpClient(ip,502)
    conn = client.connect()
except:
    print(sys.exc_info()[0])
    raise

while True:
    text = input("r | rr | sr | rb : ")
    splitText = text.split(" ")
    try:
        if (splitText[0] == "r"):
            print("Setting ready")
            client.write_register(dataReadyReg, 1)
        elif (splitText[0] == "sr"):
            print("Setting scanning ready")
            client.write_register(scanReadyReg, 2)
        elif (splitText[0] == "rr"):
            print("Retting ready")
            client.write_register(dataReadyReg, 0)
        elif (is_number(splitText[0]) and is_number(splitText[1])):
            print("Setting coordinates")
            client.write_register(dataXReg, int(splitText[0]))
            client.write_register(dataYReg, int(splitText[1]))
        elif (splitText[0] == "rb"):
            print("Reading back registers...")
            xy = client.read_holding_registers(dataXReg,4)
            r = client.read_holding_registers(dataReadyReg, 1).registers[0]
            sr = client.read_holding_registers(scanReadyReg, 1).registers[0]
            x = getSigned16bit(xy.registers[0])
            y = getSigned16bit(xy.registers[2])
            print("{} - {} |\nr: {}\nsr: {}".format(x,y,r,sr))
        else:
            print("Wat")
    except Exception:
        print("WAT")

