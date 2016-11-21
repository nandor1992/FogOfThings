#!/usr/bin/python

import Queue
import threading
import time
import serial
import json
import sqlite3
import random
import string
import datetime
import pika
import os,sys
import ConfigParser
#Config Settings
Config=ConfigParser.ConfigParser()
Config.read(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))+"/config.ini")
exitFlag = 0        
    
class UARTThread(threading.Thread):
    def __init__(self,ser,send_q,receive_q):
        threading.Thread.__init__(self)
        self.ser = ser
        self.send_q = send_q
        self.receive_q=receive_q
    def run(self):
        print "Starting Serial stuff"
        transLoop(self.ser, self.send_q, self.receive_q)
        print "Exiting Serial stuff"

def transLoop(ser,send_q,receive_q):
    message="";
    while not exitFlag:
        if not send_q.empty():
            data = send_q.get()
            print "Sending: " +data
            ser.write(data)
        try:
            reading='';
            while ser.inWaiting() > 0:
                reading += ser.read(1)
            if (len(reading)>0):
                message=message+reading;
                if message[-1]=='\n':
                    if (len(message)>250):
                        print "Long Message Error"
                        print len(message)
                        message=""
                    else:
                        receive_q.put(message[:-1])
                        message=""
            else:
                message=message+reading;
        except UnicodeDecodeError:
            print "--------------------"
            print "Unicode Decode Error"
            print "--------------------"


def handle_data(data):
    print("---------Received Data---------")
    print data
    data=data[:-1]
    data=data.replace("'",'"')
    try:
        my_json=json.loads(data);
        print json.dumps(my_json,indent=4,sort_keys=True)
    #Check if available in database if yes give it old id of not new one
    #and save to db when given, parse messages to see data as well
        if len(my_json["bn"][1])>2:
            print "Register data received"
            registerResolv(my_json)
        else:
            print "Normal data received"
            messageResolv(my_json)
    except ValueError:
        print "Value Erro, probs something stupid happened"

def messageResolv(my_json):
    dev_id=my_json.get("bn")[11:]
    dev_id=dev_id[:8]
    print dev_id
    c.execute("SELECT type FROM devices WHERE dev_id='"+dev_id+"'")
    value=c.fetchone()
    if value:
        c.execute("SELECT * FROM devices WHERE type='"+value[0]+"' ORDER BY dev_id")
        count=0
        while (c.fetchone()[0]!=dev_id):
            count+=1
        print "Found details of: "+value[0]+", updating Date "
        c.execute("UPDATE devices SET last_update='"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"' WHERE dev_id='"+dev_id+"'")
        conn.commit()
        #Sending data to amqp que
        message_amqp=json.dumps(my_json["e"])
        print message_amqp
        properties_m=pika.BasicProperties(headers={'device':""+dev_id,'number':count,'type':""+value[0],'comm': ""+gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        channel.basic_publish(exchange='device', routing_key='', body=message_amqp, properties=properties_m)
    else:
        print "No details found - not forwarding"
    
def registerResolv(my_json):
    trans=my_json.get("bn",{})[2]
    my_uuid=resolv_dev(my_json)
    trans=trans[9:]
    send_q.put("{'bn':['trans:id:"+trans+"','urn:dev:id:"+my_uuid+"']}\n");
    
def resolv_dev(my_json):
    print "Json Parts!"
    type_d=my_json.get("bn",{})[0][13:]
    mac_d=my_json.get("bn",{})[1][12:]
    ver_d=my_json.get("ver")
    c.execute("SELECT dev_id FROM devices WHERE mac='"+mac_d+"' AND type='"+type_d+"' AND ver='"+ver_d+"'")
    value=c.fetchone()
    if value:
        print "Found details "+value[0]
        rand_uuid=value[0]
    else:
        print "No details found"
        rand_uuid = ''.join([random.choice(string.ascii_letters+string.digits) for n in xrange(8)])
        c.execute("INSERT INTO devices VALUES ('"+rand_uuid+"','"+type_d+"','"+mac_d+"','"+ver_d+"','"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"')")
        for sens in my_json["e"]:
           c.execute("INSERT INTO sensors VALUES ('"+rand_uuid+"','"+sens["n"]+"','"+sens["u"]+"')")
        conn.commit()
    return rand_uuid
    
def sendMssgResolv(data,header):
    print("---------Send Data---------")
    print data
    dev_id=header.headers.get('device')
    dev_type=header.headers.get('type')
    dev_nr=header.headers.get('number')
    try:
        if (dev_id):
            c.execute("SELECT dev_id FROM devices WHERE dev_id='"+dev_id+"'")
        else:
            if (dev_type):
                print("working data")
                if (dev_nr):
                    print("we have number")
                    c.execute("SELECT dev_id FROM devices  WHERE type='"+dev_type+"' ORDER BY dev_id  LIMIT 1 OFFSET "+dev_nr)
                else:
                    c.execute("SELECT dev_id FROM devices WHERE type='"+dev_type+"'")
    except ValueError:
        print "Received Something stupid on AMQP"
    #Check if available in database if yes give it old id of not new one
    #and save to db when given, parse messages to see data as well
    value=c.fetchone()
    if value:
        print "Found details, updating Date "+value[0]
        c.execute("UPDATE devices SET last_update='"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"' WHERE dev_id='"+value[0]+"'")
        conn.commit()
        send_json="{'e':["+data+"],'bn':'urn:dev:id:"+value[0]+"'}\n"
        print(send_json)
        my_json=json.loads(send_json.replace("'",'"'));
        print(json.dumps(my_json,indent=4,sort_keys=True))
        #Send to device
        send_q.put(send_json+"\n");
    else:
        print "Data received for non existent Dev"


def gratiousExit():
    print "Error: Gracious Exit"
    exitFlag=1
    for t in threads:
        t.join()
    print "Exiting Main Thread"
    exit(1)

def shutdown():
    exitFlag=1
    for t in threads:
        t.join()
    ser.close()
    conn.close()
    connection.close()
    print "Exiting Func"

#Ques for transmission of data started
send_q = Queue.Queue(10)
receive_q = Queue.Queue(10)
threads = []
try:
    ser = serial.Serial(
        port=Config.get("Xbee","port"),
        baudrate=int(Config.get("Xbee","baud")),
        bytesize=int(Config.get("Xbee","bytesize")),
        parity=Config.get("Xbee","parity"),
        stopbits=int(Config.get("Xbee","stopbits")),
        timeout=None, xonxoff=0, rtscts=0
    )
    ser.isOpen()
except serial.SerialException:
    print "Serial Expression probs wrong port"
    gratiousExit()

#Create sql stuff and initialize
path =Config.get("Database","path")+'/zigbeedb.db'
conn = sqlite3.connect(path)
c=conn.cursor()

#amqp connn
credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
connection = pika.BlockingConnection(parameters);

channel = connection.channel()
channel.basic_qos(prefetch_count=1)
        
gw_name=Config.get("Xbee","name")
# Create new threads
uart=UARTThread(ser,send_q,receive_q)
uart.start()
threads.append(uart)

# Wait for queue to empty
try:
    while True:
        if not receive_q.empty():
            message=receive_q.get()
            handle_data(message)
        frame,header,body=channel.basic_get(queue=Config.get("Xbee","queue"),no_ack=False)
        if frame:
            channel.basic_ack(frame.delivery_tag)
            sendMssgResolv(body,header)
            
except KeyboardInterrupt:
    print "Keyboard baby"
    exitFlag=1
    for t in threads:
        t.join()
    ser.close()
    conn.close()
    connection.close()
    print "Exiting Main Thread"
