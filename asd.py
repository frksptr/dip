from collections import defaultdict
from ujkeres import ujkeres
import RPi.GPIO as GPIO

# pdict = defaultdict(list)

# pdict["asd"].append([1,2])
# pdict["asd"].append([2,3])
# pdict["qwe"].append([4,5])
# print(pdict)
# asd = []
# print(pdict["asd"][-1:][0])
# asd.append(pdict["asd"][-1:][0])
# asd.append(pdict["asd"][-1:][0])
# print(asd)
# print(len(asd))

GPIO.setmode (GPIO.BCM)
GPIO.setup(4, GPIO.IN)

while True:
    input = GPIO.input(4)
    print(input)