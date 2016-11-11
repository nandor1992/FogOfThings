# file: rfcomm-server.py
# auth: Albert Huang <albert@csail.mit.edu>
# desc: simple demonstration of a server application that uses RFCOMM sockets
#
# $Id: rfcomm-server.py 518 2007-08-10 07:20:07Z albert $

import bluetooth

server_sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM )
server_sock.bind(("",bluetooth.PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]
print server_sock.getsockname()

uuid = "00001800-0000-1000-8000-00805f9b34fb"

bluetooth.advertise_service(server_sock, "Sample_Server",
                  service_id=uuid
                  ,service_classes=[ uuid , bluetooth.SERIAL_PORT_CLASS ]
                  ,profiles=[ bluetooth.SERIAL_PORT_PROFILE ]
                   )
print("Waiting for connection on RFCOMM channel %d" % port)

client_sock, client_info = server_sock.accept()
print("Accepted connection from ", client_info,client_sock)

try:
    while True:
        data = client_sock.recv(1024)
        if len(data) == 0: break
        print("received [%s]" % data)
except IOError:
    pass

print("disconnected")

client_sock.close()
server_sock.close()
print("all done")
