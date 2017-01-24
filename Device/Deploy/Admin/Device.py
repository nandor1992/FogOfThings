#!/usr/bin/env python
import sqlite3
import os
import datetime
import couchdb

class Device:
    
    def __init__(self,user,passwd,queue):
        self.user=user
        self.passwd=passwd
        self.couch=couchdb.Server('http://'+user+':'+passwd+'@127.0.0.1:5984/')
        self.queue=queue

    def getDevList(self,gw):
        device=[]
        for p in self.queue:
            db2=self.couch[p[0]]
            for d in db2:
                doc=db2[d]
                if (doc['_id']!='_design/views'):
                    if gw==None  or gw==doc["gateway"]:
                        device.append({"driver":p[0],"id":doc['dev_id'],
                                "type":doc['dev_type'],"mac":doc['mac'],
                                "version":doc['version'],"date":doc['date'],
                                "status":doc['status']})
        return device
        
    

    def getSpecDevList(self,type_d,type_s,gw):
        device=[]
        for p in self.queue:
            db2=self.couch[p[0]]
            for d in db2:
                doc=db2[d]
                if (doc['_id']!='_design/views'):
                    if (gw==None  or gw==doc["gateway"]) and doc['dev_type']==type_d and doc['status']==type_s:
                        device.append({"driver":p[0],"id":doc['dev_id'],
                                "type":doc['dev_type'],"mac":doc['mac'],
                                "version":doc['version'],"date":doc['date'],
                                "status":doc['status']})
        return device        


if __name__ == "__main__":
    data=[('blue', 'ardu_blue'), ('rf24', 'ardu_rf24'), ('rf434', 'atmega_rfa1')]
    d=Device("admin","hunter",data)
    #d.modifyDevStatus("ardu_rf24","OWaDMY9V","Idle")
    #print(d.getDevList("Gateway_Work_2"))
    #print(d.getSensorList("ardu_rf24","OWaDMY9V"))
    print(d.getSpecDevList("ardUnoTemp","Idle",None))
