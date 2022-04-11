import socket 
import threading 
import time

clock = 0; # Set up a clock to keep track of 

loc = input("Which data center is this (1, 2, or 3)?")
if loc == 1:
    port = 8000
if loc == 2:
    port = 8001
if loc == 3:
    port = 8002
dependency = {} # List of connected peers
s = socket.socket() 
s.bind(('127.0.0.1', port)) 
s.listen() 
print("Waiting for clients...") # The message which displays before peers connect


def client_target(cli, client):
    # Get client identity
    data = cli.recv(1024)
    if data.decode() == "A":
        name = "Alice"
    elif data.decode() == "B":
        name = "Bob"
    print(name + " has connected at " + client)
    # Send over datacenter ID
    data = loc.encode()
    cli.send(data) 
    while True:
        data = cli.recv(1024)
        data = pickle.loads(data)
        op_signal = pickle.loads(data)[1]
        if op_signal[0:2] == "W_":
            if op_signal[2:] == "LOST":
                # update dependency
                # prop to others
                #might not even need all these ifs, just pass the slice as parameter
                pass
            if op_signal[2:] == "FOUND":
                pass
            if op_signal[2:] == "GLAD":
                pass
        if op_signal[0:2] == "R_"       
            if op_signal[2:] == "LOST":
                pass
            if op_signal[2:] == "FOUND":
                pass
            if op_signal[2:] == "GLAD":
                pass
        if not data: 
            break 
        cli.send(data)

while True: 
    cli, address = s.accept()
    client = str(address[0])+":"+str(address[1])
    dependency[client] = [] # Add new connection to dependencies list
    threading.Thread(target=client_target, args=(cli,client)).start()