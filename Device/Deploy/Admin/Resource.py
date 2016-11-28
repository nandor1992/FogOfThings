#!/usr/bin/env python

import couchdb

class Resource:

    def __init__(self,user,passwd,gw):
        self.name="resource"
        self.user=user
        self.passwd=passwd
        self.couch=couchdb.Server('http://'+user+':'+passwd+'@127.0.0.1:5984/')
        self.db=self.couch['admin']
        self.gw=gw
    def getResourceQue(self,name):
        device=[]
        look=self.db.view('views/resource')
        val2=None
        for p in look[['resource',self.gw]]:
            val=p.value;
            if name in val[0]:
                val2=val[1][val[0].index(name)]
        return val2

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
    res=Resource('admin','hunter','Gateway_Work_2')
    print(res.getResourceQue('storage'))
    print(res.initializeRes('storage','Thermostat_App'))
    #print(res.deleteRes('storage','thermostat_app'))
