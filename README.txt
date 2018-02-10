CPSC 471 - FTP Programming Assignment

This program demonstrates a basic FTP connection and was was developed using Python 3.6.

Usage:
---------------------------------------------
	Run the server.py first followed by client.py
	When the client successfully connects, the client can execute ls, quit, get <filename>, and put <filename> commands

	Any file the client puts on server will get a "serv_" prefix attached to it when stored on server
	Any file the client gets from server will get a "client_" prefix attached to it when stored on client
	
	Example commands:
		python server.py 2345
		python client.py localhost 2345
		
		After client connects:
			ls
			get test.txt
			put test.txt
			quit