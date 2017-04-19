#!/usr/bin/env python
import couchdb
import pika
import ast
import time
import threading
import ctypes
import datetime
import sys
from daemon import Daemon
import ConfigParser
import logging
t=time
t.clock()
PIDFILE="/home/pi/FogOfThings/Device/pid/fake_dev.pid"
Config=ConfigParser.ConfigParser()
Config.read("/home/pi/FogOfThings/Device/config.ini")
LOGFILE = Config.get("Log","location")+'/fake_dev.log'
logging.basicConfig(filename=LOGFILE,level=logging.DEBUG)
logging.getLogger("pika").setLevel(logging.ERROR)
class Listener():
    def __init__(self,c_user,c_pass,user,passw,port,virt,que,dev,rte,rate):
        logging.debug("Initialized!")
        self.c_user=c_user
        self.c_pass=c_pass
        self.couch=couchdb.Server('http://'+self.c_user+':'+self.c_pass+'@127.0.0.1:5984/')        
        self.credentials = pika.PlainCredentials(user,passw)
        self.parameters = pika.ConnectionParameters('localhost',port,virt,self.credentials)
        self.connection = pika.BlockingConnection(self.parameters);
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        self.device="Python_Dev"
        self.channel.basic_consume(self.on_request, queue=que,no_ack=True)
        self.sum=0.0
        self.rec_time=t.time()
        self.t_start=datetime.datetime.now()
        self.count=0
        self.proc=0.0
        self.first=0;
        self.rate=rate
        self.t_start=datetime.datetime.now()
        self.C_Dev=dev
        self.C_Rate=rte

    def saveToCouch(self,data):
        db=self.couch['monitoring']
        data['type']="Driver"
        data['Gateway']=Config.get("General","gateway_name")
        data['Device']=self.C_Dev
        data['Rate']=self.C_Rate
        logging.debug(data)
        db.save(data)
        
    def on_request(self,ch, method, properties, body):
        global t
        global rate
        data=ast.literal_eval(body)
        #logging.debug("---------------Message Received-----------")
        #logging.debug("Cnt:"+str(self.count))
        end=t.time()
        #logging.debug(data['start_time'])
        #logging.debug(end)
        start=float(data['start_time'])
        #logging.debug("Elapsed: "+str((end-start)*1000))
        #logging.debug("Processing: "+str(int(data['proc_time'])/1000.0))
        if end-self.rec_time >= self.rate:
            logging.debug("Started at:"+str(self.t_start))
            data=self.summary()
            data['date']=self.t_start.strftime("%Y-%m-%d %H:%M:%S")
            logging.debug(data)
            self.t_start=datetime.datetime.now()
            self.sum=0.0
            self.count=0
            self.proc=0.0   
            self.rec_time=end
            self.saveToCouch(data)
        else:
            self.sum=self.sum+(end-start)*1000
            self.count=self.count+1
            self.proc=self.proc+int(data['proc_time'])/1000.0     
                
    def putData(data):
        db=self.couch['monitoring']
        db.save(data);

    def stop(self):
        self.channel.stop_consuming()
        self.channel.close()
        self.connection.close()
        logging.debug("Stopped Listening!")

    def summary(self):
        return {'response_time':self.sum/self.count,'proc_time':self.proc/self.count}
            
    def run(self):
        logging.debug("Started Listening!")
        self.channel.start_consuming()


class Poster(threading.Thread):

    global running
    running = True
    def __init__(self,c_user,c_pass,user,passw,port,virt,rate,dev):
        logging.debug("Initialized!")
        threading.Thread.__init__(self)
        self.c_user=c_user
        self.c_pass=c_pass
        self.couch=couchdb.Server('http://'+self.c_user+':'+self.c_pass+'@127.0.0.1:5984/')        
        self.credentials = pika.PlainCredentials(user,passw)
        self.parameters = pika.ConnectionParameters('localhost',port,virt,self.credentials)
        self.connection = pika.BlockingConnection(self.parameters);
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        self.device=dev
        self.rate=10.0/rate
        self.count=0
        
    def send_request(self):
        global t
        message_amqp=t.time()
        properties_m=pika.BasicProperties(headers={'device':self.device})
        self.channel.basic_publish(exchange='device', routing_key='', body="{:10.8f}".format(message_amqp), properties=properties_m)
                
    def stop(self):
        global running
        running = False
        
    def run(self):
        global running
        logging.debug("Started Posting!")
       # while not self.stopMe:
          #  self.send_request()
         #   time.sleep(self.rate)
        while running:
            self.send_request()
            time.sleep(self.rate)
        self.channel.close()
        self.connection.close()
        logging.debug("Posting Done!")

class Fake_Dev():
    def init(self,dev,rate,que):
        self.l=Listener("admin","hunter","admin","hunter",5672,"test",que,dev,rate,10)
        self.p=Poster("admin","hunter","admin","hunter",5672,"test",rate,dev)

    def run(self):
        self.p.start()
        self.l.run()
    
    def stop(self):
        try:
            self.p.stop()
            time.sleep(2)
            self.l.stop()
        except AttributeError:
            pass
        logging.debug("Interrupt Keyboard - Stop!")

if __name__ == "__main__":
    up=Fake_Dev()
    try:
        for arg in sys.argv:
            part=arg.split("=")
            if part[0][2:]=="device":
                dev=part[1]
            elif part[0][2:]=="rate":
                rate=float(part[1])
            elif part[0][2:]=="que":
                que=part[1]
        if dev!=None and rate!=None and que!=None:
            msg_rate=rate*10
        else:
            exit()
        up.init(dev,rate,que)
        up.run()
    except Exception , e:
        logging.debug(e)
        up.stop()
        logging.debug("Exiting Main Thread - Keyboard")
    except KeyboardInterrupt:
        up.stop()
        logging.debug("Exiting Main Thread - Keyboard")
