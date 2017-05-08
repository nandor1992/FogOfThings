#!/usr/bin/env/python
import pycurl
from StringIO import StringIO
import os, sys
import json
class Karaf:
    def __init__(self,user,password,repo,location,conf_loc,apache_loc):
        self.user=user
        self.password=password
        self.repo=repo
        self.conf=conf_loc
        self.loc=location
        self.apach=apache_loc+"etc/"

    def getBundleInfo(self,id):
        buffer=StringIO()
        status={}
        c=pycurl.Curl()
        c.setopt(c.URL,"http://localhost:8181/system/console/bundles/"+str(id)+".json")
        c.setopt(c.WRITEDATA,buffer)
        c.setopt(c.USERPWD,'%s:%s' %(self.user,self.password))
        c.perform()
        c.close()
        body = buffer.getvalue()
        my_json=json.loads(body)
        status["state"]=str(my_json["data"][0]["state"])
        status["id"]=str(my_json["data"][0]["id"])
        return status

    def getBundleId(self,name):
        buffer=StringIO()
        c=pycurl.Curl()
        c.setopt(c.URL,"http://localhost:8181/system/console/bundles/.json")
        c.setopt(c.WRITEDATA,buffer)
        c.setopt(c.USERPWD,'%s:%s' %(self.user,self.password))
        c.perform()
        c.close()
        body = buffer.getvalue()
        my_json=None
        my_json=json.loads(body);
        id =0
        for item in my_json["data"]:
            symb=str(item["symbolicName"])
            length=len(symb)
            if symb==name[:length]:
                id =item["id"]
        if id==0:
            return "error:Not Found"
        else:
            return id
       
    def verifyBundleExists(self,fname):
        if os.path.isfile(""+self.loc+fname):
            return "ok"
        else:
            return "Not Found"

    def deployBundle(self,fname):
        file_loc=fname
        c=pycurl.Curl()
        if os.path.isfile(""+self.loc+fname):
            c.setopt(c.URL,"http://localhost:8181/system/console/bundles")
            c.setopt(c.USERPWD,'%s:%s' %(self.user,self.password))
            data = [ ("action","install"),("bundlestartlevel","80"),
                     ("bundlefile",(c.FORM_FILE,""+self.loc+fname))]        
            c.setopt(c.HTTPPOST,data)
            c.perform()
            status=c.getinfo(c.HTTP_CODE)
            c.close()
            if (status == 200 or status == 302):
                return "ok"
            else:
                return "error:"+str(status)
        else:
            return "error:File Not Found"

    def startBundle(self,id):
        c=pycurl.Curl()
        c.setopt(c.URL,"http://localhost:8181/system/console/bundles/"+str(id))
        c.setopt(c.USERPWD,'%s:%s' %(self.user,self.password))
        data = [ ("action","start")]        
        c.setopt(c.HTTPPOST,data)
        c.perform()
        status=c.getinfo(c.HTTP_CODE)
        c.close()
        if (status == 200 or status == 302):
            return "ok"
        else:
            return "error:"+str(status)

    def stopBundle(self,id):
        c=pycurl.Curl()
        c.setopt(c.URL,"http://localhost:8181/system/console/bundles/"+str(id))
        c.setopt(c.USERPWD,'%s:%s' %(self.user,self.password))
        data = [ ("action","stop")]        
        c.setopt(c.HTTPPOST,data)
        c.perform()
        status=c.getinfo(c.HTTP_CODE)
        c.close()
        if (status == 200 or status == 302):
            return "ok"
        else:
            return "error:"+str(status)

    def delBundle(self,id):
        c=pycurl.Curl()
        c.setopt(c.URL,"http://localhost:8181/system/console/bundles/"+str(id))
        c.setopt(c.USERPWD,'%s:%s' %(self.user,self.password))
        data = [ ("action","uninstall")]        
        c.setopt(c.HTTPPOST,data)
        c.perform()
        status=c.getinfo(c.HTTP_CODE)

        c.close()
        if (status == 200 or status == 302):
            return "ok"
        else:
            return "error:"+str(status)

    def getApp(self,uuid,filename):
        buffer=StringIO()
        c1=pycurl.Curl()
        url="http://10.0.0.134:5984/apps/"+uuid+"/"+filename
        c1.setopt(c1.URL,url)
        c1.setopt(c1.WRITEDATA,buffer)
        c1.perform()
        c1.close()
        if buffer.len>100:
            fp=open(self.loc+filename,"wb")
            fp.write(buffer.getvalue())
            fp.close()
            return "ok"
        else:
            return "error"


    def createConfig(self,fname,values):
        fp=open(self.apach+fname+".cfg","w")
        for key in values:
            fp.write(key+'\n')           
        fp.close()
        return "ok"

    
    def modifyConfig(self,fname,param,value):
        contents=open(self.apach+fname+".cfg","r").read()
        lines=contents.split('\n')
        for line in lines:
            if (line.strip()!=""):
                comp=line.split('=')
                if comp[0].strip()==param:
                    new_line=comp[0].strip()+" = "+value
                    ind=lines.index(line)
                    

    def readConfig(self,fname):
        contents=open(self.apach+fname+".cfg","r").read()
        return contents

    def delConfig(self,fname):
        os.remove(self.apach+fname+".cfg")
        return "ok"

    def addMigratedApp(self,apps,a_type):
        contents=open(self.apach+"org.karaf.messaging.cfg","r").read()
        lines=contents.split('\n')
        params={}
        for line in lines:
            if (line.strip()!=""):
                comp=line.split('=')
                if comp[1].strip()!="":
                    params[comp[0].strip()]=comp[1].strip().split(":")
                else:
                    params[comp[0].strip()]=[]
        if a_type=="forward":
            temp=[app for app in apps if app not in params['forward']]
            params['forward']=params['forward']+temp
        if a_type=="backward":
            temp=[app for app in apps if app not in params['proxy_back']]
            params['proxy_back']=params['proxy_back']+temp
        fp=open(self.apach+"org.karaf.messaging.cfg","w")
        for key in params:
            fp.write(key+" = "+":".join(params[key])+'\n')           
        fp.close()
        
    def removeMigratedApp(self,apps):
        contents=open(self.apach+"org.karaf.messaging.cfg","r").read()
        lines=contents.split('\n')
        params={}
        for line in lines:
            if (line.strip()!=""):
                comp=line.split('=')
                if comp[1].strip()!="":
                    params[comp[0].strip()]=comp[1].strip().split(":")
                else:
                    params[comp[0].strip()]=[]
        for app in apps:
            if app in params['forward']:
                params['forward'].remove(app)
            if app in params['proxy_back']:
                params['proxy_back'].remove(app)
        fp=open(self.apach+"org.karaf.messaging.cfg","w")
        for key in params:
            fp.write(key+" = "+":".join(params[key])+'\n')           
        fp.close()

if __name__ == "__main__":
    k=Karaf('karaf','karaf',"10.0.0.134","/home/pi/","/home/pi","/home/pi/apache-karaf-3.0.8")
    k.getApp('697bbbe0e7f3d065ae4652d7100044af','full_test_app-0.0.1-SNAPSHOT.jar')
#result=k.getBundleInfo(123)
#result=k.deployBundle("dummy_app-0.0.1-SNAPSHOT.jar")
#result=k.modifyConfig("org.karaf.test","test","test1")
#result=k.delBundle(117)
#result=k.getBundleId("devtransApp-0.0.1-SNAPSHOT.jar")
#result=k.readConfig("org.karaf.test")
    #print(k.createConfig("org.karaf.test2",{'arg1':'val1','arg2':'val2'}))
    #k.addMigratedApp(['Thermostat_App'],"forward")
    #k.removeMigratedApp(['Thermostat_App2','Bullcrap_app2'])
#result = k.delConfig("org.karaf.test2")
#result=k.readConfig("org.karaf.test2")
#result=k.saveDeployFile("sample_file","{'test1'}")
#print(result)
