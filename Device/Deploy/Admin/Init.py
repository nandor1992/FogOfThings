#!/usr/bin/env python
import paho.mqtt.client as mqtt
import datetime
import time
class Init:
    def __init__(self,user,passw,address,port,gw_name):
        self.gw_name=gw_name ##Redo to random
        self.client = mqtt.Client(client_id="Temp_"+self.gw_name,clean_session=True);
        self.client.username_pw_set(user,passw)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(address,int(port) ,10)
        time.sleep(1)
        
    def on_connect(self, client, userdata, flags, rc ):
        print("Connected with result code "+str(rc))
        client.subscribe("receive/"+self.gw_name,2)
        
    def on_message(self,client, userdata, msg):
        payload=(str(msg.payload));
        self.response=payload

    def register(self, data):
        self.response = None
        self.client.loop_read()
        (result,mid)=self.client.publish("receive/Cloud_Controller",payload=data,qos=1)
        print("Message Sent with result: "+str(result)+" Message Id: "+str(mid))
        ##loop until 
        while self.response==None:
            self.client.loop_read()
        self.close()
        return self.response
    
    def close(self):
        self.client.loop_stop()
        self.client.disconnect()

if __name__ == "__main__":
    ini=Init("admin","hunter","10.0.0.137","1883")
    print(ini.register("{'name':'Test_Gw1','request':'register','uuid':'TestUUIDGW1', \
    'local_ip':'10.0.0.67','hw_addr':'b8:27:eb:c5:ed:e4','api_key':'ThisIsRandomAPIKey1234', \
    'peers':[['b9:27:eb:c5:ed:e4','10.0.0.68']],'info':'Prity Random Gw info this will just be saved as is, might be usefull later'}"))
