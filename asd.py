from collections import defaultdict

asd = defaultdict(list)

asd["lofasz"].append([1,2])
print(asd)
print(len(asd["lofasz"]))
asd["lofasz"].append([1,4])
print(asd)
print(len(asd["lofasz"]))
asd["lofasz"].append([3,5])
print(asd["lofasz"][-1:][0])