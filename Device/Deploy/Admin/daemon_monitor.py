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
import psutil
import multiprocessing
#Config Settings
Config=ConfigParser.ConfigParser()
conf_loc="/home/pi/FogOfThings/Device/config.ini"
Config.read(conf_loc)
PIDFILE="/home/pi/FogOfThings/Device/pid/admin.pid"
LOGFILE = Config.get("Log","location")+'/monitor.log'
logging.basicConfig(filename=LOGFILE,level=logging.DEBUG)
logging.getLogger("pika").setLevel(logging.ERROR)

#class admin():
class admin(Daemon):

    def on_request(self,ch, method, properties, body):
        logging.debug("-----Received Data from Monitor-----")
        ##logging.debug(body)
        response = self.resolveKaraf(ast.literal_eval(body))
        ques=self.getQueueMonitor()
        save={}
        save['gateway']=ques
        save['apps']=response
        cpu=psutil.cpu_percent()
        ram=psutil.virtual_memory()[2]
        load=os.getloadavg()[0]/multiprocessing.cpu_count()
        save['gateway']['processor']={'cpu':cpu,'load':load,'ram':ram}
        save['gateway']['storage']=self.reg.checkDatabForApp()
        #Save To Database
        save['date']=time.strftime("%Y-%m-%d %H:%M:%S")
        save['type']="General"
        save['Gateway']=Config.get("General","gateway_name")
        self.reg.saveMonitoring(save)
        logging.debug(save)
        ch.basic_ack(delivery_tag = method.delivery_tag)


    def resolveKaraf(self,body):
        keys=body['device'].keys()
        for key in keys:
            apps=self.reg.checkDevsApp(key)
            if len(apps)!=0:
                for app in apps:
                    if app in body['device']:
                        body['device'][app]=int(body['device'][app])+1
                    else:
                        body['device'][app]=1
                del(body['device'][key])
        return body

    
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
        return comm
        
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

if __name__ == "__main__":
    daemon = admin(PIDFILE)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            try:
                daemon.start()
            except:
                pass
        elif 'stop' == sys.argv[1]:
            print("Stopping ...")
            print("Driver Stopped")
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            print( "Restaring ...")
            print("Driver Restarted")
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
    admin=admin()
    try:
        #admin.init()
        #admin.getQueueMonitor()
        admin.run()
  #  except Exception , e:
       # logging.debug(e)
       # admin.shutdown()
       # logging.debug("Exiting Main Thread - Keyboard")
    except KeyboardInterrupt:
        admin.shutdown()
        logging.debug("Exiting Main Thread - Keyboard")
