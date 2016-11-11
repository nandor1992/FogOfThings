#!/usr/bin/env python

#
# Example using Dynamic Payloads
# 
#  This is an example of how to use payloads of a varying (dynamic) size.
# 

from __future__ import print_function
from threading import Timer
import time
from RF24 import *
import RPi.GPIO as GPIO
import pika
import sqlite3
import json
import datetime
import string
import random
import bluetooth
import Queue
import threading
import os,sys

irq_gpio_pin = None
########### USER CONFIGURATION ###########
# See https://github.com/TMRh20/RF24/blob/master/RPi/pyRF24/readme.md

# CE Pin, CSN Pin, SPI Speed

# Setup for GPIO 22 CE and CE0 CSN with SPI Speed @ 8Mhz
radio = RF24(RPI_V2_GPIO_P1_15, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ)

#RPi B
# Setup for GPIO 15 CE and CE1 CSN with SPI Speed @ 8Mhz
#radio = RF24(RPI_V2_GPIO_P1_15, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ)

#RPi B+
# Setup for GPIO 22 CE and CE0 CSN for RPi B+ with SPI Speed @ 8Mhz
#radio = RF24(RPI_BPLUS_GPIO_J8_15, RPI_BPLUS_GPIO_J8_24, BCM2835_SPI_SPEED_8MHZ)

# RPi Alternate, with SPIDEV - Note: Edit RF24/arch/BBB/spi.cpp and  set 'this->device = "/dev/spidev0.0";;' or as listed in /dev
#radio = RF24(22, 0);


# Setup for connected IRQ pin, GPIO 24 on RPi B+; uncomment to activate
#irq_gpio_pin = RPI_BPLUS_GPIO_J8_18
message="";
exitFlag = 0
port=1
##########################################
#Threading These stuff
##########################################

f=open('/home/pi/log/rf_blue.log','a')
sys.stdout=f

class BlueThread(threading.Thread):
    def __init__(self,name,socket,send_q,receive_q):
        threading.Thread.__init__(self)
        self.name=name
        self.socket = socket
        self.send_q = send_q
        self.receive_q=receive_q
    def run(self):
        print ("Starting Blue Stuff for " + self.name)
        transLoop(self.socket, self.send_q, self.receive_q)
        print ("Exiting Blue Stuff for " + self.name)    
        sys.stdout.flush()
        
class ServerThread(threading.Thread):
    def __init__(self,server_sock):
        threading.Thread.__init__(self)
        self.server_sock=server_sock
    def run(self):
        print ("Started Server Thread")
        port = server_sock.getsockname()[1]
        print("Waiting for connection on RFCOMM channel %d" % port)
        server_sock.settimeout(2)
        while not exitFlag:
            try:
                client_socket, client_info = server_sock.accept()
                client_socket.send('x')
                addr=client_info[0]
                client_socket.settimeout(0.1)
                send_q[addr]=Queue.Queue(10)
                receive_q[addr]=Queue.Queue(10)
                bluet=BlueThread(addr,client_socket,send_q[addr],receive_q[addr])
                bluet.start()
                threads[addr]=bluet
            except bluetooth.BluetoothError :
                pass
        print("Exiting Server")
        sys.stdout.flush()            
            
            
        

def transLoop(socket,send_q,receive_q):
    message="";
    global exitFlag
    while not exitFlag:
        if not send_q.empty():
            data = send_q.get()
            print ("Sending: " +data)
            socket.send(data+'\n')
        try:
            reading=socket.recv(1024)
            if ((len(reading)>0 and reading[0]!=' ')):
                message=message+reading;
            if message[-1]=='\n' and message[-2]=='}':
                receive_q.put(message)
                message="";
            if (len(message)>250):
                print ("Long Message Error")
                print (len(message))
                message=""
        except bluetooth.BluetoothError as error:
            if error[0]!="timed out":
                print("Error:",error)
                break;
        sys.stdout.flush()
    socket.close()
    
##################
#Rest of the Stuff
##################
def try_read_data(payload):
    global message;
    message=message+payload
    if (len(message)>300):
        print("length error")
        message=""
    if (message[-1]=='\n' and message[0:1]=='{'):
        print("--------Message Received on CH=1-------")
        handle_data(message[:-1])
        message=""
            #print('Got payload size={} value="{}"'.format(len, receive_payload.decode('utf-8')))
    sys.stdout.flush()
              

def handle_data(key,data):
    print("--------Message Received from: "+key+"-------")
    data=data.replace("'",'"')
    try:
        my_json=json.loads(data);
    #Check if available in database if yes give it old id of not new one
    #and save to db when given, parse messages to see data as well
        if len(my_json["bn"][1])>=3:
            print("Register data received")
            registerResolv(key,my_json)
        else:
            print("Normal data received")
            messageResolv(my_json)
    except ValueError:
        print("Value Erro, probs something stupid happened")
    except IndexError:
        print("Index Error, probs something stupid happened")
    except KeyError:
        print("Key Error, probs something bad happened")
    sys.stdout.flush()
def messageResolv(my_json):
    conn = sqlite3.connect(path)
    c=conn.cursor()
    dev_id=my_json.get("bn")[11:]
    dev_id=dev_id[:8]
    print(dev_id)
    if (dev_list.count(dev_id)!=0):
        message_amqp=json.dumps(my_json["e"])
	message_amqp=message_amqp.replace('"',"'")
        print(message_amqp)
        if dev_id in timer_list:
            timer_list[dev_id].cancel()
        properties_m=pika.BasicProperties(headers={'device':""+dev_id,'comm': ""+gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        channel.basic_publish(exchange='device', routing_key='', body=message_amqp, properties=properties_m)
        conn = sqlite3.connect(path)
        c=conn.cursor()
        updateDevTime(c,conn,dev_id,"Available")
        conn.close()
    else:
        print("No details found - not forwarding")
    sys.stdout.flush()
    
def registerResolv(key,my_json):
    trans=my_json.get("bn",{})[2]
    my_uuid=resolv_dev(my_json)
    trans=trans[9:]
    data="{'bn':['trans:id:"+trans+"','urn:dev:id:"+my_uuid+"']}"
    dev_mac[my_uuid]=key
    sendRf(my_uuid,data);

    
def resolv_dev(my_json):
    conn = sqlite3.connect(path)
    c=conn.cursor()
    print ("Json Parts!")
    type_d=my_json.get("bn",{})[0][13:]
    mac_d=my_json.get("bn",{})[1][12:]
    ver_d=my_json.get("ver")
    c.execute("SELECT dev_id FROM devices WHERE mac='"+mac_d+"' AND type='"+type_d+"' AND ver='"+ver_d+"'")
    value=c.fetchone()
    if value:
        print("Found details "+value[0])
        rand_uuid=value[0]
        updateDevTime(c,conn,value[0],"Available")
        dev_list.append(value[0])
    else:
        print("No details found")
        rand_uuid = ''.join([random.choice(string.ascii_letters+string.digits) for n in xrange(8)])
        c.execute("INSERT INTO devices VALUES ('"+rand_uuid+"','"+type_d+"','"+mac_d+"','"+ver_d+"','"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"','Available')")
        for sens in my_json["e"]:
           c.execute("INSERT INTO sensors VALUES ('"+rand_uuid+"','"+sens["n"]+"','"+sens["u"]+"')")
        conn.commit()
        dev_list.append(rand_uuid)
    conn.close()
    sys.stdout.flush()
    return rand_uuid

    
def sendMssgResolv(data,header):
    print("---------Send Data---------")
    print(data)
    dev_id=header.headers.get('device')
    qos=str(header.headers.get('qos')).strip()
    print(dev_id)
    if (dev_list.count(dev_id)!=0):
        print("Found details")
        send_json="{'e':"+data+",'bn':'urn:dev:id:"+dev_id+"'}"
        send_json=send_json.replace(" ","_")
        print(send_json)
        #Start timer here
        if (qos!=None):
            if (qos=='1'):
                t=Timer(5,timeout,[dev_id,send_json,0])
                timer_list[dev_id]=t
                t.start()
        sendRf(dev_id,send_json)
    else:
        print("Data received for non existent Dev")
    sys.stdout.flush()
    
def callback(ch,method,properties,body):
    sendMssgResolv(body,properties) 

def sendRf(device,message):
    key=dev_mac[device]
    print(device+"-"+key)
    send_q[key].put(message)
    
def timeout(dev,val,cnt):
    print("Message Timed Out: ",cnt)
    if (cnt<5):
        sendRf(dev,val)
        t=Timer(5,timeout,[dev,val,cnt+1])
        t.start()
        timer_list[dev]=t
    else:
        print ("Max Retransmit Reached")
        message_amqp="Retransmit Error"
        properties_m=pika.BasicProperties(headers={'device':""+dev,'comm': ""+gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        channel.basic_publish(exchange='device', routing_key='', body=message_amqp, properties=properties_m)
        timer_list[dev].cancel()
        conn = sqlite3.connect(path)
        c=conn.cursor()
        updateDevTime(c,conn,dev,"Max Retransmit")
        conn.close()
    sys.stdout.flush()
    
def updateDev(c,conn,dev_id,status):
    #ToDo update Date of Device
    string="UPDATE devices SET status='"+status+"' WHERE dev_id='"+dev_id+"'"
    c.execute(string)
    conn.commit()

def updateDevTime(c,conn,dev_id,status):
    #ToDo update Date of Device
    string="UPDATE devices SET status='"+status+"', last_update='"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"' WHERE dev_id='"+dev_id+"'"
    c.execute(string)
    conn.commit()
    
    
def scan():
    print("Scanning timeout")
    global port,send_q,receive_q,threads
    nearby_devices=bluetooth.discover_devices(lookup_names=True)
    print("found %d devices" %len(nearby_devices))
    for addr,name in nearby_devices:
        print(" %s - %s "% (addr,name))
        if (name=="NAN-BLU" or name=="raspberrypi_client"):
            print("Attempting"+name+":"+addr+"port:"+str(port))
            try:
                socket=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                socket.connect((addr,port))
                print('Connected to %s on port %s'%(name,port))
#                port=port+1
		socket.send('x')
                socket.settimeout(0.1)
                send_q[addr]=Queue.Queue(10)
                receive_q[addr]=Queue.Queue(10)
                bluet=BlueThread(name,socket,send_q[addr],receive_q[addr])
                bluet.start()
                threads[addr]=bluet
            except bluetooth.BluetoothError as error:
                print (error)
    if not exitFlag:
        mainTimer=Timer(20,scan)
        timer_list["main"]=mainTimer
        mainTimer.start()
    sys.stdout.flush()
    
def shutdown():
    global exitFlag
    exitFlag=1
    channel.close()
    connection.close()
    timer_list["main"].cancel()
    for key in timer_list:
	timer_list[key].cancel()

gw_name="Gateway-Blue"
dev_list= []
timer_list = {}

print("Bluetooth Radio started: "+time.strftime('%X %x %Z'))


if irq_gpio_pin is not None:
    # set up callback for irq pin
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(irq_gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(irq_gpio_pin, GPIO.FALLING, callback=try_read_data)

    radio.openWritingPipe(pipes[0])
    radio.openReadingPipe(1,pipes[1])
    radio.startListening()

#Create sql stuff and initialize
path ='/home/pi/databases/ardu_blue.db'

#Get Database deviecs
conn = sqlite3.connect(path)
c2=conn.cursor()
c=conn.cursor()
c.execute("SELECT dev_id FROM devices")
value=c.fetchone()
while value:
    updateDev(c2,conn,value[0],"Idle")
    value=c.fetchone()
print("Working Deviecs")
print(dev_list)
conn.close()
sys.stdout.flush()
#QUeueu stuff
send_q = {}
receive_q = {}
threads = {}
dev_mac = {}

        
#Blue Start
nearby_devices=bluetooth.discover_devices(lookup_names=True)
print("found %d devices" %len(nearby_devices))
for addr,name in nearby_devices:
    print("Dev: %s - %s "% (addr,name))
    if (name=="NAN-BLU" or name=="raspberrypi_client"):
        try:
            socket=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            socket.connect((addr,port))
            print('Connected to %s on port %s'%(name,port))
#            port=port+1
            socket.send('x')
            socket.settimeout(0.1)
            send_q[addr]=Queue.Queue(10)
            receive_q[addr]=Queue.Queue(10)
            bluet=BlueThread(name,socket,send_q[addr],receive_q[addr])
            bluet.start()
            threads[addr]=bluet
        except bluetooth.BluetoothError as error:
            print(error)
#AMQP Stuff

credentials = pika.PlainCredentials('admin', 'hunter')
parameters = pika.ConnectionParameters('localhost',5672,'test', credentials)
connection = pika.BlockingConnection(parameters);

channel = connection.channel()
channel.basic_qos(prefetch_count=1)

#Server Socket 
server_sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM )
server_sock.bind(("",1))
server_sock.listen(1)
servT=ServerThread(server_sock)
servT.start()
threads["serv"]=servT


mainTimer=Timer(60,scan)
timer_list["main"]=mainTimer
mainTimer.start()

#Timer Stuff
#t=Timer(1,timeout,["OWaDMY9V","{'e':[{'n':'led','v':'1'}],'bn':'urn:dev:id:OWaDMY9V'}"])
#timer_list["OWaDMY9V"]=t
#t.start()
#time.sleep(5)
#timer_list["OWaDMY9V"].cancel()    
        
# forever loop
sys.stdout.flush()
try:
    while True:
        for key in receive_q:
            if not receive_q[key].empty():
                message=receive_q[key].get()
                handle_data(key,message)
        frame,header,body=channel.basic_get(queue='ardu_blue',no_ack=False)
        if frame:
            channel.basic_ack(frame.delivery_tag)
            sendMssgResolv(body,header)
except KeyboardInterrupt,IOError:
    print ("Keyboard baby")
    shutdown()
    server_sock.close()
    print ("Exiting Main Thread")
    sys.stdout.flush()
