import socket 
import os
import pickle
import time

identity = input("Are you Alice (A) or Bob (B)?")
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
    srv_id = s.recv(1024).decode() # Find out server identity
    # Alice logic
    if name == "A":
        while True: 
            command = input("What would you like to send?")
                if command == "lost": # Write "lost" to DC1
                    data = pickle.dumps(["W_LOST", [srv_id, clock]]) # Message being sent, [datacenter ID, timestamp]
                    s.send(data)
                if command == "found": # Write "found" to DC1
                    # Read first to check if DC1 has lost 
                    data = pickle.dumps(["W_FOUND", [srv_id, clock]]) # Message being sent, [datacenter ID, timestamp]
                    s.send(data)
                if command == "wait": # Wait for t seconds and adjust clock accordingly
                    t = int(input("How many seconds would you like to wait?"))
                    time.sleep(t) 
                    clock += t       
    # Bob logic
    if name == "B":
        while True: 
            command = input("What would you like to do?")
                
                if command == "glad": # Write "found" to DC1
                    # Read first to check if DC2 has found
                    data = pickle.dumps(["W_GLAD", [srv_id, clock]]) # Message being sent, [datacenter ID, timestamp]
                    s.send(data)
                if command == "wait": # Wait for t seconds and adjust clock accordingly
                    t = int(input("How many seconds would you like to wait?"))
                    time.sleep(t) 
                    clock += t        

#Alice: I've lost my wedding ring."  "Bob: I'm glad to hear that."
