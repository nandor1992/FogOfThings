#!/usr/bin/env python

import couchdb

class Resource:
    map_databases = '''function(doc){
        emit(doc.type,[doc.res_name,doc.queue]);
        }'''
    def __init__(self,user,passwd):
        self.name="resource"
        self.user=user
        self.passwd=passwd
        self.couch=couchdb.Server('http://'+user+':'+passwd+'@127.0.0.1:5984/')
        self.db=self.couch['admin']

    def getResourceQue(self,name):
        device=[]
        look=self.db.query(self.map_databases)
        val2=None
        for p in look['resource']:
            val=p.value;
            if name in val[0]:
                val2=val[1][val[0].index(name)]
        return val2

    def initializeRes(self,res,app):
        if (res=="storage"):
            self.couch.create("app_"+app.lower())
        return "ok"

    def deleteRes(self,res,app):
        if (res=="storage"):
            self.couch.delete("app_"+app.lower())
        return "ok"

if __name__ == "__main__":
    res=Resource('admin','hunter')
    print(res.getResourceQue('storage'))
    res.initializeRes('storage','Thermostat_App')
    #res.deleteRes('storage','thermostat_app')
   # res.deleteRes('storage','app')
