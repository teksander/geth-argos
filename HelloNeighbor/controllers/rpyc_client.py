# rpyc client
import rpyc
conn = rpyc.connect("localhost", 12345)
c = conn.root

# do stuff over rpyc
import time
print('update =', c.get_main_update())
time.sleep(2)
print('update =', c.get_main_update())
print('testing returned:', c.testthings(lambda x: x))  # calling a method of the remote service
print('update =', c.get_main_update())