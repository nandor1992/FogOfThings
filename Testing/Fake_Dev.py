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
        self.channel.basic_qos(prefetch_count=1)
        self.device="Python_Dev"
        self.channel.basic_consume(self.on_request, queue="dev_test",no_ack=True)
        self.sum=0.0
        self.count=0
        self.proc=0.0
        self.first=0;
        
    def on_request(self,ch, method, properties, body):
        data=ast.literal_eval(body)
        print("---------------Message Received-----------")
        end=time.time()
        #print(data['start_time'])
        #print(end)
        start=float(data['start_time'])
        print("Elapsed: "+str((end-start)*1000))
        print("Processing: "+str(int(data['proc_time'])/1000.0))
        if self.first>2:
            self.sum=self.sum+(end-start)*1000
            self.proc=self.proc+float(data['proc_time'])/1000.0
            self.count=self.count+1
        else:
            self.first=self.first+1
                
    def putData(data):
        db=self.couch['monitoring']
        db.save(data);

    def stop(self):
        self.channel.stop_consuming()
        self.channel.close()
        self.connection.close()
        print("Stopped Listening!")

    def summary(self):
        return {'response_time':self.sum/self.count,'proc_time':self.proc/self.count}
            
    def run(self):
        print("Started Listening!")
        self.channel.start_consuming()

class Poster(threading.Thread):
    def __init__(self,c_user,c_pass,user,passw,port,virt,rate,cnt):
        print("Initialized!")
        threading.Thread.__init__(self)
        self.c_user=c_user
        self.c_pass=c_pass
        self.couch=couchdb.Server('http://'+self.c_user+':'+self.c_pass+'@127.0.0.1:5984/')        
        self.credentials = pika.PlainCredentials(user,passw)
        self.parameters = pika.ConnectionParameters('localhost',port,virt,self.credentials)
        self.connection = pika.BlockingConnection(self.parameters);
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=2)
        self.device="Python_Dev"
        self.rate=10.0/rate
        self.stopMe=False
        self.count=0
        self.range=cnt
    def send_request(self):
        message_amqp=time.time()
        properties_m=pika.BasicProperties(headers={'device':self.device})
        self.channel.basic_publish(exchange='device', routing_key='', body=str(message_amqp), properties=properties_m)
                
    def stop(self):
        self.stopMe=True
        
    def run(self):
        print("Started Posting!")
       # while not self.stopMe:
          #  self.send_request()
         #   time.sleep(self.rate)
        for i in range(0,self.range):
            self.send_request()
            time.sleep(self.rate)
        self.channel.close()
        self.connection.close()
        print("Posting Done!")


if __name__ == "__main__":
    msg_rate=10; #/10Seconds
    t=time.clock()
    try:
        l=Listener("admin","hunter","admin","hunter",5672,"test")
        p=Poster("admin","hunter","admin","hunter",5672,"test",msg_rate,10)
        p.start()
        l.run()
    except KeyboardInterrupt:
        p.stop()
        print(l.summary())
        l.stop()
        print("Interrupt Keyboard - Stop!")    
