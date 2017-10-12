import numpy as np

def findCircle(xArr,yArr):
    M = np.empty((0,3),int)
    b = np.empty((0,1),int)
    for i in range(0,len(xArr)):
            xi = xArr[i]
            yi = yArr[i]
            M = np.append(M, np.array([[xi,yi,1]]),axis=0)
            b = np.append(b, np.array([[-xi*xi-yi*yi]]),axis=0)
            
    a = np.linalg.lstsq(M, b)[0]
    a1 = -a[0]/2
    a2 = -a[1]/2
    return [a1[0],a2[0]]
