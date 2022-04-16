import socket 
import threading 
import time
import pickle

# Set up global variables
status = []  # Message to pass data between threads
dependency = {}  # Dependency data for the server, used as main reference for consistency
loc = int(input("Which data center is this (1, 2, or 3)?\n"))  # Server ID, user input

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
rpl_sock_list = [] # Socket for inter-server connection (client-like function)
srv_sock = socket.socket() # Socket for inter-server connection (server-like function)
cli_sock = socket.socket() # Socket for client connection
cli_sock.bind(('127.0.0.1', port))
cli_sock.listen()

# Thread which handles client connections to the server
def client_target(cli, client):
    # set up variables to work with
    global status
    global dependency
    clock = 0 # Lamport clock to handle timestamps
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
        op_signal = data[0]
        if op_signal[0:2] == "W_":
            if op_signal[2:] == "LOST":
                clock += 1
                dependency[client].append([op_signal[2:], [loc, clock]])
                status = [op_signal[2:], [loc, clock],client]
                print("Alice: I have lost my wedding ring!")
                op_signal = "OP_NULL"
            if op_signal[2:] == "FOUND":
                # Perform dependency check recursively
                dep_check = 0
                for d in dependency[client]:
                    if "LOST" in d:
                        dep_check = 1
                        break
                if dep_check == 1:
                # Add to dict and send signal to primary_target thread to begin propogating
                    clock += 1
                    dependency[client].append([op_signal[2:], [loc, clock]])
                    status = [op_signal[2:], [loc, clock],client]
                    print("Alice: I have found my wedding ring!")
                    op_signal = "OP_NULL"
                else:
                    print("Could not commit message. Alice has not yet lost her wedding ring.")
            if op_signal[2:] == "GLAD":
                dep_check = 0
                for d in dependency: 
                    if dependency[d][0] == "FOUND": # If FOUND appears in any of the dependency entries
                        dep_check = 1
                        break
                if dep_check == 1:
                    clock += 1
                    dependency[client].append([op_signal[2:], [loc, clock]])
                    status = [op_signal[2:], [loc, clock],client]
                    print("Bob: I am glad to hear that!")
                    op_signal = "OP_NULL"
                    break
                # Somehow delay signal to avoid inconsistency
                else:
                    print("")
        if op_signal[0:2] == "R_":       
            if op_signal[2:] == "FOUND":
                op_signal = "OP_NULL"
            if op_signal[2:] == "GLAD":
                op_signal = "OP_NULL"
        if op_signal == "OP_NULL":
            continue
        if not data: 
            break 

# Sets up server to listen to other servers
def primary_listen():
    print("Established a server on port " + str(srv_port))
    srv_sock.bind(('127.0.0.1', srv_port))
    srv_sock.listen()
    while True:
        srv, address = srv_sock.accept()
        print("The server on port " + str(address[1]) + " is now accepting requests.")
        serverConnect = threading.Thread(target=primary_target, args=(srv,)).start()
        
# Propogates updates to other servers
def primary_target(srv):
    global status
    # Wait to recieve location info, so you can adjust delays accordingly
    data = srv.recv(1024)
    peer_loc = int(data.decode())
    while True:
        # When status is set, get ready to update other datacenters with the information contained within it 
        if len(status) != 0:
            # Simulate a delay which scales with distance
            delay = abs(peer_loc-loc)*2
            time.sleep(delay)
            # Send data over to requesting server
            data = pickle.dumps(status)
            srv.send(data)
            if delay == 2: # Prevent thread from looping before all changes have been propogated
                time.sleep(2.1)
            if delay == 4: # Only clear when we know its the last propogated signal
                status = [] # Reset status list to indicate that we are done updating the other servers
            
# Handles incoming requests from other servers
def replica_target(in_port):
    # Connect to corresponding server, inform them of your location
    print("Accepting requests from the server on port " + str(in_port))
    rpl_sock_list.append(socket.socket())
    rpl_sock = rpl_sock_list[-1]
    rpl_sock.connect(('127.0.0.1', in_port))
    rpl_sock.send(str(loc).encode())
    while True:
    # Copy infomation from message into dependency list; if more messages exist, add another thing to the message to handle cases
        data = rpl_sock.recv(1024)
        dep_info = pickle.loads(data)
        client = dep_info[2]
        # Put information into dict, depending on if it already is there or not
        if client in dependency.keys():
            dependency[client].append([dep_info[0], [dep_info[1][0], dep_info[1][1]]])
        else:
            dependency[client] = [[dep_info[0], [dep_info[1][0], dep_info[1][1]]]]
        # Print message once recieved
        if dep_info[0] == "LOST":
            print("Alice: I have lost my wedding ring!")
        if dep_info[0] == "FOUND":
            print("Alice: I have found my wedding ring!")
        if dep_info[0] == "GLAD":
            print("Bob: I am glad to hear that!")


#Establish server connection, wait for some time to allow me to get all the servers online, then begin connecting them to each other
listenConnect = threading.Thread(target=primary_listen, args=()).start()
print("Waiting 10 seconds...")
time.sleep(10)
for p in peer_port:
    replicaConnect = threading.Thread(target=replica_target, args=(p,)).start()

# Listen for connecting clients
while True:
    cli, address = cli_sock.accept()
    client = str(address[0])+":"+str(address[1])
    dependency[client] = [] # Add new connection to dependencies list
    # Get the threads running: one for serving client, one for serving the others, one per each of the others' servers
    clientConnect = threading.Thread(target=client_target, args=(cli,client)).start()

            