import socket 
import os
import pickle
import time

identity = input("Are you Alice (A) or Bob (B)?\n")
if identity == "A": # Default Alice to West datacenter
    name = "A"
    port = 8000 
if identity == "B": # Default Bob to Central datacenter
    name = "B"
    port = 8001 

clock = 0 # This clock will keep track of what is going on

s = socket.socket()
s.connect(('127.0.0.1', port)) #Port 8000 is datacenter 1, Port 8001 is datacenter 2, Port 8002 is datacenter 3  

while True: 
    s.send(name.encode()) # Inform server of identity
    srv_id = int(s.recv(1024).decode()) # Find out server identity
    # Alice logic
    if name == "A":
        while True: 
            command = input("What would you like to send?\n")
            if command == "lost": # Write "lost" to DC1
                clock += 1
                data = pickle.dumps(["W_LOST", srv_id, clock]) # Message being sent, [datacenter ID, timestamp]
                s.send(data)
            if command == "found": # Write "found" to DC1
                # Read first to check if DC1 has lost
                clock += 1 
                data = pickle.dumps(["W_FOUND", srv_id, clock]) # Message being sent, [datacenter ID, timestamp]
                s.send(data)
            if command == "wait": # Wait for t seconds and adjust clock accordingly
                t = int(input("How many seconds would you like to wait?\n"))
                time.sleep(t) 
                clock += t
                print("The time is now " + str(clock) + " seconds.")       
    # Bob logic
    if name == "B":
        while True: 
            command = input("What would you like to do?\n")
            if command == "glad": # Write "glad" to DC2
                # Read first to check if DC2 has found
                data = pickle.dumps(["W_GLAD", srv_id, clock]) # Message being sent, [datacenter ID, timestamp]
                s.send(data)
            if command == "wait": # Wait for t seconds and adjust clock accordingly
                t = int(input("How many seconds would you like to wait?\n"))
                time.sleep(t) 
                clock += t        

