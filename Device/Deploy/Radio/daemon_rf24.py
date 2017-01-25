#!/usr/bin/env python

#
# Example using Dynamic Payloads
# 
#  This is an example of how to use payloads of a varying (dynamic) size.
# 
# Modified to work from FogOf Thinggs and with Ini Fie
# Modified Driver to Work with CouchDB

from __future__ import print_function
from threading import Timer
import time
from RF24 import *
import RPi.GPIO as GPIO
import pika
import json
import datetime
import string
import random
import database
import os,sys
import ConfigParser
from daemon import Daemon
import logging
#Config Settings

PIDFILE="/home/pi/FogOfThings/Device/pid/rf24.pid"
LOGFILE = '/var/log/yourdaemon.log'

Config=ConfigParser.ConfigParser()
Config.read("/home/pi/FogOfThings/Device/config.ini")
LOGFILE = Config.get("Log","location")+'/rf24.log'
# Configure logging
logging.basicConfig(filename=LOGFILE,level=logging.DEBUG)

class rf24():
#class rf24(Daemon):

    def try_read_data(self,channel=0):
        if self.radio.available():
            while self.radio.available():
                length = self.radio.getDynamicPayloadSize()
                payload = self.radio.read(length).decode()
                payload = payload[:31]
                self.message=self.message+payload.strip()
                #logging.debug(message)
                if (self.message[-1]=='}' and self.message[0:1]=='{'):
                    logging.debug("--------Message Received on CH=1-------")
                    self.handle_data(self.message)
                    self.message=""
                elif self.message[0:1]!='{':
                    logging.debug("Wrong Start to msg delete rest")
                    self.message=""
                elif len(self.message)>300:
                    logging.debug("length error")
                    self.message=""
            #print(message)
            #print('Got payload size={} value="{}"'.format(len, receive_payload.decode('utf-8')))

    
    def sendRf(self,message):
        self.radio.stopListening()
        self.radio.write(message[:31].encode())
        while len(message)>31:
            message=message[31:]
            self.radio.write(message[:31].encode())
        self.radio.startListening()
              

    def handle_data(self,data):
        data=data.replace("'",'"')
        logging.debug(data)
        try:
            my_json=json.loads(data);
        #Check if available in database if yes give it old id of not new one
        #and save to db when given, parse messages to see data as well
            if len(my_json["bn"][1])>=3:
                logging.debug("Register data received")
                self.registerResolv(my_json)
            else:
                logging.debug("Normal data received")
                self.messageResolv(my_json)
        except ValueError:
            logging.debug("Value Erro, probs something stupid happened")
        except IndexError:
            logging.debug("Index Error, probs something stupid happened")
    
    def messageResolv(self,my_json):
        dev_id=my_json.get("bn")[11:]
        dev_id=dev_id[:8]
        logging.debug(dev_id)
        if (self.dev_list.count(dev_id)!=0):
            message_amqp=json.dumps(my_json["e"])
            message_amqp=message_amqp.replace('"',"'")
            message_amqp=message_amqp.replace(' ','')
            logging.debug(message_amqp)
            if  dev_id in self.timer_list:
                self.timer_list[dev_id].cancel()
            properties_m=pika.BasicProperties(headers={'device':""+dev_id,'comm': ""+self.gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            self.channel.basic_publish(exchange='device', routing_key='', body=message_amqp, properties=properties_m)
            self.updateDevTime(dev_id,"Available")
        else:
            ##Check if Device listed as belonging to this GW and if yes, add to devList and send msg
            if self.datab.checkDevGw(dev_id):
                message_amqp=json.dumps(my_json["e"])
                message_amqp=message_amqp.replace('"',"'")
                message_amqp=message_amqp.replace(' ','')
                properties_m=pika.BasicProperties(headers={'device':""+dev_id,'comm': ""+self.gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                self.channel.basic_publish(exchange='device', routing_key='', body=message_amqp, properties=properties_m)
                self.updateDevTime(dev_id,"Available")
                self.dev_list.append(dev_id)
            else:
                logging.debug("No details found - not forwarding")
    
    def registerResolv(self,my_json):
        trans=my_json.get("bn",{})[2]
        my_uuid=self.resolv_dev(my_json)
        trans=trans[9:]
        data="{'bn':['trans:id:"+trans+"','urn:dev:id:"+my_uuid+"']}"
        self.sendRf(data);

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
            logging.debug("New UUID="+str(rand_uuid))
            sense=[]
            for sens in my_json["e"]:
                sense.append({sens["n"]:sens["u"]})
            self.datab.addDevice(rand_uuid,type_d,mac_d,ver_d,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'Available',sense)
            self.dev_list.append(rand_uuid)
        return rand_uuid
    
    def sendMssgResolv(self,data,header):
        logging.debug("---------Send Data---------")
        logging.debug(data)
        dev_id=str(header.headers.get('device')).strip()
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
            self.sendRf(send_json)
        else:
            ##Check if Device listed as belonging to this GW and if yes, add to devList and send msg
            if self.datab.checkDevGw(dev_id):
                logging.debug("Pre-Existing Device")
                send_json="{'e':"+data+",'bn':'urn:dev:id:"+dev_id+"'}"
                send_json=send_json.replace(" ","_")
                logging.debug(send_json)
                #Start timer here
                if (qos!=None):
                    if (qos=='1'):
                        t=Timer(5,self.timeout,[dev_id,send_json,0])
                        self.timer_list[dev_id]=t
                        t.start()
                self.sendRf(send_json)
            else:
                logging.debug("Data received for non existent Dev")
    
    def callback(self,ch,method,properties,body):
        self.sendMssgResolv(body,properties) 


    def timeout(self,dev,val,cnt):
        logging.debug("Message Timed Out: "+str(cnt))
        if (cnt<5):
            self.sendRf(val)
            t=Timer(5,self.timeout,[dev,val,cnt+1])
            t.start()
            self.timer_list[dev]=t
            self.message="";
        else:
            logging.debug("Max Retransmit Reached")
            message_amqp="[{'Retransmit Error'}]"
            properties_m=pika.BasicProperties(headers={'device':""+dev,'comm': ""+self.gw_name,'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            self.channel.basic_publish(exchange='device', routing_key='', body=message_amqp, properties=properties_m)
            self.timer_list[dev].cancel()
            self.updateDevTime(dev,"Max Retransmit")

    def resetTimeout(self):
        self.sendRf("{'e':'This_is_a_test'}")
        self.t_reset=Timer(90,self.resetTimeout)
        self.t_reset.start()
        sys.stdout.flush()
        
    def updateDev(self,dev_id,status):
        #ToDo update Date of Device
        self.datab.updateStat(dev_id,status)

    def updateDevTime(self,dev_id,status):
        #ToDo update Date of Device
        self.datab.updateDateStat(dev_id,status,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def init(self):
        ##Initial Config Stuff

        irq_gpio_pin = 25 ##22 maybe
        self.radio = RF24(RPI_V2_GPIO_P1_15, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ)
        self.message="";

           
        pipes = [Config.get("RF24","pipe_write"),Config.get("RF24","pipe_read")]
        self.gw_name=Config.get("RF24","name")
        self.gw=Config.get("General","gateway_name")
        self.dev_list= []
        self.timer_list = {}

        logging.debug("RF24 Radio started: "+time.strftime('%X %x %Z'))

        self.radio.begin()
        self.radio.enableDynamicPayloads()
        self.radio.setPALevel(RF24_PA_MAX);
        self.radio.setRetries(5,15);

        if irq_gpio_pin is not None:
        # set up callback for irq pin
            #GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(irq_gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(irq_gpio_pin, GPIO.FALLING, callback=self.try_read_data)

            self.radio.openWritingPipe(pipes[0])
            self.radio.openReadingPipe(1,pipes[1])
            self.radio.startListening()

        #Get Database deviecs
        self.datab=database.Database(Config.get("couchDB","user"),Config.get("couchDB","pass"),'rf24',Config.get("General","Gateway_Name"))
        value=self.datab.getAllDevs()
        for r in value:
            self.datab.updateStat(r,"Idle")
        sys.stdout.flush()
        #AMQP Stuff
        logging.getLogger("pika").setLevel(logging.ERROR)
        credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
        parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
        self.connection = pika.BlockingConnection(parameters);

        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.callback,queue=Config.get("RF24","queue"),no_ack=True)


        #Timer Stuff
        self.t_reset=Timer(90,self.resetTimeout)
        self.t_reset.start()
        
    def run(self):
        #Main Loop of system
        self.init()
        while(1):
            try:
                self.channel.start_consuming()     
            except Exception, e:
                logging.error(e)
                self.radio.stopListening()
                self.channel.close()
                self.connection.close()
                self.t_reset.cancel()
                logging.debug("Exiting Main Thread")
                sys.exit(2)

if __name__ == "__main2__":
	daemon = rf24(PIDFILE)
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
    rf=rf24()
    try:
        rf.run()    
    except Exception, e:
        logging.error(e)
        self.radio.stopListening()
        self.channel.close()
        self.connection.close()
        self.t_reset.cancel()
        logging.debug("Exiting Main Thread")
        sys.exit(2)   
            
