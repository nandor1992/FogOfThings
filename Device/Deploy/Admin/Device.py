#!/usr/bin/env python
import sqlite3
import os
import datetime
import couchdb

class Device:
    
    def __init__(self,user,passwd):
        self.user=user
        self.passwd=passwd
        self.couch=couchdb.Server('http://'+user+':'+passwd+'@127.0.0.1:5984/')
        self.admin_db=self.couch['admin']
        

    def getDevList(self,gw):
        device=[]
        look=self.admin_db.view('views/device')
        val=None
        for p in look[['device',gw]]:
            val=p.value;
        for db in val[0]:
            db2=self.couch[db]
            for d in db2:
                doc=db2[d]
                if (doc['_id']!='_design/views'):
                    device.append({"driver":val[1][val[0].index(db)],"id":doc['dev_id'],
                                "type":doc['dev_type'],"mac":doc['mac'],
                                "version":doc['version'],"date":doc['date'],
                                "status":doc['status']})
        return device
        
    

    def getSpecDevList(self,type_d,type_s,gw):
        device=[]
        look=self.admin_db.view('views/device')
        val=None
        for p in look[['device',gw]]:
            val=p.value;
        for db in val[0]:
            db2=self.couch[db]
            for d in db2:
                doc=db2[d]
                if (doc['_id']!='_design/views'):
                    if (doc['dev_type']==type_d and doc['status']==type_s):
                        device.append({"driver":val[1][val[0].index(db)],"id":doc['dev_id'],
                                "type":doc['dev_type'],"mac":doc['mac'],
                                "version":doc['version'],"date":doc['date'],
                                "status":doc['status']})
        return device
        


if __name__ == "__main__":
    d=Device("admin","hunter")
    #d.modifyDevStatus("ardu_rf24","OWaDMY9V","Idle")
    print(d.getDevList("Gateway_Work_2"))
    #print(d.getSensorList("ardu_rf24","OWaDMY9V"))
    print(d.getSpecDevList("ardUnoTemp","Idle","Gateway_Work_2"))
