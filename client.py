# ************************************************
# Authors: Steve Sanchez
# Course: CPSC 471
# Due date: 11/26/17
# This program simulates a file transfer protocol. The client reads in 
# commands from the user that are sent to the server via the initial 
# control connection. When transferring files over, the client establishes 
# a new connection, the data connection, to retrieve some response from 
# the server.
# ************************************************

import socket
import os
import sys
import argparse
import time


# Print usage if user has incorrect number of arguments given and exit
if len(sys.argv) < 3:
    print("ERROR! Invalid # of arguments given. See sample input below:")
    print("python client.py" + " <server domain name> " + "<server port>")
    sys.exit(1)

# Store the arguments in variables
serv_name = sys.argv[1]
serv_port =int(sys.argv[2])

# Get and store the IP address of the domain name
serv_IP = socket.gethostbyname(serv_name)

# Connect to server
ctrl_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ctrl_channel.connect((serv_IP, serv_port))


# ************************************************
# Sends the specified data over the specified socket
# @param args - the data being sent
# @param conn_channel - the socket from which to send
# *************************************************
def sendData(args, conn_channel):
    # Get the size of the data read and convert it to string
    data_size_str = str(len(args))
    
    # Prepend 0's to the size string until the size is 10 bytes
    while len(data_size_str) < 10:
         data_size_str = "0" + data_size_str
         
    # Prepend the data size to the data being sent
    args = data_size_str + args

    # Keep track of the number of bytes sent
    num_sent = 0
    
    # Send the data
    while len(args) > num_sent:
        num_sent += conn_channel.send(args[num_sent:])
        

# ************************************************
# Receives the specified number of bytes from the specified socket
# @param sock - the socket from which to receive
# @param num_bytes - the number of bytes to receive
# @return - the bytes received
# *************************************************
def recvAll(sock, num_bytes):

	# Create a buffer and temp buffer
	recv_buff = ""
	tmp_buff = ""
	
	# Keep receiving until all is received
	while len(recv_buff) < num_bytes:
		
		# Attempt to receive bytes
		tmp_buff =  sock.recv(num_bytes)
		
		# The other side has closed the socket
		if not tmp_buff:
			break
		
		# Add the received bytes to the buffer
		recv_buff += tmp_buff
	
	return recv_buff

# ************************************************
# Recieves the file data from the socket
# @param sock - the socket from which to receive
# @return - the data received
# *************************************************
def receiveData(sock):
	# The buffer to all data received from the the server
	file_data = ""
	
	# The temporary buffer to store the received data
	recv_buff = ""
	
	# The size of the incoming file
	file_size = 0	
	
	# The buffer containing the file size
	file_size_buff = ""
	
	# Receive the first 10 bytes indicating the size of the file
	file_size_buff = recvAll(sock, 10)
	
	# Get the file size
	file_size = int(file_size_buff)
	
	# Get the file data
	file_data = recvAll(sock, file_size)

	return file_data
 

while True:
    # Get input from the user
    line = raw_input("ftp> ")
    print(line)

    # Split the input into the command + arguments(if any)
    client_args = line.split()
    
    # First check if ls,get,or put commands to generate an ephemeral port for transfer 
    if (client_args[0] == 'ls' or client_args[0] == 'get' or client_args[0] == 'put'):
        # Create a socket used for data transfer
        data_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to port 0 and listen for response
        data_channel.bind(('',0))

        # Send command and port over control channel
        sendData(client_args[0], ctrl_channel)
        sendData(str(data_channel.getsockname()[1]), ctrl_channel)
        
	# Listen for a connection
        data_channel.listen(1)
        while True:
            print("Awaiting server connection...")
            data_sock, data_addr = data_channel.accept()
            
            print("Accepted connection from server:", data_sock)

            # Send additional argument for get or put commands over contrl channel
            if (len(client_args) > 1):
                sendData(client_args[1], ctrl_channel)

                # If the client asked to get file, receive and write a new file with its contents
                if (client_args[0] == 'get'):
                    contents = receiveData(data_sock)
                    
                    # If contents is a failure message, just print
                    if (contents == "FAILURE. File does not exist on server."):
                         print(contents)
                         break

                    # Otherwise, write contents to a file
                    else:
                        file_recv = open('client_' + client_args[1], 'w+')
                        file_recv.write(contents)

                    # Close the file
                    file_recv.close()

                    # Print the name of the file received and size of data sent
                    # Added 10 to the size due to the header attached to data containing file size
                    print("Received " + client_args[1] + " of " + str(len(contents)+10) + " bytes.")

                # If the client asked to put a file, send file to server
                elif (client_args[0] == 'put'):
                    
                    # Check if file is valid / on the client directory
                    if (os.path.isfile('./' + client_args[1]) == True):
                        # Read in the file
                        file_obj = open(client_args[1], "r")
                        file_data = file_obj.read()

                        # If data is valid, send data server via control channel
                        if file_data:
                            sendData(file_data, ctrl_channel)

                        # Close the file
                        file_obj.close()

                        # Print the name of the file sent and size of data sent
                        # Added 10 to the size due to the header attached to data containing file size
                        print("Sent " + client_args[1] + " of " + str(len(file_data)+10) + " bytes.")

                        # Receive message from server via data channel
                        reply = receiveData(data_sock)
                        
                    # Otherwise file does not exist on client so print error
                    else:
                        # Send indicator of failure to server so it can do other commands
                        file_data = "FAILURE. File does not exist on client"
                        sendData(file_data, ctrl_channel)
                        print(file_data)

                # Otherwise client gave extra argument to ls command so print error
                else:
                    print("FAILURE. Gave ls command an extra argument. Discarding...")
                    
                    # Still print the ls being sent
                    ls_result = receiveData(data_sock)
                    print("Sent ls command of " + str(len(client_args[0])+10) + " bytes.")
                    print(ls_result)
                    
            else:
                # Receive command results
                ls_result = receiveData(data_sock)
                print("Sent ls command of " + str(len(client_args[0])+10) + " bytes.")
                print(ls_result)

            # Prepare to close data connection
            break
            
        data_channel.close()
        
    else:
        # Send commands over control channel
        sendData(client_args[0], ctrl_channel)

        # If command is quit, prepare to close connection
        if (client_args[0] == 'quit'):
            print("Sent quit command of " + str(len(client_args[0])+10) + " bytes.")
            # Prepare to close connection
            break

# End client
ctrl_channel.close()

