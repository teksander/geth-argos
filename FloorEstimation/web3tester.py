import rpyc

conn = rpyc.connect("172.18.0.4", 4000, config = {"allow_all_attrs" : True})
w3 = conn.root
