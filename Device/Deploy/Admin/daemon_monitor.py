#!/usr/bin/env python
import pika
import datetime
import Route
import Karaf
import Device
import Resource
import json
import time
import os,sys
import ConfigParser
import Region
import ast
import random
from string import ascii_letters,digits
from Init import Init,InitReq
from daemon import Daemon
import logging
#Config Settings
Config=ConfigParser.ConfigParser()
conf_loc="/home/pi/FogOfThings/Device/config.ini"
Config.read(conf_loc)
PIDFILE="/home/pi/FogOfThings/Device/pid/admin.pid"
LOGFILE = Config.get("Log","location")+'/monitor.log'
logging.basicConfig(filename=LOGFILE,level=logging.DEBUG)
logging.getLogger("pika").setLevel(logging.ERROR)

class admin():
#class admin(Daemon):

    def on_request(self,ch, method, properties, body):
        monitor=properties.headers.get("monitor")
        if (monitor!=None):
            logging.debug("-----Received Data from Monitor-----")
            response = self.resolve(body)
            logging.debug(self.getQueueMonitor())
            logging.debug(response)
        else:
            logging.debug("Missing component")
        ch.basic_ack(delivery_tag = method.delivery_tag)

    def getQueueMonitor(self):
        #Initilizing Comm
        comm={}
        comm['cloud']={}
        comm['apps']={}
        comm['federation']={}
        #Cloud
        cloud=self.reg.getExchangeInfo("cloud")
        for element in cloud:
            curr_queue="cloud"
            queue=self.resolveQue(element)
            if queue in comm[curr_queue]:
                comm[curr_queue][queue]=comm[curr_queue][queue]+cloud[element]
            else:
                comm[curr_queue][queue]=cloud[element]
            if queue in ['cloud','apps','federation']:
                if curr_queue in comm[queue]:
                    comm[queue][curr_queue]=comm[queue][curr_queue]+cloud[element]
                else:
                    comm[queue][curr_queue]=cloud[element]
        print(cloud)
        print(comm)
        #Device   
        dev=self.reg.getExchangeInfo("device")
        for element in dev:
            curr_queue="device"
            queue=self.resolveQue(element)
            if queue in ['cloud','apps','federation']:
                if curr_queue in comm[queue]:
                    comm[queue][curr_queue]=comm[queue][curr_queue]+dev[element]
                else:
                    comm[queue][curr_queue]=dev[element]
        print(dev)
        print(comm)

        #Region
        reg=self.reg.getExchangeInfo("region")
        for element in reg:
            curr_queue="region"
            queue=self.resolveQue(element)
            if queue in ['cloud','apps','federation']:
                if curr_queue in comm[queue]:
                    comm[queue][curr_queue]=comm[queue][curr_queue]+reg[element]
                else:
                    comm[queue][curr_queue]=reg[element]
        print(reg)
        print(comm)        
        #Apps
        apps=self.reg.getExchangeInfo("apps")
        cloud=self.reg.getExchangeInfo("cloud")
        for element in apps:
            curr_queue="apps"
            queue=self.resolveQue(element)
            if queue in comm[curr_queue]:
                comm[curr_queue][queue]=comm[curr_queue][queue]+apps[element]
            else:
                comm[curr_queue][queue]=apps[element]
            if queue in ['cloud','apps','federation']:
                if curr_queue in comm[queue]:
                    comm[queue][curr_queue]=comm[queue][curr_queue]+apps[element]
                else:
                    comm[queue][curr_queue]=apps[element]
        print(apps)
        print(comm)
        #Do federation Next
        #Federation Me
        fed=self.reg.getExchangeInfo("federation."+self.controller_name)
        cloud=self.reg.getExchangeInfo("cloud")
        for element in fed:
            curr_queue="federation"
            queue=self.resolveQue(element)
            if queue in comm[curr_queue]:
                comm[curr_queue][queue]=comm[curr_queue][queue]+fed[element]
            else:
                comm[curr_queue][queue]=fed[element]
            if queue in ['cloud','apps','federation']:
                if curr_queue in comm[queue]:
                    comm[queue][curr_queue]=comm[queue][curr_queue]+fed[element]
                else:
                    comm[queue][curr_queue]=fed[element]
        print(fed)
        print("Results:")
        print(comm)
    
    def resolveQue(self,queue):
        #ToDo - Make this work dynamically
        drivers=['ardu_blue','ardu_rf24','ardu_xbee','atmega_rfa1']
        cloud=['mqtt_conn1','mqtt_conn2']
        if queue=="karaf_app":
            return "apps"
        elif queue[:4]=="res_":
            return "resource"
        elif queue[:4]=="reg_":
            return "region"
        elif queue in drivers:
            return "device"
        elif queue in cloud:
            return "cloud"
        elif queue[:10]=="federation":
            return "federation"
        else:
            return "other"
        pass
    def init(self):
        credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
        parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
        self.connection = pika.BlockingConnection(parameters);
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)        
        self.channel.basic_consume(self.on_request, queue="monitor")
        
        self.reg=Region.Region(Config.get("Amqp","user"),Config.get("Amqp","pass"),Config.get("Amqp","virt"),Config.get("couchDB","user"),Config.get("couchDB","pass")) 
        self.controller_name= Config.get("General","Gateway_Name")
        
    def shutdown(self):
        self.channel.stop_consuming()
        self.channel.close()
        self.connection.close()

    def run(self):
        self.init()
        try:
            logging.debug("Awaiting Requests!")
            self.channel.start_consuming()
       # except Exception,e:
         #   logging.error(e)
          #  self.shutdown()
         #   logging.debug("Exiting Main Thread - Error")
        except KeyboardInterrupt:
            self.shutdown()
            logging.debug("Exiting Main Thread - Keyboard")

if __name__ == "__main_2_":
    daemon = admin(PIDFILE)
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

if __name__ == "__main__":
    admin=admin()
    try:
        admin.init()
        admin.getQueueMonitor()
        #admin.run()
  #  except Exception , e:
       # logging.debug(e)
       # admin.shutdown()
       # logging.debug("Exiting Main Thread - Keyboard")
    except KeyboardInterrupt:
        admin.shutdown()
        logging.debug("Exiting Main Thread - Keyboard")