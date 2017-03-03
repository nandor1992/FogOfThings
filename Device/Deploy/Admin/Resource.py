#!/usr/bin/env python

import couchdb
import time
import ast

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
            if name in d[0]:
                return d[1]
        return None

    def initializeRes(self,res,app):
        if (res=="storage"):
            try:
                if "app_"+app.lower() in self.couch:
                    db=self.couch["app_"+app.lower()]
                else:
                    db=self.couch.create("app_"+app.lower())
                    while "app_"+app.lower() not in self.couch:
                        time.sleep(0.1)
                    db=self.couch["app_"+app.lower()]   
                    db.save({'_id':'_design/views','views':{'payload':{'map':'function (doc) {\n emit(doc.datetime,doc.payload);\n}'}},'language':'javascript'})          
            except Exception, e:
                try:
                    while "app_"+app.lower() not in self.couch:
                            time.sleep(0.1)
                    db=self.couch["app_"+app.lower()]
                    db.save({'_id':'_design/views','views':{'payload':{'map':'function (doc) {\n emit(doc.datetime,doc.payload);\n}'}},'language':'javascript'})          
                except Exception, e:
                    return "not ok"+str(e)
        return "ok"

    def deleteRes(self,res,app):
        if (res=="storage"):
            try:
                self.couch.delete("app_"+app.lower())
            except:
                return "ok"
        return "ok"

    def saveDeployFile(self,name,payload):
        #Save Gateway 
        db=self.couch['apps']
        try:
            ret=ast.literal_eval(payload)
            ret['gateway']=self.gw
            db.save(ret)
            return "ok"
        except Exception,e:
            return "Error"+str(e)

    def getDeployedApps(self,needs):
        havs=[]
        ##Add gw as constraint
        db=self.couch['apps']
        look=db.view('views/app-name')
        for need in needs:
            for p in look[['apps',self.gw]]:
                havs.append(p.value[0])
        return havs

    def getDeployFile(self,name):
        doc=None
        db=self.couch['apps']
        look=db.view('views/app-name')
        for v in look[[name,self.gw]]:
            doc=db[v.value[1]]
            del(doc['_id'])
            del(doc['_rev'])
            return doc
        return doc

    def deleteDeployedFile(self,name):
        db=self.couch['apps']
        look=db.view('views/app-name')
        for v in look[[name,self.gw]]:
            del(db[v.value[1]])
        return "ok"

    def checkDeviceDependency(self,d_type):
        pass
    

if __name__ == "__main__":
    data = [('metadata', 'res_metadata'), ('position', 'res_position'), ('storage', 'res_storage')]
    res=Resource('admin','hunter','Vazquez_7663',data)
    #print(res.getDeployedApps(['Thermostat_App','Dummy_app']))
    print(res.getDeployFile('Thermostat_App'))
    #print(res.checkDeviceDependency('ardUnoTemp'))
    #print(res.deleteDeployedFile('Thermostat_App2'))
    #print(res.getResourceQue('metadata'))
    #print(res.initializeRes("storage","test_app12"))
    #print(res.initializeRes('storage','Thermostat_App'))
    #print(res.deleteRes('storage','thermostat_app'))
