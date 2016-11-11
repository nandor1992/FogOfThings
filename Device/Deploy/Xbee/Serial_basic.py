import time
import serial
import sys
from select import select
# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
    port='/dev/ttyUSB1',
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=None, xonxoff=0, rtscts=0
)

ser.isOpen()

print 'Enter your commands below.\r\nInsert "exit" to leave the application.'

input=1
while 1 :
    out = ''
    # let's wait one second before reading output (let's give device time to answer)
    time.sleep(1)
    while ser.inWaiting() > 0:
        out += ser.read(1)
    if out != '':
        print ">>" + out
    rlist, _, _ =select([sys.stdin],[],[],0.1)
    if rlist:
        input=sys.stdin.readline()                        
#input = raw_input(">> ")
        if input == 'exit':
            ser.close()
            exit()
        else:
            ser.write(input)
