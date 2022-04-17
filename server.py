import socket 
import threading 
import time
import pickle

# 156, DELAY IF TIMESTAMP IS LARGER THAN CURRENT ONE PLUS DELAy
# WILL PROBABLY HAVE TO DO THIS FOR GLAD
# CHECK IF RPL SOCKET LIST IS NECESSARY
# MAY BE ABLE TO REMOVE READ SIGNALS ENTIRELY 

# Set up global variables
status = []  # Message to pass data between threads
dependency = {}  # Dependency data for the server, used as main reference for consistency
loc = int(input("Which data center is this (1, 2, or 3)?\n"))  # Server ID, user input
clock = 0 # Lamport clock to handle timestamps

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
    # declare global variables
    global status
    global dependency
    global clock
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
                clock = data[2]
                dependency[client].append([op_signal[2:], [loc, clock]])
                status = [op_signal[2:], [loc, clock],client]
                print("Alice: I have lost my wedding ring! (recieved directly from client at time " + str(clock) + ")")
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
                    clock = data[2]
                    dependency[client].append([op_signal[2:], [loc, clock]])
                    status = [op_signal[2:], [loc, clock],client]
                    print("Alice: I have found my wedding ring! (recieved directly from client at time " + str(clock) + ")")
                    op_signal = "OP_NULL"
                else:
                    print("Could not commit message. Alice has not yet lost her wedding ring.")
                    op_signal = "OP_NULL"
            if op_signal[2:] == "GLAD":
                dep_check = 0
                time_check = 0
                # Checks to see if FOUND is in any of the current dicts at the given time
                for d in dependency:
                    if len(dependency[d]) != 0:
                        for i in range(0,len(dependency[d])):
                            if "FOUND" in dependency[d][i][0]:
                                dep_check = 1
                                time_check = dependency[d][i][1][1]
                                break
                if dep_check == 1:
                    # Check to see if the dependency is in on time, if not, stall until it arrives
                    if data[2] < time_check:
                        delta_time = time_check - data[2] + 1
                        print("GLAD recieved before dependency, stalling for " + str(delta_time) + " seconds.")
                        time.sleep(delta_time)
                        clock = data[2] + delta_time
                    else:
                        clock = data[2]
                    # Sends out signal with the right clock
                    dependency[client].append([op_signal[2:], [loc, clock]])
                    status = [op_signal[2:], [loc, clock],client]
                    print("Bob: I am glad to hear that! (recieved directly from client at time " + str(clock) + ")")
                    op_signal = "OP_NULL"
                    break
                # Don't commit message if dependencies aren't met
                else:
                    print("Could not commit message. Alice has not yet found her wedding ring.")
                    op_signal = "OP_NULL"
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
    print("Server " + str(srv_port-8099) + " is online")
    srv_sock.bind(('127.0.0.1', srv_port))
    srv_sock.listen()
    while True:
        srv, address = srv_sock.accept()
        print("Server on port " + str(address[1]) + " ready to accept requests")
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
            # Send data over to requesting server, along with delay
            status.append(delay)
            data = pickle.dumps(status)
            srv.send(data)
            del status[-1]
            if delay == 2: # Prevent thread from looping before all changes have been propogated
                time.sleep(2.1)
            if delay == 4 or loc == 2: # Only clear when we know its the last propogated signal
                status = [] # Reset status list to indicate that we are done updating the other servers
            
# Handles incoming requests from other servers
def replica_target(in_port):
    global clock
    # Connect to corresponding server, inform them of your location
    print("Accepting requests from Server " + str(in_port-8099))
    rpl_sock_list.append(socket.socket())
    rpl_sock = rpl_sock_list[-1]
    rpl_sock.connect(('127.0.0.1', in_port))
    rpl_sock.send(str(loc).encode())
    while True:
    # Copy infomation from message into dependency list; if more messages exist, add another thing to the message to handle cases
        data = rpl_sock.recv(1024)
        dep_info = pickle.loads(data)
        client = dep_info[2]
        delay = dep_info[3]
        new_time = dep_info[1][1]+delay

        # Print message once recieved
        if dep_info[0] == "LOST":
            print("Alice: I have lost my wedding ring! (recieved from Server " + str(dep_info[1][0]) + " at time " + str(new_time) +  ")")

        if dep_info[0] == "FOUND":
            # In order to check the dependency, the dict has to be scanned due to how its set up. Wherever LOST is, use index to find the time it was sent
            old_time = 0 
            for d in dependency[client]: 
                if "LOST" in d:
                    old_time = d[1][1]
                    break            
            # Check if the clocks align for the dependency and the new message. If not, delay and update time.
            if new_time < old_time: 
                delta_time = old_time - new_time + 1
                print("FOUND recieved before dependency, stalling for " + str(delta_time) + "seconds.")
                time.sleep(delta_time)
                new_time = new_time + delta_time
            print("Alice: I have found my wedding ring! (recieved from Server " + str(dep_info[1][0]) + " at time " + str(new_time) +  ")")

        if dep_info[0] == "GLAD":
            # In order to check the dependency, the dict has to be scanned due to how its set up. Wherever LOST is, use index to find the time it was sent
            old_time = 0
            for d in dependency:
                if len(dependency[d]) != 0:
                    for i in range(0,len(dependency[d])):
                        if "FOUND" in dependency[d][i][0]:
                            old_time = dependency[d][i][1][1]
            # Check if the clocks align for the dependency and the new message. If not, delay and update time.
            if new_time < old_time: 
                delta_time = old_time - new_time + 1
                print("GLAD recieved before dependency, stalling for " + str(delta_time) + "seconds.")
                time.sleep(delta_time)
                new_time = old_time + delta_time
            print("Bob: I am glad to hear that! (recieved from Server " + str(dep_info[1][0]) + " at time " + str(new_time) +  ")")

        # Put information into dict, depending on if it already is there or not
        if client in dependency.keys():
            dependency[client].append([dep_info[0], [dep_info[1][0], new_time]])
        else:
            dependency[client] = [[dep_info[0], [dep_info[1][0], new_time]]]

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

            