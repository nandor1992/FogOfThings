#!/usr/bin/env python

import pika
import time
import paho.mqtt.client as mqtt
import json
import os,sys
import ConfigParser
from daemon import Daemon
import logging
import time
import urllib
import datetime
#Config Settings
PIDFILE2="/home/pi/FogOfThings/Device/pid/m2a.pid"
Config=ConfigParser.ConfigParser()
Config.read("/home/pi/FogOfThings/Device/config.ini")
LOGFILE = Config.get("Log","location")+'/mqtt_to_amqp.log'
logging.basicConfig(filename=LOGFILE,level=logging.DEBUG)
logging.getLogger("pika").setLevel(logging.ERROR)
#Moore_1850
#class up():
class up(Daemon):

    def callback(self,ch,method,properties,body):
        logging.debug("[x] Received %r"%body)
        admin=False
        try:
            try:
                my_json=json.loads('{"payload":'+body+'}')
            except ValueError:
                logging.debug("Non json payload")
                body=body.replace('"',"'")
                my_json=json.loads('{"payload":"'+body+'"}')
            for names in properties.headers:
                if names=="source":
                    if properties.headers.get(names)=="Cloud_Controller":
                        admin=True
                temp={names:properties.headers.get(names)}
                my_json.update(temp)
            data=json.dumps(my_json)
            logging.debug(data)
            self.client.reconnect()
            if admin:
                dest="receive/Cloud_Controller" 
            else:
                dest="send/"+self.clientId
            (result,mid)=self.client.publish(dest,payload=data,qos=1)
            while result!=mqtt.MQTT_ERR_SUCCESS:
                logging.debug("MQTT Disconnected "+time.strftime('%X %x %Z')+ ", Reconnecting")
                self.client.reconnect()
                (result,mid)=self.client.publish(dest,payload=data,qos=1)
            logging.debug("Message Sent with result: "+str(result)+" Message Id: "+str(mid))            
        except (ValueError, TypeError) as e:
            logging.debug("Nor Json or valid string data")

    def init(self):
        self.clientId=Config.get("General","Gateway_Name")
        self.conn_name=Config.get("Mqtt1","name")

        credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
        parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
        self.connection = pika.BlockingConnection(parameters);

        self.channel = self.connection.channel()

        self.client = mqtt.Client(client_id=self.clientId+"_Send",clean_session=True);
        self.client.username_pw_set(Config.get("Mqtt1","user"),Config.get("Mqtt1","pass"))
        self.client.connect(Config.get("Mqtt1","address"),int(Config.get("Mqtt1","port")) ,10)

        logging.debug("Broker started: "+time.strftime('%X %x %Z'))
        logging.debug(' [*] Waiting for messages. To exit press CTRL+C')

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.callback,queue=self.conn_name,no_ack=True)

    def run(self):
        self.init()
        try:
           self.channel.start_consuming()
        except Exception,e:
            logging.error(e)
            self.client.disconnect()
            self.connection.close()
            logging.debug("Exiting Main Thread - Error")
        except KeyboardInterrupt:
            self.client.disconnect()
            self.connection.close()
            logging.debug("Exiting Main Thread - Keyboard")
    def shutdown(self):
        self.channel.close()
        self.connection.close()
        self.client.disconnect()
            
#class down():
class down(Daemon):

    def on_connect(self,client, userdata,flags, rc):
        logging.debug("Connected with result code "+str(rc))
        client.subscribe("receive/"+self.clientId,2)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self,client, userdata, msg):
        logging.debug("------Received Message-------")
        logging.debug("Message: "+msg.topic+" "+str(msg.payload)[1:-1])
        try:
            payload=(str(msg.payload));
            payload=payload.replace('\n', '').replace('\r', '')
            logging.debug(payload)
            my_json=json.loads(payload);
            logging.debug(json.dumps(my_json,indent=1,sort_keys=True))
            headers={'cloud':self.conn_name}
            for item in my_json:
                if (item!="payload"):
                    headers.update({item:my_json[item]})
            logging.debug(headers)
            properties_m=pika.BasicProperties(headers=headers)
            payload=json.dumps(my_json["payload"])
            logging.debug(payload)
            if ("device" in my_json) or ("dev_type" in my_json):
                logging.debug("Device message")
                retr=False
                while retr==False:
                    retr=self.publish('device',payload,properties_m)
            else:
                logging.debug("Other message")
                payload=payload[1:-1]
                retr=False
                while retr==False:
                    retr=self.publish('app',payload,properties_m)
            #channel.basic_publish(exchange='',routing_key='test_queue',body=msg.payload)
        except (ValueError,TypeError) as e:
            logging.debug("Value Erro, probs something stupid happened")

    def publish(self,route,body,properties):
        try:
            self.channel.basic_publish(exchange='cloud', routing_key=route, body=body,properties=properties)
            return True
        except pika.exceptions.ConnectionClosed:
            logging.debug("Pika Disconnected "+time.strftime('%X %x %Z')+ ", Reconnecting")
            self.connection = pika.BlockingConnection(self.parameters);
            self.channel=self.connection.channel()
            return False
    
    def on_disconnect(self,client,userdata,rc):
        if rc!=0:
            logging.debug("Unexpected Disconnect "+time.strftime('%X %x %Z')+ " Reconnecting")
           #  client.reconnect()
            self.client.loop_stop()
            self.client.disconnect()
            self.client.reinitialise()
            loop=0
            while loop==0:
                try:
                    self.client = mqtt.Client(client_id=""+clientId+"_Receive",clean_session=True);
                    self.client.username_pw_set(Config.get("Mqtt1","user"),Config.get("Mqtt1","pass"))
                    self.client.on_connect = self.on_connect
                    self.client.on_message = self.on_message
                    self.client.on_disconnect = self.on_disconnect
                    self.client.connect(Config.get("Mqtt1","address"),int(Config.get("Mqtt1","port")) ,10)
                    self.client.loop_forever(timeout=1.0, max_packets=1,retry_first_connection=False)
                    loop=1
                except:
                    logging.debug("Exception hit at mqtt reconnect")
                    time.sleep(5)
            
        else:
            logging.debug("Expected Disconnect")

    def init(self):
        self.clientId=Config.get("General","Gateway_Name")
        self.conn_name=Config.get("Mqtt1","name")
        logging.debug("Starting New Session at "+time.strftime('%X %x %Z')) 
        self.client = mqtt.Client(client_id=self.clientId+"_Receive",clean_session=True);
        self.client.username_pw_set(Config.get("Mqtt1","user"),Config.get("Mqtt1","pass"))
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.connect(Config.get("Mqtt1","address"),int(Config.get("Mqtt1","port")) ,10)

        credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
        self.parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
        self.connection = pika.BlockingConnection(self.parameters);
        self.channel = self.connection.channel()
    
    def run(self):
        self.init()
        try:
            self.client.loop_forever(timeout=1.0, max_packets=1,retry_first_connection=False)
        except Exception,e:
            logging.error(e)
            self.shutdown()
            logging.debug("Exiting Main Thread - Error")
        except KeyboardInterrupt:
            self.shutdown()
            logging.debug("Exiting Main Thread - Keyboard")

    def shutdown(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.connection.close()

if __name__ == "__main__":
    daemon2 = down(PIDFILE2)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            try:
                daemon2.start()
            except:
                pass
        elif 'stop' == sys.argv[1]:
            print("Stopping ...")
            logging.debug("Driver Stopped")
            daemon2.stop()
        elif 'restart' == sys.argv[1]:
            print( "Restaring ...")
            logging.debug("Driver Restarted")
            daemon2.restart()
        elif 'status' == sys.argv[1]:
            try:
                pf2 = file(PIDFILE2,'r')
                pid2 = int(pf2.read().strip())
                pf2.close()
            except IOError:
                pid2 = None
            except SystemExit:
                pid2 = None

            if pid2:
                print( 'YourDaemon is running as pid %s' % pid2)
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
    down=down()
    try:
        down.run()
        #down.run()
    except Exception , e:
        print(e)
        down.shutdown()
        logging.debug("Exiting Main Thread - Keyboard")
    except KeyboardInterrupt:
        down.shutdown()
        logging.debug("Exiting Main Thread - Keyboard")
