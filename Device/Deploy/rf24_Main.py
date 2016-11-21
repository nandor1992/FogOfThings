#!/usr/bin/env python

#
# Example using Dynamic Payloads
# 
#  This is an example of how to use payloads of a varying (dynamic) size.
# 
# Modified to work from FogOf Thinggs and with Ini Fie
# Modified Driver to Work with CouchDB

from __future__ import print_function
from threading import Timer
import time
from RF24 import *
import RPi.GPIO as GPIO
import pika
import json
import datetime
import string
import random
import database
import os,sys
import ConfigParser
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

f=open(Config.get("Log","location")+'/rf24.log','a')
sys.stdout=f

##########################################
def try_read_data(channel=0):
    global message;
    if radio.available():
        while radio.available():
            length = radio.getDynamicPayloadSize()
            payload = radio.read(length).decode()
            payload = payload[:31]
            message=message+payload.strip()
            #print(message)
            if (message[-1]=='}' and message[0:1]=='{'):
                print("--------Message Received on CH=1-------")
                handle_data(message)
                message=""
            elif message[0:1]!='{':
                print("Wrong Start to msg delete rest")
                message=""
            elif len(message)>300:
                print("length error")
                message=""
            #print(message)
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
    sys.stdout.flush()
    
def messageResolv(my_json):
    dev_id=my_json.get("bn")[11:]
    dev_id=dev_id[:8]
    print(dev_id)
    if (dev_list.count(dev_id)!=0):
        message_amqp=json.dumps(my_json["e"])
	message_amqp=message_amqp.replace('"',"'")
        message_amqp=message_amqp.replace(' ','')
        print(message_amqp)
        if  dev_id in timer_list:
            timer_list[dev_id].cancel()
        properties_m=pika.BasicProperties(headers={'device':""+dev_id,'comm': ""+gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        channel.basic_publish(exchange='device', routing_key='', body=message_amqp, properties=properties_m)
        updateDevTime(dev_id,"Available")
    else:
        print("No details found - not forwarding")
    sys.stdout.flush()
    
def registerResolv(my_json):
    trans=my_json.get("bn",{})[2]
    my_uuid=resolv_dev(my_json)
    trans=trans[9:]
    data="{'bn':['trans:id:"+trans+"','urn:dev:id:"+my_uuid+"']}"
    sendRf(data);
    sys.stdout=f

def resolv_dev(my_json):
    print ("Json Parts!")
    type_d=my_json.get("bn",{})[0][13:]
    mac_d=my_json.get("bn",{})[1][12:]
    ver_d=my_json.get("ver")
    value=datab.lookupDev(mac_d,type_d,ver_d)
    if value!=None:
        print("Found details "+value[0])
        rand_uuid=value[0]
        updateDevTime(value[0],"Available")
        dev_list.append(value[0])
    else:
        print("No details found")
        rand_uuid = ''.join([random.choice(string.ascii_letters+string.digits) for n in xrange(8)])
        print("New UUID="+str(rand_uuid))
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
    dev_id=str(header.headers.get('device')).strip()
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
        sendRf(send_json)
    else:
        print("Data received for non existent Dev")
    sys.stdout.flush()
    
def callback(ch,method,properties,body):
    sendMssgResolv(body,properties) 


def timeout(dev,val,cnt):
    global message
    print("Message Timed Out: ",cnt)
    if (cnt<5):
        sendRf(val)
        t=Timer(5,timeout,[dev,val,cnt+1])
        t.start()
        timer_list[dev]=t
        message="";
    else:
        print ("Max Retransmit Reached")
        message_amqp="[{'Retransmit Error'}]"
        properties_m=pika.BasicProperties(headers={'device':""+dev,'comm': ""+gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        channel.basic_publish(exchange='device', routing_key='', body=message_amqp, properties=properties_m)
        timer_list[dev].cancel()
        updateDevTime(dev,"Max Retransmit")
    sys.stdout.flush()

def resetTimeout():
    global radio
    global t_reset
    global message
    sendRf("{'e':'This_is_a_test'}")
    t_reset=Timer(90,resetTimeout)
    t_reset.start()
    sys.stdout.flush()
        
def updateDev(dev_id,status):
    #ToDo update Date of Device
    datab.updateStat(dev_id,status)

def updateDevTime(dev_id,status):
    #ToDo update Date of Device
    datab.updateDateStat(dev_id,status,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
pipes = [Config.get("RF24","pipe_write"),Config.get("RF24","pipe_read")]
gw_name=Config.get("RF24","name")
dev_list= []
timer_list = {}

print("RF24 Radio started: "+time.strftime('%X %x %Z'))

radio.begin()
radio.enableDynamicPayloads()
radio.setPALevel(RF24_PA_MAX);
radio.setRetries(5,15);

if irq_gpio_pin is not None:
    # set up callback for irq pin
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(irq_gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(irq_gpio_pin, GPIO.FALLING, callback=try_read_data)

    radio.openWritingPipe(pipes[0])
    radio.openReadingPipe(1,pipes[1])
    radio.startListening()

#Create sql stuff and initialize

#Get Database deviecs
datab=database.Database(Config.get("couchDB","user"),Config.get("couchDB","pass"),'rf24')
value=datab.getAllDevs()
for r in value:
    datab.updateStat(r,"Idle")
sys.stdout.flush()
#AMQP Stuff

credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
connection = pika.BlockingConnection(parameters);

channel = connection.channel()
channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,queue=Config.get("RF24","queue"),no_ack=True)


#Timer Stuff
t_reset=Timer(90,resetTimeout)
t_reset.start()  
        
# forever loop
try:
    channel.start_consuming()     
except KeyboardInterrupt:
    print ("Keyboard baby")
    radio.stopListening()
    channel.close()
    connection.close()
    t_reset.cancel()
    print ("Exiting Main Thread")
    sys.stdout.flush()
