#!/usr/bin/env python

#
# Example using Dynamic Payloads
# 
#  This is an example of how to use payloads of a varying (dynamic) size.
# 
# Modified to work from FogOf Thinggs and with Ini Fie
# To-Do: Nothing Really for this

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
import ConfigParser
import os,sys
#Config Settings
Config=ConfigParser.ConfigParser()
Config.read(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))+"/config.ini")


irq_gpio_pin = 25

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
            message=payload.strip()
            if (len(message)>300):
                print("length error")
                message=""
            if message[0:1]=='{':
                start=time.time()
                handle_data(message.split('}',1)[0]+'}')
            #print('Got payload size={} value="{}"'.format(len, receive_payload.decode('utf-8')))

              
def handle_data(data):
    data=data.replace("'",'"')
    print(data)
    try:
        print("validate json")
        print(len(data));
        my_json=json.loads(data);
        print(json.dumps(my_json,indent=4,sort_keys=True))
        messageResolv(my_json)
    #except ValueError:
       # print("Value Erro, probs something stupid happened")
    except IndexError:
        print("Index Error, probs something stupid happened")

def messageResolv(my_json):
    try:
        print("resolve json")
        dev_id=my_json.get("id")
        print(dev_id)
        message_amqp=my_json.get("v")
        properties_m=pika.BasicProperties(headers={'device':""+dev_id,'comm': ""+gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        channel.basic_publish(exchange='device', routing_key='', body=message_amqp, properties=properties_m)
    except ValueError:
        print("Value Erro, probs something stupid happened")
    except IndexError:
        print("Index Error, probs something stupid happened")


    
def sendMssgResolv(data,header):
    print("---------Send Data---------")
    print(data)
    print("Not an option for these devices")

def callback(ch,method,properties,body):
    print("[x] Received %r"%body)
    sendMssgResolv(body,properties) 
    
pipes = [Config.get("RF24-tiny","pipe_write"),Config.get("RF24-tiny","pipe_read")]
gw_name=Config.get("RF24-tiny","name")


print('Receive Example')
radio.begin()

if irq_gpio_pin is not None:
        # set up callback for irq pin
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(irq_gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(irq_gpio_pin, GPIO.FALLING, callback=try_read_data)

    radio.openWritingPipe(pipes[0])
    radio.openReadingPipe(1,pipes[1])
    radio.startListening()

#AMQP Stuff

credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
connection = pika.BlockingConnection(parameters);

channel = connection.channel()
channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,queue=Config.get("RF24-tiny","queue"),no_ack=True)


# forever loop
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print ("Keyboard baby")
    radio.stopListening()
    connection.close()
    print ("Exiting Main Thread")  

