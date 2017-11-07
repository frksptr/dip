import numpy as np

def ujkeres(x,y,r):
    a = getFurthestNeighbors(x,y)
    print("furthest neighbors: {} - {}".format(a[0],a[1]))
    p1 = np.array(a[0])
    p2 = np.array(a[1])

    felezo = (p1+p2)/2
    diff = p1-p2
    #print("diff {}".format(diff))
    n = np.linalg.norm(diff)
    #print("n {}".format(n))
    scale = 1/(n/(2*r)*r)
    #print("scale {}".format(scale))
    if (diff[0] == 0):
        mmeroleges = 0
        iranyvektor = np.array([1,0])
    else:
        m = diff[1]/diff[0]
        if (m == 0):
            iranyvektor = np.array([0,1])
        else:
            mmeroleges = -1/m
            iranyvektor = np.array([1,mmeroleges] / np.sqrt(1+mmeroleges**2))
    
    #print("iranyvektor {}".format(iranyvektor))
    #print("felezo {}".format(felezo))
    kezdo = felezo + iranyvektor*(2*r)
    veg = felezo - iranyvektor*(2*r)
    return {'kezdo': kezdo, 'veg': veg}

def sortCCW(xArray, yArray):
    cx = np.mean(xArray)
    cy = np.mean(yArray)
    tan = np.arctan2(yArray - cy, xArray - cx)

    s = np.argsort(tan)
    x = np.array(xArray)
    y = np.array(yArray)
    xs = x[s]
    ys = y[s]
    return {'x': xs, 'y': ys}

def getFurthestNeighbors(x, y):
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
            Mj  = j
    p1 = [x[Mi],y[Mi]]
    p2 = [x[Mj],y[Mj]]
    return [p1,p2]
