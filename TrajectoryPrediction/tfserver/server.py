import socket
import pickle

HEADERSIZE = 10
class Server(object):
    def __init__(self, ip=socket.gethostname(), port=1234, nb_clients=10) -> None:
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET is for IPV4, and SOCK_STREAM is for TCP
        self.ip = socket.gethostbyname(ip)
        self.ip = "172.18.0.1"
        self.port = port
        self.server.bind((self.ip, self.port))
        self.server.listen(nb_clients)
        self.clientsocket, self.address = None, None

    def accept_new_connection(self):
        print(f"Waiting for clients, my ip is {self.ip} and my port is {self.port}")
        self.clientsocket, self.address = self.server.accept()
        print(f"connection from {self.address} has been established!")

    def get_message(self):
        """Accepts a new tcp connection to the server, receives a message, decodes it and returns that message.

        Returns:
            string: The message received
            It should normaly be a dictionnary of the form : 
            >>> d = {'ID': 5, 'weights': [1, 2, 3, 4]}
            where you have 2 keys : ID and weights.
            ID is the id of the robot sending the message/dictionnary, it will be usefull to know which data file to open.
            Weights is a list of the weights the robots wants to assign to it's neural network.
        """

        end_message = False
        new_message = True
        full_msg = b''
        while not end_message:
            msg = self.clientsocket.recv(1024)
            if new_message:
                print(f'new message length: {msg[:HEADERSIZE]}')
                msglen = int(msg[:HEADERSIZE])
                new_message = False

            full_msg += msg


            if len(full_msg)-HEADERSIZE == msglen:
                print("full msg received")
                dico = pickle.loads(full_msg[HEADERSIZE:])
                end_message = True
        return dico

    def send_message(self, msg):
        """Send a message to the last connection accepted.

        Args:
            msg (string): The message you want to send.
        """
        # msg = "Welcome to the server!"
        msg = pickle.dumps(msg)
        msg = bytes(f'{len(msg):<{HEADERSIZE}}', "utf-8") + msg
        self.clientsocket.send(msg)
    
    def send_weights(self, weights):
        """Send a list of weights to the last connection accepted.

        Args:
            weights (list): The weights you want to send.
        """
        msg = pickle.dumps(weights)
        msg = bytes(f'{len(msg):<{HEADERSIZE}}', "utf-8") + msg
        self.clientsocket.send(msg)


    
    
# HEADERSIZE = 10

# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET is for IPV4, and SOCK_STREAM is for TCP

# """
# The AF_INET constant is named as such because it stands for "Address Family: Internet" and specifically
# refers to the IPv4 protocol. The "AF" part of the name comes from the term "address family," which is a
# general term used to refer to the set of protocols that are used for communicating over a network. 
# The "INET" part of the name comes from the term "Internet," which refers to the global network of 
# interconnected computers that use the Internet Protocol (IP) for communication. Together, the name 
# "AF_INET" indicates that the constant represents the address family for the Internet Protocol 
# version 4 (IPv4).
# """
# ip = socket.gethostname()
# port = 1235
# s.bind((ip, port))

# s.listen(5) # the number indicates the max queue size, i think for the purpose of the master thesis we will set the queue size to the number of robots.*

# while True:
#     clientsocket, address = s.accept()
#     msg = clientsocket.recv(128)
#     msg = msg.decode("utf-8")[HEADERSIZE:]
#     print(f"connection from {address} has been established!")
#     print(f"the client message : {msg}")

#     msg = "Welcome to the server!"
#     msg = f'{len(msg):<{HEADERSIZE}}{msg}'

#     clientsocket.send(bytes(msg,"utf-8"))
#     time.sleep(10)



        