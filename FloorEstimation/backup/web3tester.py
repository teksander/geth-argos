import rpyc

def identifersExtract(robotID, query = 'IP'):
    namePrefix = 'ethereum_eth.' + str(robotID) + '.'
    containersFile = open('identifiers.txt', 'r')
    for line in containersFile.readlines():
        if line.__contains__(namePrefix):
            if query == 'IP':
                return line.split()[-1]
            if query == 'ENODE':
                return line.split()[1]


robot1IP = identifersExtract(1)
print(robot1IP)
conn = rpyc.connect(robot1IP, 4000, config = {"allow_all_attrs" : True})
w3 = conn.root
