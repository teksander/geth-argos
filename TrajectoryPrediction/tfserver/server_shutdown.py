import socket
import pickle

HEADERSIZE = 10

ip = "172.18.0.1" # ip we wish to connect to 
port = 9801

msg = {'End': "Shut Down Server"}
msg = pickle.dumps(msg)
msg = bytes(f'{len(msg):<{HEADERSIZE}}', "utf-8") + msg
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.connect((ip,port))
    server.send(msg)

