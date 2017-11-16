from pymodbus.client.sync import ModbusTcpClient
import sys

dataReadyReg = 1006
dataXReg = 1000
dataYReg = 1002


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
    ip = '192.168.0.18'
    client = ModbusTcpClient(ip,502)
    conn = client.connect()
except:
    print(sys.exc_info()[0])
    raise

while True:
    text = input("?: ")
    splitText = text.split(" ")
    try:
        if (splitText[0] == "r"):
            print("Setting ready")
            client.write_register(dataReadyReg,1)
        elif (splitText[0] == "nr"):
            print("Setting ready")
            client.write_register(dataReadyReg,0)
        elif (is_number(splitText[0]) and is_number(splitText[1])):
            print("Setting coordinates")
            client.write_register(dataXReg, int(splitText[0]))
            client.write_register(dataYReg, int(splitText[1]))
        else:
            print("Wat")
    except Exception:
        print("WAT")

