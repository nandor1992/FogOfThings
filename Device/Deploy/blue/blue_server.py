# file: rfcomm-server.py
# auth: Albert Huang <albert@csail.mit.edu>
# desc: simple demonstration of a server application that uses RFCOMM sockets
#
# $Id: rfcomm-server.py 518 2007-08-10 07:20:07Z albert $

from bluetooth import *

server_sock=BluetoothSocket(RFCOMM )
server_sock.bind(("",1))
server_sock.listen(1)

port = server_sock.getsockname()[1]

uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

#advertise_service(server_sock, "Sample_Server",
#                  service_id=uuid
#                  ,service_classes=[ uuid , SERIAL_PORT_CLASS ]
#                  ,profiles=[ SERIAL_PORT_PROFILE ]
#                   )
print("Waiting for connection on RFCOMM channel %d" % port)

socket, client_info = server_sock.accept()
print("Accepted connection from ", client_info)
print(client_info[0])
message="";
try:
    while True:
        try:
            reading=socket.recv(1024)
	    print (reading)
            if ((len(reading)>0 and reading[0]!=' ')):
                message=message+reading;
                if message[-1]=='\n' and message[-2]=='}':
                    print(message)
                    message="";
                elif message[-1]=='x':
                    print("Received Start Message [x]")
                    message="";
                    socket.send("{'e':[{'n':'name','u':'Rand'}],'bn':['urn:dev:type:RaspiBlue','urn:dev:mac:123raspimac','trans:id:492'],'ver':'1'}\n")    
            if (len(message)>250):
                print ("Long Message Error")
                print (len(message))
                message=""
        except BluetoothError:
            pass
except KeyboardInterrupt,IOError:
    print ("Keyboard baby")
    socket.close()
    server_sock.close()
    print("all done")
