from pymodbus.client.sync import ModbusTcpClient
import sys

#import RPi.GPIO as GPIO

#GPIO.setmode (GPIO.BCM)

#GPIO.setup(4, GPIO.IN)


def setNeg(n):
    if (n < 0):
        return ~n+1+pow(2,15)
    else:
        return n
    

try:
    client = ModbusTcpClient('192.168.0.18',502)
    conn = client.connect()
    print(conn)
    client.write_register(500, 13)
    asd = client.read_holding_registers(500,1)
    print(asd.registers[0])
    client.close()
except:
    print(sys.exc_info()[0])
    raise
