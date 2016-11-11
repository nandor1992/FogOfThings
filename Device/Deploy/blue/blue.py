import bluetooth,subprocess

nearby_devices=bluetooth.discover_devices(lookup_names=True)
print("found %d devices" %len(nearby_devices))

addr1=""

for addr,name in nearby_devices:
    print(" %s - %s "% (addr,name))
    if name=="NAN-BLU":
        addr1=addr
        
passkey="1234"
port = 1

print(addr1)
if addr1!="":
    socket=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    socket.connect((addr1,port))
    print('Connected')
    socket.send('x')
    socket.send("Hello World!")
    try:
        while True:
            data=socket.recv(1)
            print('%s-'%data)
    except IOError:
        pass
    socket.close()
