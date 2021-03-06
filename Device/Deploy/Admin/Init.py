#!/usr/bin/env python
import paho.mqtt.client as mqtt
import datetime
import time
import pycurl
import os,sys
import couchdb
import ConfigParser
from StringIO import StringIO
class InitReq:
    def __init__(self,user,passw,address,port,gw_name):
        self.gw_name=gw_name ##Redo to random
        self.client = mqtt.Client(client_id="Temp_"+self.gw_name,clean_session=True);
        self.client.username_pw_set(user,passw)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(address,int(port) ,10)
        time.sleep(1)
        
    def on_connect(self, client, userdata, flags, rc ):
        client.subscribe("receive/"+self.gw_name,2)
        
    def on_message(self,client, userdata, msg):
        payload=(str(msg.payload));
        self.response=payload

    def register(self, data):
        self.response = None
        self.client.loop_read()
        (result,mid)=self.client.publish("receive/Cloud_Controller",payload=data,qos=1)
        while self.response==None:
            self.client.loop_read()
        self.close()
        return self.response
    
    def close(self):
        self.client.loop_stop()
        self.client.disconnect()

class Init:
    def __init__(self,r_user,r_pass,c_user,c_pass):
        self.c_user=c_user
        self.c_pass=c_pass
        self.r_user=r_user
        self.r_pass=r_pass
        self.couch=couchdb.Server('http://'+c_user+':'+c_pass+'@127.0.0.1:5984/')
        
    def initRabbitmq(self,fname):
        c=pycurl.Curl()
        if os.path.isfile(fname):
            c.setopt(c.URL,"http://localhost:15672/api/definitions")
            c.setopt(c.USERPWD,'%s:%s' %(self.r_user,self.r_pass))
            data = [("file",(c.FORM_FILE,fname))]        
            c.setopt(c.HTTPPOST,data)
            c.perform()
            status=c.getinfo(c.HTTP_CODE)
            c.close()
            if (status == 201):
                return "ok"
            else:
                return "error:"+str(status)
        else:
            return "error:File Not Found"

    def initCouchDB(self,queues):
        try:
            self.couch.create("_global_changes")
        except couchdb.PreconditionFailed:
            pass
        try:
            self.couch.create("_metadata")
        except couchdb.PreconditionFailed:
            pass
        try:        
            self.couch.create("_replicator")
        except couchdb.PreconditionFailed:
            pass
        try: 
            self.couch.create("_users")
        except couchdb.PreconditionFailed:
            pass
        try: 
            self.couch.create("monitoring")
        except couchdb.PreconditionFailed:
            pass
        try: 
            db=self.couch.create("admin")
            db.save({'_id':'_design/views',  'views': { "docs_by_type": {"map": "function (doc) {\n  emit(doc.type,doc._id);\n}" }},'language':'javascript'})                   
        except couchdb.PreconditionFailed:
            pass
        try: 
            db=self.couch.create("apps")
            db.save({'_id':'_design/views',  'views': { "app-name": {"map": "function (doc) {\n  emit([doc.name,doc.current_gateway],[doc.name,doc._id]);\n}" },"app_for_dev":{"map":"function(doc){\n for(var dev in doc.conn_devs){\n emit(doc.conn_devs[dev],doc.name);\n}\n}"} },'language':'javascript'})                   
        except couchdb.PreconditionFailed:
            pass
        try: 
            db=self.couch.create("monitoring")
            db.save({'_id':'_design/views',  'views': { "dates": {"map": "function (doc) {\n  emit(doc.date,doc._id);\n}" }},'language':'javascript'})                   
        except couchdb.PreconditionFailed:
            pass
        try: 
            print(queues)
            for q in queues:
                print(q)
                print(q[0])
                try:
                    db=self.couch.create(q[0])
                    db.save({'_id':'_design/views',  'views': { "device": {"map": "function (doc) {\n  emit([doc.mac,doc.dev_type,doc.version],[doc.dev_id,doc.gateway]);\n}" },
                        "doc": {"map": "function (doc) {\n  emit(doc.dev_id,doc._id);\n}"},"dev-gw": {"map": "function (doc) {\n  emit([doc.dev_id,doc.gateway],doc._id);\n}"}},'language':'javascript'})            
                except couchdb.PreconditionFailed:
                    pass
        except:
            return "error in DB"
        return "ok"
    
if __name__ == "__main__":
    #inir=InitReq("admin","hunter","10.0.0.134","1883","Test_Me")
    ini=Init("admin","hunter","admin","hunter")
    #data=[('blue', 'ardu_blue'), ('rf24', 'ardu_rf24'), ('rf434', 'atmega_rfa1')]
    Config=ConfigParser.ConfigParser()
    conf_loc="/home/pi/FogOfThings/Device/config.ini"
    Config.read(conf_loc)
    print(Config.items("DeviceQ"))
    print(ini.initCouchDB(Config.items("DeviceQ")))
    #print(ini.initRabbitmq("/home/pi/FogOfThings/Device/RabbitVersions/rabbit_bare.json"))
    #print(ini.initCouchDB(data))
    #print(inir.register("{'name':'Test_Gw1','request':'register','uuid':'TestUUIDGW1', \
    #'local_ip':'10.0.0.67','hw_addr':'b8:27:eb:c5:ed:e4','api_key':'ThisIsRandomAPIKey1234', \
    #'peers':[['b9:27:eb:c5:ed:e4','10.0.0.68']],'info':'Prity Random Gw info this will just be saved as is, might be usefull later'}"))
