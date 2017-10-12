import numpy as np

x = [2,0,-3,6,0,-2]
y = [2,-5,0,0,5,2]
def sortCCW(xArray, yArray):
    cx = np.mean(xArray)
    cy = np.mean(yArray)
    tan = np.arctan2(yArray - cy, xArray - cx)

    s = np.argsort(tan)
    print(s)
    x = np.array(xArray)
    y = np.array(yArray)
    xs = x[s]
    ys = y[s]
    return {'x': xs, 'y': ys}

def asd(x, y):
    a = sortCCW(x,y)
    x = a['x']
    y = a['y']
    print(x)
    print(y)
    size = len(x)
    D = np.zeros((size,size),float)
    M = 0
    Mi = 0
    Mj = 0
    for i in range(0,size):
        pi = np.array([x[i],y[i]])
        if (i == size-1):
            j = 0
        else:
            j = i+1
        pj = np.array([x[j],y[j]])
        d = np.linalg.norm(pi-pj)
        if (d > M):
            M = d
            Mi = i
            Mj= j
    p1 = [x[Mi],y[Mi]]
    p2 = [x[Mj],y[Mj]]
    return [p1,p2]

a = asd(x,y)
print(a)
