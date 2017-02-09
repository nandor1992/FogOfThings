#!/usr/bin/python

import datetime
import couchdb

class Database:
    map_lookup = '''function(doc){
        emit([doc.mac,doc.dev_type,doc.version],[doc.dev_id]);
        }'''
    map_id = '''function(doc){
        emit(doc.dev_id,doc._id);
        }'''''
    
    def __init__(self,user,passwd,db):
        self.user=user
        self.passwd=passwd
        self.couch=couchdb.Server('http://'+user+':'+passwd+'@127.0.0.1:5984/')
        self.db=self.couch[db]

    def lookupDev(self,mac,dev_type,ver):
        #Look for Device based on mac + type + version
        #Return dev_id if found, if not null
        look=self.db.query(self.map_lookup)
        res=None
        for p in look[[mac,dev_type,ver]]:
            res=p.value
        return res
        
    def getAllDevs(self):
        look=self.db.query(self.map_lookup)
        res=[]
        for p in look:
            res.append(p.value[0])
        return res
    
    def addDevice(self,rand,dev_type,mac,ver,date,status,sensors):
        #Add device based on these, sensors comes as formatted dict list
        #no return neccesary
        self.db.save({'dev_id': rand,'dev_type': dev_type,'mac': mac,'version': ver,'date': date,'status': status,'sensors':sensors})

    def updateStat(self,dev_id,state):
        #Update state of only this dev id
        #need view to find unique id of dev_id
        look=self.db.query(self.map_id)
        res=None
        for p in look[dev_id]:
            res=p.value
        doc=self.db[res]
        doc['status']=state
        self.db[doc.id]=doc

    def updateDateStat(self,dev_id,state,date):
        #use previeous View just add modify date
        look=self.db.query(self.map_id)
        res=None
        for p in look[dev_id]:
            res=p.value
        doc=self.db[res]
        doc['status']=state
        doc['date']=date
        self.db[doc.id]=doc

        
if __name__ == "__main__":
    db1=Database('admin','hunter','rf24')
    #print(db1.lookupDev('123mac2me56','ardUnoTemp','1')[0])
    #print(db1.getAllDevs())
    #db1.updateStat('OWaDMY9V','Idle')
    #db1.addDevice('OWADMAA','ard_tedt','newMAc2',2,'2016-11-12 18:06:51','Available',[{'test':'one'},{'test2':'two'}])
