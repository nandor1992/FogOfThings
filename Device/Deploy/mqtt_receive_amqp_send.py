#!/usr/bin/env python
import pika
import time
import paho.mqtt.client as mqtt
import datetime
import json
import os,sys
import time
import ConfigParser
import urllib
#Config Settings

# Modified to work from FogOf Thinggs and with Ini Fie
#No To-Do's Here

Config=ConfigParser.ConfigParser()
Config.read(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))+"/config.ini")


clientId=Config.get("General","Gateway_Name")
conn_name=Config.get("Mqtt1","name")
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc):
    global gw_name
    print("Connected with result code "+str(rc))
	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.
    client.subscribe("receive/"+clientId,2)
    sys.stdout.flush()

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print ("------Received Message-------")
    print("Message: "+msg.topic+" "+str(msg.payload)[1:-1])
    try:
	payload=(str(msg.payload));
	payload=payload.replace('\n', '').replace('\r', '')
	print payload;
        my_json=json.loads(payload);
        print json.dumps(my_json,indent=1,sort_keys=True)
        headers={'cloud':conn_name}
        for item in my_json:
            if (item!="payload"):
                headers.update({item:my_json[item]})
        print(headers)
        properties_m=pika.BasicProperties(headers=headers)
        payload=json.dumps(my_json["payload"])
        print(payload)
        if ("device" in my_json) or ("dev_type" in my_json):
            print "Device message"
            retr=False
            while retr==False:
                retr=publish('device',payload,properties_m)
        else:
            print "Other message"
            payload=payload[1:-1]
            retr=False
            while retr==False:
                retr=publish('app',payload,properties_m)
            #channel.basic_publish(exchange='',routing_key='test_queue',body=msg.payload)
    except (ValueError,TypeError) as e:
        print "Value Erro, probs something stupid happened"
    sys.stdout.flush()

def publish(route,body,properties):
    global channel
    global parameters
    try:
        channel.basic_publish(exchange='cloud', routing_key=route, body=body,properties=properties)
        return True
    except pika.exceptions.ConnectionClosed:
        print("Pika Disconnected "+time.strftime('%X %x %Z')+ ", Reconnecting")
        sys.stdout.flush()
        connection = pika.BlockingConnection(parameters);
        channel=connection.channel()
        return False
    
def on_disconnect(client,userdata,rc):
    global Config
    if rc!=0:
        print "Unexpected Disconnect "+time.strftime('%X %x %Z')+ " Reconnecting"
       #  client.reconnect()
        client.loop_stop()
        client.disconnect()
        client.reinitialise()
        loop=0
        while loop==0:
            try:
                client = mqtt.Client(client_id=""+clientId+"_Receive",clean_session=True);
                client.username_pw_set(Config.get("Mqtt1","user"),Config.get("Mqtt1","pass"))
                client.on_connect = on_connect
                client.on_message = on_message
                client.on_disconnect = on_disconnect
                client.connect(Config.get("Mqtt1","address"),int(Config.get("Mqtt1","port")) ,10)
                client.loop_forever(timeout=1.0, max_packets=1,retry_first_connection=False)
                loop=1
            except:
                print "Exception hit at mqtt reconnect"
                sys.stdout.flush()
                time.sleep(5)
            
    else:
        print "Expected Disconnect"
    sys.stdout.flush()

f=open(Config.get("Log","location")+'/mqtt_to_amqp.log','a')
sys.stdout=f
print("Starting New Session at "+time.strftime('%X %x %Z'))
sys.stdout.flush()
client = mqtt.Client(client_id=clientId+"_Receive",clean_session=True);
client.username_pw_set(Config.get("Mqtt1","user"),Config.get("Mqtt1","pass"))
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.connect(Config.get("Mqtt1","address"),int(Config.get("Mqtt1","port")) ,10)

credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
connection = pika.BlockingConnection(parameters);
channel = connection.channel()
# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
try:
    client.loop_forever(timeout=1.0, max_packets=1,retry_first_connection=False)
except:
    client.loop_stop()
    client.disconnect()
    connection.close()
    print "Exiting Main Thread"
    sys.stdout.flush()
