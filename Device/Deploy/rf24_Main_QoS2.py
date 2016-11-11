#!/usr/bin/env python

#
# Example using Dynamic Payloads
# 
#  This is an example of how to use payloads of a varying (dynamic) size.
# 

from __future__ import print_function
import time
from RF24 import *
import RPi.GPIO as GPIO
import pika
import sqlite3
import json
import datetime
import string
import random

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
irq_gpio_pin = 25
message="";

##########################################
def try_read_data(channel=0):
    global message;
    if radio.available():
        while radio.available():
            length = radio.getDynamicPayloadSize()
            payload = radio.read(length).decode()
            payload = payload[:31]
            message=message+payload.strip()
            if (len(message)>300):
                print("length error")
                message=""
            if (message[-1]=='}' and message[0:1]=='{'):
                print("--------Message Received on CH=1-------")
                handle_data(message)
                message=""
            #print('Got payload size={} value="{}"'.format(len, receive_payload.decode('utf-8')))

def sendRf(message):
    radio.stopListening()
    radio.write(message[:31].encode())
    while len(message)>31:
        message=message[31:]
        radio.write(message[:31].encode())
    radio.startListening()

              

def handle_data(data):
    data=data.replace("'",'"')
    print(data)
    try:
        my_json=json.loads(data);
        print(json.dumps(my_json,indent=4,sort_keys=True))
    #Check if available in database if yes give it old id of not new one
    #and save to db when given, parse messages to see data as well
        if len(my_json["bn"][1])>=3:
            print("Register data received")
            registerResolv(my_json)
        else:
            print("Normal data received")
            messageResolv(my_json)
    except ValueError:
        print("Value Erro, probs something stupid happened")
    except IndexError:
        print("Index Error, probs something stupid happened")

def messageResolv(my_json):
    conn = sqlite3.connect(path)
    c=conn.cursor()
    dev_id=my_json.get("bn")[11:]
    dev_id=dev_id[:8]
    print(dev_id)
    c.execute("SELECT type FROM devices WHERE dev_id='"+dev_id+"'")
    value=c.fetchone()
    if value:
        c.execute("SELECT * FROM devices WHERE type='"+value[0]+"' ORDER BY dev_id")
        count=0
        while (c.fetchone()[0]!=dev_id):
            count+=1
        print("Found details of: "+value[0]+", updating Date ")
        c.execute("UPDATE devices SET last_update='"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"' WHERE dev_id='"+dev_id+"'")
        conn.commit()
        #Sending data to amqp que
        message_amqp=json.dumps(my_json["e"])
	message_amqp=message_amqp.replace('"',"'")
        print(message_amqp)
        properties_m=pika.BasicProperties(headers={'device':""+dev_id,'dev_number':str(count),'dev_type':""+value[0],'comm': ""+gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        channel.basic_publish(exchange='device', routing_key='', body=message_amqp, properties=properties_m)
    else:
        print("No details found - not forwarding")
    conn.close()

def registerResolv(my_json):
    trans=my_json.get("bn",{})[2]
    my_uuid=resolv_dev(my_json)
    trans=trans[9:]
    data="{'bn':['trans:id:"+trans+"','urn:dev:id:"+my_uuid+"']}"
    sendRf(data);

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
    else:
        print("No details found")
        rand_uuid = ''.join([random.choice(string.ascii_letters+string.digits) for n in xrange(8)])
        c.execute("INSERT INTO devices VALUES ('"+rand_uuid+"','"+type_d+"','"+mac_d+"','"+ver_d+"','"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"')")
        for sens in my_json["e"]:
           c.execute("INSERT INTO sensors VALUES ('"+rand_uuid+"','"+sens["n"]+"','"+sens["u"]+"')")
        conn.commit()
    conn.close()
    return rand_uuid

    
def sendMssgResolv(data,header):
    print("---------Send Data---------")
    print(data)
    dev_id=header.headers.get('device')
    print(dev_id)
    conn = sqlite3.connect(path)
    c=conn.cursor()
    dev_type=header.headers.get('dev_type')
    dev_nr=header.headers.get('dev_number')
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
        print("Received Something stupid on AMQP")
    #Check if available in database if yes give it old id of not new one
    #and save to db when given, parse messages to see data as well
    value=c.fetchone()
    if value:
        print("Found details, updating Date "+value[0])
        c.execute("UPDATE devices SET last_update='"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"' WHERE dev_id='"+value[0]+"'")
        conn.commit()
        send_json="{'e':["+data+"],'bn':'urn:dev:id:"+value[0]+"'}"
        send_json=send_json.replace(" ","_")
        print(send_json)
        try:
            my_json=json.loads(send_json.replace("'",'"'));
            print(json.dumps(my_json,indent=4,sort_keys=True))
            #Send to device
            sendRf(send_json)
        except ValueError:
            print("Bad: correct partial data probably")
    else:
        print("Data received for non existent Dev")
    conn.close()

def callback(ch,method,properties,body):
    print("[x] Received %r"%body)
    sendMssgResolv(body,properties) 
    
pipes = ['1Node','2Node','3Node','4Node']
gw_name="Gateway-RF24"


print('Receive Example')
radio.begin()
radio.enableDynamicPayloads()
radio.setRetries(5,15)

if irq_gpio_pin is not None:
        # set up callback for irq pin
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(irq_gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(irq_gpio_pin, GPIO.FALLING, callback=try_read_data)

    radio.openWritingPipe(pipes[0])
    radio.openReadingPipe(1,pipes[1])
    radio.startListening()

#AMQP Stuff

credentials = pika.PlainCredentials('admin', 'hunter')
parameters = pika.ConnectionParameters('localhost',5672,'test', credentials)
connection = pika.BlockingConnection(parameters);

channel = connection.channel()
channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,queue='ardu_rf24',no_ack=True)

#Create sql stuff and initialize
path ='/home/pi/databases/ardurf24.db'

# forever loop
try:
    channel.start_consuming()     
except KeyboardInterrupt:
    print ("Keyboard baby")
    radio.stopListening()
    connection.close()
    print ("Exiting Main Thread")

