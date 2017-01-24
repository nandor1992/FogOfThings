#!/usr/bin/env python

import couchdb

class Resource:

    def __init__(self,user,passwd,gw,queue):
        self.name="resource"
        self.user=user
        self.passwd=passwd
        self.couch=couchdb.Server('http://'+user+':'+passwd+'@127.0.0.1:5984/')
        self.queue=queue
        self.gw=gw

    def getResourceQue(self,name):
        for d in self.queue:
            print(d)
            if name in d[0]:
                return d[1]
        return None

    def initializeRes(self,res,app):
        if (res=="storage"):
            try:
                db=self.couch.create("app_"+app.lower())
                db.save({'_id':'_design/views','views':{'payload':{'map':'function (doc) {\n emit(doc.datetime,doc.payload);\n}'}},'language':'javascript'})            
            except:
                return "ok"
        return "ok"

    def deleteRes(self,res,app):
        if (res=="storage"):
            try:
                self.couch.delete("app_"+app.lower())
            except:
                return "ok"
        return "ok"

if __name__ == "__main__":
    data = [('metadata', 'res_metadata'), ('position', 'res_position'), ('storage', 'res_storage')]
    res=Resource('admin','hunter','Gateway_Work_2',data)
    print(res.getResourceQue('metadata'))
    #print(res.initializeRes('storage','Thermostat_App'))
    #print(res.deleteRes('storage','thermostat_app'))
