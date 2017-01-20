#!/usr/bin/env python
import pika
import time
import paho.mqtt.client as mqtt
import json
import os,sys
import ConfigParser
#Config Settings
Config=ConfigParser.ConfigParser()
Config.read(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))+"/config.ini")


# Modified to work from FogOf Thinggs and with Ini Fie
#No To-Do's Here

clientId=Config.get("General","Gateway_Name")
conn_name=Config.get("Mqtt1","name")

credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
connection = pika.BlockingConnection(parameters);

channel = connection.channel()

client = mqtt.Client(client_id=clientId+"_Send",clean_session=True);
client.username_pw_set(Config.get("Mqtt1","user"),Config.get("Mqtt1","pass"))
client.connect(Config.get("Mqtt1","address"),int(Config.get("Mqtt1","port")) ,10)

f=open(Config.get("Log","location")+'/amqp_to_mqtt.log','a')
sys.stdout=f
    
print("Broker started: "+time.strftime('%X %x %Z'))
print(' [*] Waiting for messages. To exit press CTRL+C')

def callback(ch,method,properties,body):
    print("[x] Received %r"%body)
    admin=False
    try:
        try:
            my_json=json.loads('{"payload":'+body+'}')
        except ValueError:
            print "Non json payload"
            body=body.replace('"',"'")
            my_json=json.loads('{"payload":"'+body+'"}')
        for names in properties.headers:
            if names=="source":
                if properties.headers.get(names)=="Cloud_Controller":
                    admin=True
            temp={names:properties.headers.get(names)}
            my_json.update(temp)
        data=json.dumps(my_json)
        print data
        client.reconnect()
        if admin:
            dest="receive/Cloud_Controller"
        else:
            dest="send/"+clientId
        (result,mid)=client.publish(dest,payload=data,qos=1)
        while result!=mqtt.MQTT_ERR_SUCCESS:
            print("MQTT Disconnected "+time.strftime('%X %x %Z')+ ", Reconnecting")
            client.reconnect()
            (result,mid)=client.publish(dest,payload=data,qos=1)
        print("Message Sent with result: "+str(result)+" Message Id: "+str(mid))
            
    except (ValueError, TypeError) as e:
            print "Nor Json or valid string data"
    sys.stdout.flush()
    
channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,queue=conn_name,no_ack=True)
sys.stdout.flush()
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print "Keyboard baby"
    client.disconnect()
    connection.close()
    print "Exiting Main Thread"
    sys.stdout.flush()
