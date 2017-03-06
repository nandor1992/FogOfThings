#!/usr/bin/env python
import couchdb
import pika
import ast
import time
import threading
import ctypes

class Listener():
    def __init__(self,c_user,c_pass,user,passw,port,virt):
        print("Initialized!")
        self.c_user=c_user
        self.c_pass=c_pass
        self.couch=couchdb.Server('http://'+self.c_user+':'+self.c_pass+'@127.0.0.1:5984/')        
        self.credentials = pika.PlainCredentials(user,passw)
        self.parameters = pika.ConnectionParameters('localhost',port,virt,self.credentials)
        self.connection = pika.BlockingConnection(self.parameters);
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=2)
        self.device="Python_Dev"
        self.channel.basic_consume(self.on_request, queue="dev_test",no_ack=True)
        
    def on_request(self,ch, method, properties, body):
        data=ast.literal_eval(body)
        print("---------------Message Received-----------")
        end=time.time()
        start=long(data['start_time'])
        print("Elapsed: "+str(end-start))
        print("Processing: "+str(data['proc_time']))
                
    def putData(data):
        db=self.couch['monitoring']
        db.save(data);

    def stop(self):
        self.channel.stop_consuming()
        self.channel.close()
        self.connection.close()
        print("Stopped Listening!")
        
    def start(self):
        print("Started Listening!")
        self.channel.start_consuming()

if __name__ == "__main__":
    print("Starting Listener")
    try:
        l=Listener("admin","hunter","admin","hunter",5672,"test")
        l.start()
    except KeyboardInterrupt:
        l.stop()
        print("Interrupt Keyboard - Stop!")
