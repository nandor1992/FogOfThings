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
            db.save(payload)
            return "ok"
        except Exception,e:
            print(e)
            return "Error "+str(e)

    def updateDeplFile(self,app,old,gw):
        doc=None
        db=self.couch['apps']
        look=db.view('views/app-name')
        for v in look[[app,old]]:
            doc=db[v.value[1]]
            doc['current_gateway']=gw
            db[doc.id]=doc
    
    def getDeployedApps(self,needs):
        havs=[]
        ##Add gw as constraint
        db=self.couch['apps']
        look=db.view('views/app-name')
        for need in needs:
            for p in look[['apps',self.gw]]:
                havs.append(p.value[0])
        return havs

    def getDeployFile(self,name,gw):
        doc=None
        db=self.couch['apps']
        look=db.view('views/app-name')
        for v in look[[name,gw]]:
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
    data2={'config_file': 'org.karaf.full_test', 'name': 'Test_App1', 'host_gateway': 'James_2344', 'region': [{'name': 'FirstRegion', 'key': 'BasicApiKey1'}], 'apps': [], 'cluster': 'Cluster_Jasmine_1529', 'resources': ['storage'], 'file': 'full_test_app-0.0.1-SNAPSHOT.jar', 'AppId': '697bbbe0e7f3d065ae4652d7100044af', 'device': {'AndroidPhoneT': ['ZOfxl5hv']}, 'config': {'name': 'Test_App1', 'dev_AndroidPhoneT': 'ZOfxl5hv', 'region': 'FirstRegion;BasicApiKey1', 'resources': 'storage', 'dev_message': 'Gcode:G01_X1_Y1_Z1', 'cloud': 'mqtt_conn1'}, 'cloud': ['mqtt_conn1'], 'current_gateway': 'James_2344'}
    res=Resource('admin','hunter','Vazquez_7663',data)
    #print(res.getDeployedApps(['Thermostat_App','Dummy_app']))
    print(res.saveDeployFile("Testing_App2",data2))
    #print(res.getDeployFile('Thermostat_App'))
    #print(res.checkDeviceDependency('ardUnoTemp'))
    #print(res.deleteDeployedFile('Thermostat_App2'))
    #print(res.getResourceQue('metadata'))
    #print(res.initializeRes("storage","test_app12"))
    #print(res.initializeRes('storage','Thermostat_App'))
    #print(res.deleteRes('storage','thermostat_app'))
