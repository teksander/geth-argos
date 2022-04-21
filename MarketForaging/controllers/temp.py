import socket

HOST = '172.18.0.3'  # The server's hostname or IP address
PORT = 9898        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    x = {213}
    s.sendall(str(x).encode())
    data = s.recv(1024)
    print(data)

