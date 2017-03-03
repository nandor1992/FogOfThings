#!/usr/bin/env python
import couchdb
import pika
import ast
import time

class Fake_Dev():
    def __init__(self,c_user,c_pass,user,passw,port,virt):
        print("Initialized!")
        self.c_user=c_user
        self.c_pass=c_pass
        self.couch=couchdb.Server('http://'+self.c_user+':'+self.c_pass+'@127.0.0.1:5984/')        
        self.credentials = pika.PlainCredentials(user,passw)
        self.parameters = pika.ConnectionParameters('localhost',port,virt,self.credentials)
        self.connection = pika.BlockingConnection(self.parameters);
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.on_request, queue="dev_test",no_ack=True)
        self.device="Python_Dev"
        self.sent=time.time()
        
    def on_request(self,ch, method, properties, body):
        data=ast.literal_eval(body)
        print(data['start_time'])
        print(data['proc_time'])
        print("Elapsed: "+str(time.time()-long(self.sent)))

    def send_request(self):
        message_amqp=time.time()
        self.sent=time.time()
        properties_m=pika.BasicProperties(headers={'device':self.device})
        self.channel.basic_publish(exchange='device', routing_key='', body=str(message_amqp), properties=properties_m)
                
    def start(self):
        print("Started!")
        self.channel.start_consuming()
        
    def putData(data):
        db=self.couch['monitoring']
        db.save(data);

    def close(self):
        self.channel.stop_consuming()
        self.channel.close()
        self.connection.close()
        
if __name__ == "__main__":
    try:
        f=Fake_Dev("admin","hunter","admin","hunter",5672,"test")
        f.send_request()
        f.start();
    except KeyboardInterrupt:
        f.close();
        print("Keyboard Interrupt")
