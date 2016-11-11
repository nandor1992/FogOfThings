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
start=0;
##########################################
def try_read_data(channel=0):
    global start
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
                handle_data(message)
                message=""
            #print('Got payload size={} value="{}"'.format(len, receive_payload.decode('utf-8')))

def sendRf(message):
    global start
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
            registerResolv(my_json)
        else:
            messageResolv(my_json)
    except ValueError:
        print("Value Erro, probs something stupid happened")
    except IndexError:
        print("Index Error, probs something stupid happened")

def messageResolv(my_json):

    dev_id=my_json.get("bn")[11:]
    dev_id=dev_id[:8]
    message_amqp=json.dumps(my_json["e"])
    properties_m=pika.BasicProperties(headers={'device':""+dev_id,'dev_number':'0','dev_type':'ardUnoTemp','comm': ""+gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    channel.basic_publish(exchange='devices', routing_key='', body=message_amqp, properties=properties_m)

def registerResolv(my_json):
    trans=my_json.get("bn",{})[2]
    my_uuid=resolv_dev(my_json)
    trans=trans[9:]
    data="{'bn':['trans:id:"+trans+"','urn:dev:id:"+my_uuid+"']}"
    sendRf(data);

def resolv_dev(my_json):
    conn = sqlite3.connect(path)
    c=conn.cursor()
    type_d=my_json.get("bn",{})[0][13:]
    mac_d=my_json.get("bn",{})[1][12:]
    ver_d=my_json.get("ver")
    c.execute("SELECT dev_id FROM devices WHERE mac='"+mac_d+"' AND type='"+type_d+"' AND ver='"+ver_d+"'")
    value=c.fetchone()
    if value:
        rand_uuid=value[0]
    else:
        rand_uuid = ''.join([random.choice(string.ascii_letters+string.digits) for n in xrange(8)])
        c.execute("INSERT INTO devices VALUES ('"+rand_uuid+"','"+type_d+"','"+mac_d+"','"+ver_d+"','"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"')")
        for sens in my_json["e"]:
           c.execute("INSERT INTO sensors VALUES ('"+rand_uuid+"','"+sens["n"]+"','"+sens["u"]+"')")
        conn.commit()
    conn.close()
    return rand_uuid

    
def sendMssgResolv(data,header):
    print("---------Send Data---------")
    send_json="{'e':["+data+"],'bn':'urn:dev:id:OWaDMY9V'}"
    try:
        my_json=json.loads(send_json.replace("'",'"'));
        print(json.dumps(my_json,indent=4,sort_keys=True))
        #Send to device
        sendRf(send_json)
    except ValueError:
        print("Bad: correct partial data probably")

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

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print ("Keyboard baby")
    radio.stopListening()
    connection.close()
    print ("Exiting Main Thread")  
            
    

