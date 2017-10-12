from helper import Filter, Edge
        
F = Filter(3)
E1 = Edge()
while 1:
    i = input()
    f = F.step(i)
    print("filtered: {} | edge: {}".format(f,E1.chk(f)))
