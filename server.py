import socket 
import threading 
import time
import pickle

# REWRITE ENTIRE CODE TO MAKE IT SO ANY SERVER CAN SEND TO ANY OTHER 

# have everything use one thread for connecting, send a message on connection to identify either client or peer, logic from there
# have the other thread use the other servers' ports

# Set up global variables
status = []  # Message to pass data between threads
clock = 0  # Lamport clock to handle timestamps
dependency = {}  # Dependency data for the server, used as main reference for consistency
loc = int(input("Which data center is this (1, 2, or 3)?"))  # Server ID, user input

# Depending on where the server is, set port and recieve ports accordingly
if loc == 1: 
    port = 8000
    peer_port = [8101,8102]
if loc == 2:
    port = 8001 
    peer_port = [8100,8102]
if loc == 3:
    port = 8002
    peer_port = [8100,8101]

srv_port = port + 100

# Prepare sockets
srv_sock = socket.socket() # Socket for inter-server connection (server-like function)
rpl_sock = socket.socket() # Socket for inter-server connection (client-like function)

cli_sock = socket.socket() # Socket for client connection
cli_sock.bind(('127.0.0.1', port))
cli_sock.listen()

print("Loading...") # The message which displays before client connection


# Thread which handles client connections to the server
def client_target(cli, client):
    # Get client identity
    data = cli.recv(1024)
    if data.decode() == "A":
        name = "Alice"
    elif data.decode() == "B":
        name = "Bob"
    print(name + " has connected at " + client)
    # Send over datacenter ID
    cli.send(str(loc).encode()) 
    while True:
        data = cli.recv(1024)
        data = pickle.loads(data)
        op_signal = pickle.loads(data)[0]
        if op_signal[0:2] == "W_":
            if op_signal[2:] == "LOST":
                clock += 1
                dependency[client].append([op_signal[2:], [loc, clock]])
                status = [op_signal[2:], [loc, clock]]
                print("Alice: I have lost my wedding ring!")
            if op_signal[2:] == "FOUND":
                if "LOST" in dependency[client]:
                    clock += 1
                    dependency[client].append([op_signal[2:], [loc, clock]])
                    status = [op_signal[2:], [loc, clock]]
                    print("Alice: I have found my wedding ring!")
            if op_signal[2:] == "GLAD":
                for d in dependency: 
                    if dependency[d][0] == "FOUND": # If FOUND appears in any of the dependency entries
                        clock += 1
                        dependency[client].append([op_signal[2:], [loc, clock]])
                        status = [op_signal[2:], [loc, clock]]
                        print("Bob: I am glad to hear that!")
                        break
        if op_signal[0:2] == "R_":       
            if op_signal[2:] == "FOUND":
                pass
            if op_signal[2:] == "GLAD":
                pass
        if not data: 
            break 
        cli.send(data)

# Thread for every server-type connection to other servers
def primary_target():
    # Set up server
    srv_sock.bind(('127.0.0.1', srv_port))
    srv_sock.listen()
    srv, address = srv_sock.accept()
     # Wait to recieve location info, so you can adjust delays accordingly
    data = srv.recv(1024)
    peer_loc = int(data.decode())
    while True:
        # When status is set, get ready to send it to other datacenters 
        if len(status) != 0:
            # Simulate a delay which scales with distance
            delay = abs(peer_loc-loc)*2 
            time.sleep(delay)
            # Send data over to requesting server
            data = pickle.dumps(status)
            srv.send(data)
            
            
# Thread for every client-type connection to other servers
def replica_target(in_port):
    # Connect to corresponding server, inform them of your location
    rpl_sock.connect(('127.0.0.1', in_port))
    rpl_sock.send(str(loc).encode())
    while True:
    # Copy infomation from message into dependency list; if more messages exist, add another thing to the message to handle cases
        data = rpl_sock.recv(1024)
        dep_info = pickle.loads(data)
        dependency[client].append([dep_info[0], [dep_info[1][0], dep_info[1][1]]])
        # Print message once recieved
        if dep_info[0] == "LOST":
            print("Alice: I have lost my wedding ring!")
        if dep_info[0] == "FOUND":
            print("Alice: I have found my wedding ring!")
        if dep_info[0] == "GLAD":
            print("Bob: I am glad to hear that!")

while True:
    serverConnect = threading.Thread(target=primary_target, args=()).start()
    cli, address = cli_sock.accept()
    client = str(address[0])+":"+str(address[1])
    dependency[client] = [] # Add new connection to dependencies list
    print("Ready!")
    # Get the threads running: one for serving client, one for serving the others, one per each of the others' servers
    clientConnect = threading.Thread(target=client_target, args=(cli,client)).start()
    for p in peer_port:
        print(p,peer_port) 
        replicaConnect = threading.Thread(target=replica_target, args=(p,)).start()
            