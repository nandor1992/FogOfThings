#!/usr/bin/env python

#
# Example using Dynamic Payloads
# 
#  This is an example of how to use payloads of a varying (dynamic) size.
# 

# Modified to work from FogOf Thinggs and with Ini Fie
# To-Do: Modify Driver to work with CouchDB not sqlLite


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
import database
import ConfigParser
#Config Settings
Config=ConfigParser.ConfigParser()
Config.read(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))+"/config.ini")

message="";
exitFlag = 0
port=1
##########################################
#Threading These stuff
##########################################

f=open(Config.get("Log","location")+'/rf_blue.log','a')
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
        updateDevTime(dev_id,"Available")
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
    print ("Json Parts!")
    type_d=my_json.get("bn",{})[0][13:]
    mac_d=my_json.get("bn",{})[1][12:]
    ver_d=my_json.get("ver")
    value=datab.lookupDev(mac_d,type_d,ver_d)
    if value!=None:
        print("Found details "+value)
        rand_uuid=value
        updateDevTime(value,"Available")
        dev_list.append(value)
    else:
        print("No details found")
        rand_uuid = ''.join([random.choice(string.ascii_letters+string.digits) for n in xrange(8)])
        sense=[]
        for sens in my_json["e"]:
            sense.append({sens["n"]:sens["u"]})
        datab.addDevice(rand_uuid,type_d,mac_d,ver_d,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'Available',sense)
        dev_list.append(rand_uuid)
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
        updateDevTime(dev,"Max Retransmit")
    sys.stdout.flush()
    
def updateDev(dev_id,status):
    #ToDo update Date of Device
    datab.updateStat(dev_id,status)

def updateDevTime(dev_id,status):
    #ToDo update Date of Device
    datab.updateDateStat(dev_id,status,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
def scan():
    print("Scanning timeout")
    global port,send_q,receive_q,threads
    nearby_devices=bluetooth.discover_devices(lookup_names=True)
    print("found %d devices" %len(nearby_devices))
    for addr,name in nearby_devices:
        print(" %s - %s "% (addr,name))
        if name in find_devs:
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
        mainTimer=Timer(1200,scan)
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

gw_name=Config.get("Bluetooth","name")
dev_list= []
timer_list = {}
find_devs = []
print("Bluetooth Radio started: "+time.strftime('%X %x %Z'))

#Create sql stuff and initialize
find_devs=Config.get("Bluetooth","peers").split(',')
#Get Database deviecs
datab=database.Database(Config.get("couchDB","user"),Config.get("couchDB","pass"),'blue',Config.get("General","Gateway_Name"))
value=datab.getAllDevs()
for r in value:
    datab.updateStat(r,"Idle")
sys.stdout.flush()


#Queueu stuff
send_q = {}
receive_q = {}
threads = {}
dev_mac = {}

        
#Blue Start
nearby_devices=bluetooth.discover_devices(lookup_names=True)
print("found %d devices" %len(nearby_devices))
for addr,name in nearby_devices:
    print("Dev: %s - %s "% (addr,name))
    if name in find_devs:
        try:
            socket=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            socket.connect((addr,port))
            print('Connected to %s on port %s'%(name,port))
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

credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
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


mainTimer=Timer(1200,scan)
timer_list["main"]=mainTimer
mainTimer.start()

# forever loop
sys.stdout.flush()
try:
    while True:
        for key in receive_q:
            if not receive_q[key].empty():
                message=receive_q[key].get()
                handle_data(key,message)
        frame,header,body=channel.basic_get(queue=Config.get("Bluetooth","queue"),no_ack=False)
        if frame:
            channel.basic_ack(frame.delivery_tag)
            sendMssgResolv(body,header)
except KeyboardInterrupt,IOError:
    print ("Keyboard baby")
    shutdown()
    server_sock.close()
    print ("Exiting Main Thread")
    sys.stdout.flush()
