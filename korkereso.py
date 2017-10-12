import numpy as np
import matplotlib.pyplot as plt

def findCircle(array):
    M = np.empty((0,3),int)
    b = np.empty((0,1),int)
    x = np.array([])
    y = np.array([])
    startx = []
    starty = []
    endx = []
    endy = []
    f = "./meres/keres105241.txt"
    with open(f,"r") as file:
        for line in file:
            currentline = line.split(",")
            if (len(currentline) == 2):
                xi = int(currentline[0])
                yi = int(currentline[1])
                M = np.append(M, np.array([[xi,yi,1]]),axis=0)
                b = np.append(b, np.array([[-xi*xi-yi*yi]]),axis=0)
                x = np.append(x,xi)
                y = np.append(y,yi)
            elif(len(currentline) == 3):
                xi = int(currentline[0])
                yi = int(currentline[1])
                if ("start" in currentline[2]):
                    startx.append(xi)
                    starty.append(yi)
                if ("end" in currentline[2]):
                    endx.append(xi)
                    endy.append(yi)

    a = np.linalg.lstsq(M, b)[0]
    a1 = -a[0]/2
    a2 = -a[1]/2
    
    print(a1)
    print(a2)
    
    plt.scatter(x, y)
    plt.scatter(a1,a2,color='red')
    plt.scatter(startx,starty,color='yellow')
    plt.scatter(endx,endy,color='green')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.autoscale('True','both','False')
    plt.show()


findCircle([])
