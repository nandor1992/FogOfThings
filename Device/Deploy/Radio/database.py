#!/usr/bin/python

import datetime
import couchdb

class Database:
    def __init__(self,user,passwd,db,gateway):
        self.user=user
        self.passwd=passwd
        self.couch=couchdb.Server('http://'+user+':'+passwd+'@127.0.0.1:5984/')
        self.db=self.couch[db]
        self.gateway=gateway

    def lookupDev(self,mac,dev_type,ver):
        #Look for Device based on mac + type + version
        #Return dev_id if found, if not null
        look=self.db.view('views/device')
        res=None
        for p in look[[mac,dev_type,ver]]:
            res=p.value[0]
        return res
        
    def getAllDevs(self):
        look=self.db.view('views/device')
        res=[]
        for p in look:
            if p.value[1]==self.gateway:
                res.append(p.value[0])
        return res
    
    def addDevice(self,rand,dev_type,mac,ver,date,status,sensors):
        #Add device based on these, sensors comes as formatted dict list
        #no return neccesary
        self.db.save({'dev_id': rand,'dev_type': dev_type,'mac': mac,'version': ver,'date': date,'status': status,'sensors':sensors,'gateway':self.gateway})

    def updateStat(self,dev_id,state):
        #Update state of only this dev id
        #need view to find unique id of dev_id
        look=self.db.view('views/doc')
        res=None
        for p in look[dev_id]:
            res=p.value
        doc=self.db[res]
        doc['status']=state
        doc['gateway']=self.gateway
        self.db[doc.id]=doc

    def updateDateStat(self,dev_id,state,date):
        #use previeous View just add modify date
        look=self.db.view('views/doc')
        res=None
        for p in look[dev_id]:
            res=p.value
        doc=self.db[res]
        doc['status']=state
        doc['date']=date
        doc['gateway']=self.gateway
        self.db[doc.id]=doc

        
if __name__ == "__main__":
    db1=Database('admin','hunter','rf24',"Gateway_Work_2")
    print(db1.lookupDev('123mac2me56','ardUnoTemp','1'))
    print(db1.getAllDevs())
    #db1.updateStat('OWaDMY9V','Idle')
    #db1.addDevice('OWADMAA','ard_test','newMAc2',2,'2016-11-12 18:06:51','Available',[{'test':'one'},{'test2':'two'}])
