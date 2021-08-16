import rpyc

<<<<<<< HEAD
def identifersExtract(robotID, query = 'IP'):
    namePrefix = 'ethereum_eth.' + str(robotID) + '.'
    containersFile = open('identifiers.txt', 'r')
    for line in containersFile.readlines():
        if line.__contains__(namePrefix):
            if query == 'IP':
                return line.split()[-1]
            if query == 'ENODE':
                return line.split()[1]


robot1IP = identifersExtract(10)
print(robot1IP)
conn = rpyc.connect(robot1IP, 4000, config = {"allow_all_attrs" : True})
=======
conn = rpyc.connect("172.18.0.4", 4000, config = {"allow_all_attrs" : True})
>>>>>>> 71c7877b914d8b4fb1ac48f65c26fe0e8a98cbb3
w3 = conn.root
