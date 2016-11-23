#!/usr/bin/env python
import pika
import datetime
import json
import time
import os,sys
import ConfigParser
import datetime
## This is Dummy might need to make it smarter later on 
#Config Settings
Config=ConfigParser.ConfigParser()
Config.read(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))+"/config.ini")

Config.read(os.getcwd()+"/config.ini")

credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
connection = pika.BlockingConnection(parameters);

channel = connection.channel()
channel.basic_qos(prefetch_count=1)

        
def on_request(ch, method, properties, body):
    app_name=properties.headers.get("app")
    req_type=properties.headers.get("task")
    if (req_type=="get"):
        resp="{'cluster':['Gatweway-UUID1','Gateway-UUID2'],'avg_latency':'23ms'}"
        properties_m=pika.BasicProperties(headers={'app':app_name,'res': "metadata"})
        channel.basic_publish(exchange='resource', routing_key='', body=resp, properties=properties_m)
    ch.basic_ack(delivery_tag = method.delivery_tag)
channel.basic_consume(on_request, queue=Config.get("Metadata","queue"))


print(" [x] Awaiting RPC requests")
try:
    channel.start_consuming()     
except KeyboardInterrupt:
    print ("Keyboard baby")
    channel.stop_consuming()
    channel.close()
    connection.close()
    print ("Exiting Main Thread")
