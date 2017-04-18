#!/usr/bin/env python
import couchdb
import pika
import ast
import time
import threading
import ctypes
import datetime
import sys

t=time
t.clock()
class Listener():
    def __init__(self,c_user,c_pass,user,passw,port,virt,cnt,que):
        print("Initialized!")
        self.c_user=c_user
        self.c_pass=c_pass
        self.couch=couchdb.Server('http://'+self.c_user+':'+self.c_pass+'@10.0.0.137:5984/')        
        self.credentials = pika.PlainCredentials(user,passw)
        self.parameters = pika.ConnectionParameters('localhost',port,virt,self.credentials)
        self.connection = pika.BlockingConnection(self.parameters);
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        self.device="Python_Dev"
        self.channel.basic_consume(self.on_request, queue=que,no_ack=True)
        self.sum=0.0
        self.count=0
        self.proc=0.0
        self.first=0;
        self.tot=cnt
        self.t_start=None
        
    def on_request(self,ch, method, properties, body):
        global t
        data=ast.literal_eval(body)
        print("---------------Message Received-----------")
        print("Cnt:"+str(self.first))
        end=t.time()
        #print(data['start_time'])
        #print(end)
        start=float(data['start_time'])
        print("Elapsed: "+str((end-start)*1000))
        print("Processing: "+str(int(data['proc_time'])/1000.0))
        if self.first==self.tot/5:
           self.t_start=datetime.datetime.now()
        if self.first>self.tot/5:
            self.sum=self.sum+(end-start)*1000
            self.proc=self.proc+float(data['proc_time'])/1000.0
            self.count=self.count+1
            self.first=self.first+1
        else:
            self.first=self.first+1
        self.end=datetime.datetime.now()
                
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
    def __init__(self,c_user,c_pass,user,passw,port,virt,rate,cnt,dev):
        print("Initialized!")
        threading.Thread.__init__(self)
        self.c_user=c_user
        self.c_pass=c_pass
        self.couch=couchdb.Server('http://'+self.c_user+':'+self.c_pass+'@10.0.0.137:5984/')        
        self.credentials = pika.PlainCredentials(user,passw)
        self.parameters = pika.ConnectionParameters('localhost',port,virt,self.credentials)
        self.connection = pika.BlockingConnection(self.parameters);
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        self.device=dev
        self.rate=10.0/rate
        self.count=0
        self.range=cnt
    def send_request(self):
        global t
        message_amqp=t.time()
        properties_m=pika.BasicProperties(headers={'device':self.device})
        self.channel.basic_publish(exchange='device', routing_key='', body="{:10.8f}".format(message_amqp), properties=properties_m)
                
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
    dev=None
    rate=None
    msg_cnt=0
    msg_rate=0
    que=None
    tmp=0
    for arg in sys.argv:
        print(arg)
        part=arg.split("=")
        if part[0][2:]=="device":
            print("Device")
            print(part[1])
            dev=part[1]
        elif part[0][2:]=="rate":
            print("Rate")
            print(part[1])
            rate=float(part[1])
        elif part[0][2:]=="time":
            print("Rate")
            print(part[1])
            tmp=int(part[1])
        elif part[0][2:]=="que":
            print("Que")
            print(part[1])
            que=part[1]
        else:
            print("Unknown Exit")
    if dev!=None and rate!=None and que!=None:
        msg_cnt=int(rate*tmp*60)
        msg_rate=rate*10
    else:
        exit()
    try:
        l=Listener("admin","hunter","admin","hunter",5672,"test",msg_cnt,que)
        p=Poster("admin","hunter","admin","hunter",5672,"test",msg_rate,msg_cnt,dev)
        p.start()
        l.run()
    except KeyboardInterrupt:
        p.stop()
        end=l.end
        print(l.summary())
        l.stop()
        print("Started: "+l.t_start.strftime("%Y-%m-%d %H:%M:%S"))
        print("Now: "+end.strftime("%Y-%m-%d %H:%M:%S"))
        print("Interrupt Keyboard - Stop!")    
