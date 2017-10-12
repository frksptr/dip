import numpy as np
import matplotlib.pyplot as plt

def scatterPoints(file):
    x = np.array([])
    y = np.array([])
    with open(file,"r") as file:
              for line in file:
                  currentline = line.split(",")
                  if (len(currentline) > 1):
                      x = np.append(x,currentline[0])
                      y = np.append(y,currentline[1])
                      

    plt.scatter(x.astype(int), y.astype(int))
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.autoscale('True','both','False')
    plt.show()

scatterPoints("keres.txt")
