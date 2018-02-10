# ************************************************
# Authors: Steve Sanchez
# Course: CPSC 471
# Due date: 11/26/17
# This program simulates a file transfer protocol.The server waits for
# a client to connect and waits to receive commands via the control 
# connection. When a command has been received, the server connects to 
# the client's ephemeral port to send an appropriate response.
# ************************************************

import socket
import os
import sys
import subprocess
import time

# Print usage if user has incorrect number of arguments given and exit
if len(sys.argv) < 1:
    print("ERROR! Invalid # of arguments given. See sample input below:")
    print("python client.py" +  "<port number>")
    sys.exit(1)
    
# Port for control channel
ctrl_port = int(sys.argv[1])

# Bind and listen to port
ctrl_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ctrl_channel.bind(('', ctrl_port))
ctrl_channel.listen(1)

print("Awaiting connections...")

# Accept commands at this connection
command_sock, command_addr = ctrl_channel.accept()

print("Accepted connection from client: ", command_addr)


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


while True:
    # Receive command from client
    command = receiveData(command_sock)
    print("command is", command)
    
    # If command is ls, get, or put, then connect to ephemeral port for data transfer
    if (command == 'ls' or command == 'get' or command == 'put'):
        data_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = receiveData(command_sock)
        data_channel.connect((command_addr[0],int(port)))

        # If the command is get, send file requested to the client
        if (command == 'get'):
            file_name = receiveData(command_sock)

            # Check if file is valid / on the server directory
            if (os.path.isfile('./' + file_name) == True):
                # Read in the file
                file_obj = open(file_name, "r")
                file_data = file_obj.read()
                
                # If data is valid, send it to client
                if file_data:
                    sendData(file_data, data_channel)
                    
                # Close the file
                file_obj.close()
		print("SUCCESS. File has been sent to client.")

            # Otherwise file is invalid so send failure message to client
            else:
                msg = "FAILURE. File does not exist on server."
		print(msg)
                sendData(msg, data_channel)
            
        # Else if the command is put, retrieve the file from the client and store
        elif(command == 'put'):
            # Receive file name and contents from client
            file_name = receiveData(command_sock)
            contents = receiveData(command_sock)

            # If contents is a failure indicator, print failure
            if (contents == "FAILURE. File does not exist on client"):
                print(contents)

            # Otherwise, store the file on server
            else:
                # Open/Create and write to the the file
                file_recv = open('serv_' + file_name, "w+")
                file_recv.write(contents)

                # Send success message to client
                msg = "SUCCESS. File has been stored on server."
                print(msg)
                sendData(msg, data_channel)
                        
                # Close the file
                file_recv.close()
            
        # Else the command is ls so display items in directory
        else:
            # Run ls-equivalent command for Windows
            if os.name == 'nt':
                ls_result = subprocess.check_output('dir', shell=True) 

            # Else run ls -l for Linux
            elif os.name == 'posix':
                ls_result = subprocess.check_output(['ls', '-l'], shell=True)

            # Send ls results back to client
            sendData(str(ls_result), data_channel)
            print("SUCCESS. File list has been sent to client.")

        # Close the data channel connection
        data_channel.close()
        
    # Else if the command is quit, prepare to close connection
    elif (command == 'quit'):
        # Close server side of connection
        command_sock.close()
        print("SUCCESS. Server connection closing...")
        break
    
    # Else the command is not recognized so print error message
    else:
        print("FAILURE. Invalid input given.")
          
# End server
ctrl_channel.close()
