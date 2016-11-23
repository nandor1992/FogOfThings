#!/usr/bin/env python
import pika
import datetime
import json
import time
import os,sys
import ConfigParser
import datetime
import couchdb
#Config Settings
Config=ConfigParser.ConfigParser()
Config.read(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))+"/config.ini")

Config.read(os.getcwd()+"/config.ini")

credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
connection = pika.BlockingConnection(parameters);

channel = connection.channel()
channel.basic_qos(prefetch_count=1)


map_databases = '''function(doc){
        emit(doc.datetime,doc.payload);
        }'''
couch=couchdb.Server('http://'+Config.get("couchDB","user")+':'+Config.get("couchDB","pass")+'@127.0.0.1:5984/')

def getData(db,first,last):
    resp=""
    print ("Data: "+first+" "+last)
    look=db.query(map_databases)
    for p in look[first:last]:
        print(p.value)
        resp=resp+p.value+";"
    return resp
        
def on_request(ch, method, properties, body):
    app_name=properties.headers.get("app")
    req_type=properties.headers.get("task")
    if (req_type=="add"):
        print("Received Add Message")
        db=couch["app_"+app_name.lower()]
        db.save({'datetime':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'payload':body})
    ch.basic_ack(delivery_tag = method.delivery_tag)
    if (req_type=="get"):
        print("Received Get Message")
        db=couch["app_"+app_name.lower()]
        parts=body.split(';')
        response=getData(db,parts[0],parts[1])
        print("Resp: ")
        print(response)
        properties_m=pika.BasicProperties(headers={'app':app_name,'res': "storage"})
        channel.basic_publish(exchange='resource', routing_key='', body=response, properties=properties_m)

channel.basic_consume(on_request, queue=Config.get("couchDB","queue"))


print(" [x] Awaiting RPC requests")
try:
    channel.start_consuming()     
except KeyboardInterrupt:
    print ("Keyboard baby")
    channel.stop_consuming()
    channel.close()
    connection.close()
    print ("Exiting Main Thread")
