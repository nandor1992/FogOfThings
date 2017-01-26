#!/usr/bin/env python

from __future__ import print_function
from threading import Timer
import time
from RF24 import *
import RPi.GPIO as GPIO
import pika
import sqlite3
import json
import datetime
import string
import random
import bluetooth
import Queue
import threading
import os,sys
import database
import ConfigParser
from daemon import Daemon
import logging
#Config Settings
PIDFILE="/home/pi/FogOfThings/Device/pid/blue.pid"

Config=ConfigParser.ConfigParser()
Config.read("/home/pi/FogOfThings/Device/config.ini")
LOGFILE = Config.get("Log","location")+'/rf_blue.log'
# Configure logging
logging.basicConfig(filename=LOGFILE,level=logging.DEBUG)
exitFlag=0
send_q = {}
receive_q = {}
threads = {}
#class blue():
class blue(Daemon):

    class BlueThread(threading.Thread):

        def __init__(self,name,socket,send_q,receive_q):
            threading.Thread.__init__(self)
            self.name=name
            self.socket = socket
            self.send_q = send_q
            self.receive_q=receive_q

        def run(self):
            logging.debug("Starting Blue Stuff for " + self.name)
            self.transLoop(self.socket, self.send_q, self.receive_q)
            logging.debug("Exiting Blue Stuff for " + self.name)    

        def transLoop(self,socket,send_q,receive_q):
            message="";
            while not exitFlag:
                if not send_q.empty():
                    data = send_q.get()
                    logging.debug("Sending: " +data)
                    socket.send(data+'\n')
                try:
                    reading=socket.recv(1024)
                    if ((len(reading)>0 and reading[0]!=' ')):
                        message=message+reading;
                    if message[-1]=='\n' and message[-2]=='}':
                        receive_q.put(message)
                        message="";
                    if (len(message)>250):
                        logging.debug("Long Message Error")
                        logging.debug(len(message))
                        message=""
                except bluetooth.BluetoothError as error:
                    if error[0]!="timed out":
                        logging.error("Error:",error)
                        break;
            socket.close()
        
    class ServerThread(threading.Thread):
        def __init__(self,server_sock):
            threading.Thread.__init__(self)
            self.server_sock=server_sock
        def run(self):
            logging.debug("Started Server Thread")
            port = self.server_sock.getsockname()[1]
            logging.debug("Waiting for connection on RFCOMM channel %d" % port)
            self.server_sock.settimeout(2)
            while not exitFlag:
                try:
                    client_socket, client_info = self.server_sock.accept()
                    client_socket.send('x')
                    addr=client_info[0]
                    client_socket.settimeout(0.1)
                    send_q[addr]=Queue.Queue(10)
                    receive_q[addr]=Queue.Queue(10)
                    bluet=blue.BlueThread(addr,client_socket,send_q[addr],receive_q[addr])
                    bluet.start()
                    threads[addr]=bluet
                except bluetooth.BluetoothError :
                    pass
            logging.debug("Exiting Server")
    
    def handle_data(self,key,data):
        logging.debug("--------Message Received from: "+key+"-------")
        data=data.replace("'",'"')
        try:
            my_json=json.loads(data);
        #Check if available in database if yes give it old id of not new one
        #and save to db when given, parse messages to see data as well
            if len(my_json["bn"][1])>=3:
                logging.debug("Register data received")
                self.registerResolv(key,my_json)
            else:
                logging.debug("Normal data received")
                self.messageResolv(my_json)
        except ValueError:
            logging.error("Value Erro, probs something stupid happened")
        except IndexError:
            logging.error("Index Error, probs something stupid happened")
        except KeyError:
            logging.error("Key Error, probs something bad happened")

    def messageResolv(self,my_json):
        dev_id=my_json.get("bn")[11:]
        dev_id=dev_id[:8]
        logging.debug(dev_id)
        if (self.dev_list.count(dev_id)!=0):
            message_amqp=json.dumps(my_json["e"])
            message_amqp=message_amqp.replace('"',"'")
            logging.debug(message_amqp)
            if dev_id in self.timer_list:
                self.timer_list[dev_id].cancel()
            properties_m=pika.BasicProperties(headers={'device':""+dev_id,'comm': ""+self.gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            self.channel.basic_publish(exchange='device', routing_key='', body=message_amqp, properties=properties_m)
            self.updateDevTime(dev_id,"Available")
        else:
            logging.debug("No details found - not forwarding")
    
    def registerResolv(self,key,my_json):
        trans=my_json.get("bn",{})[2]
        my_uuid=self.resolv_dev(my_json)
        trans=trans[9:]
        data="{'bn':['trans:id:"+trans+"','urn:dev:id:"+my_uuid+"']}"
        self.dev_mac[my_uuid]=key
        self.sendRf(my_uuid,data);

    
    def resolv_dev(self,my_json):
        logging.debug("Json Parts!")
        type_d=my_json.get("bn",{})[0][13:]
        mac_d=my_json.get("bn",{})[1][12:]
        ver_d=my_json.get("ver")
        value=self.datab.lookupDev(mac_d,type_d,ver_d)
        if value!=None:
            logging.debug("Found details "+value)
            rand_uuid=value
            self.updateDevTime(value,"Available")
            self.dev_list.append(value)
        else:
            logging.debug("No details found")
            rand_uuid = ''.join([random.choice(string.ascii_letters+string.digits) for n in xrange(8)])
            sense=[]
            for sens in my_json["e"]:
                sense.append({sens["n"]:sens["u"]})
            self.datab.addDevice(rand_uuid,type_d,mac_d,ver_d,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'Available',sense)
            self.dev_list.append(rand_uuid)
        return rand_uuid

    
    def sendMssgResolv(self,data,header):
        logging.debug("---------Send Data---------")
        logging.debug(data)
        dev_id=header.headers.get('device')
        qos=str(header.headers.get('qos')).strip()
        logging.debug(dev_id)
        if (self.dev_list.count(dev_id)!=0):
            logging.debug("Found details")
            send_json="{'e':"+data+",'bn':'urn:dev:id:"+dev_id+"'}"
            send_json=send_json.replace(" ","_")
            logging.debug(send_json)
            #Start timer here
            if (qos!=None):
                if (qos=='1'):
                    t=Timer(5,self.timeout,[dev_id,send_json,0])
                    self.timer_list[dev_id]=t
                    t.start()
            self.sendRf(dev_id,send_json)
        else:
            logging.debug("Data received for non existent Dev")
    
    def callback(self,ch,method,properties,body):
        self.sendMssgResolv(body,properties) 

    def sendRf(self,device,message):
        key=self.dev_mac[device]
        logging.debug(device+"-"+key)
        send_q[key].put(message)
    
    def timeout(self,dev,val,cnt):
        logging.debug("Message Timed Out: ",cnt)
        if (cnt<5):
            self.sendRf(dev,val)
            t=Timer(5,self.timeout,[dev,val,cnt+1])
            t.start()
            self.timer_list[dev]=t
        else:
            logging.debug("Max Retransmit Reached")
            message_amqp="Retransmit Error"
            properties_m=pika.BasicProperties(headers={'device':""+dev,'comm': ""+self.gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            self.channel.basic_publish(exchange='device', routing_key='', body=message_amqp, properties=properties_m)
            self.timer_list[dev].cancel()
            self.updateDevTime(dev,"Max Retransmit")
    
    def updateDev(self,dev_id,status):
        #ToDo update Date of Device
        self.datab.updateStat(dev_id,status)

    def updateDevTime(self,dev_id,status):
        #ToDo update Date of Device
        self.datab.updateDateStat(dev_id,status,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def scan(self):
        logging.debug("Scanning timeout")
        nearby_devices=bluetooth.discover_devices(lookup_names=True)
        logging.debug("found %d devices" %len(nearby_devices))
        for addr,name in nearby_devices:
            logging.debug(" %s - %s "% (addr,name))
            if name in self.find_devs:
                logging.debug("Attempting"+name+":"+addr+"port:"+str(self.port))
                try:
                    socket=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                    socket.connect((addr,port))
                    logging.debug('Connected to %s on port %s'%(name,port))
                    #port=port+1
                    socket.send('x')
                    socket.settimeout(0.1)
                    send_q[addr]=Queue.Queue(10)
                    receive_q[addr]=Queue.Queue(10)
                    bluet=self.BlueThread(name,socket,send_q[addr],receive_q[addr])
                    bluet.start()
                    threads[addr]=bluet
                except bluetooth.BluetoothError as error:
                    logging.error(error)
        if not exitFlag:
            mainTimer=Timer(300,self.scan)
            self.timer_list["main"]=mainTimer
            mainTimer.start()
	
    def init(self):

        self.message="";
        exitFlag = 0
        self.port=1

        self.gw_name=Config.get("Bluetooth","name")
        self.dev_list= []
        self.timer_list = {}
        self.find_devs = []
        self.dev_mac = {}
        logging.debug("Bluetooth Radio started: "+time.strftime('%X %x %Z'))
        
        #Create sql stuff and initialize
        self.find_devs=Config.get("Bluetooth","peers").split(',')
        #Get Database deviecs
        self.datab=database.Database(Config.get("couchDB","user"),Config.get("couchDB","pass"),'blue',Config.get("General","Gateway_Name"))
        value=self.datab.getAllDevs()
        for r in value:
            self.datab.updateStat(r,"Idle")

        #Queueu stuff
        exitFlag=0
        send_q = {}
        receive_q = {}
        threads = {}
        
        #AMQP Stuff
        logging.getLogger("pika").setLevel(logging.ERROR)
        credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
        parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
        self.connection = pika.BlockingConnection(parameters);

        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)

        #Server Socket 
        server_sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM )
        server_sock.bind(("",1))
        server_sock.listen(1)
        servT=self.ServerThread(server_sock)
        servT.start()
        threads["serv"]=servT


        mainTimer=Timer(300,self.scan)
        self.timer_list["main"]=mainTimer
        mainTimer.start()        
    
    def shutdown(self):
        exitFlag=1
        self.channel.close()
        self.connection.close()
        self.timer_list["main"].cancel()
        for key in self.timer_list:
            self.timer_list[key].cancel()
            
    def run(self):
        self.init()
        try:
            while True:
                for key in receive_q:
                    if not receive_q[key].empty():
                        message=receive_q[key].get()
                        self.handle_data(key,message)
                frame,header,body=self.channel.basic_get(queue=Config.get("Bluetooth","queue"),no_ack=False)
                if frame:
                    self.channel.basic_ack(frame.delivery_tag)
                    self.sendMssgResolv(body,header)
        except Exception,e:
            logging.error(e)
            self.shutdown()
            self.server_sock.close()
            logging.debug("Exiting Main Thread - Error")
        except KeyboardInterrupt:
            self.shutdown()
            self.server_sock.close()
            logging.debug("Exiting Main Thread - Keyboard")


if __name__ == "__main__":
	daemon = blue(PIDFILE)
	if len(sys.argv) == 2:

		if 'start' == sys.argv[1]:
			try:
				daemon.start()
			except:
				pass

		elif 'stop' == sys.argv[1]:
			print("Stopping ...")
			logging.debug("Driver Stopped")
			daemon.stop()

		elif 'restart' == sys.argv[1]:
			print( "Restaring ...")
			logging.debug("Driver Restarted")
			daemon.restart()

		elif 'status' == sys.argv[1]:
			try:
				pf = file(PIDFILE,'r')
				pid = int(pf.read().strip())
				pf.close()
			except IOError:
				pid = None
			except SystemExit:
				pid = None

			if pid:
				print( 'YourDaemon is running as pid %s' % pid)
			else:
				print( 'YourDaemon is not running.')

		else:
			print( "Unknown command")
			sys.exit(2)
			sys.exit(0)
	else:
		print( "usage: %s start|stop|restart|status" % sys.argv[0])
		sys.exit(2)

if __name__ == "__main2__":
    blue=blue()
    try:
        blue.run()
    except Exception , e:
        print(e)
        blue.shutdown()
        threads["serv"].close()
        logging.debug("Exiting Main Thread - Keyboard")
    except KeyboardInterrupt:
        blue.shutdown()
        threads["serv"].close()
        logging.debug("Exiting Main Thread - Keyboard")
