#!/usr/bin/env python
import couchdb
import datetime
class monitor():
    def __init__(self,c_user,c_pass):
        self.c_user=c_user
        self.c_pass=c_pass
        self.couch=couchdb.Server('http://'+c_user+':'+c_pass+'@127.0.0.1:5984/')

    def getData(self,start,end,apps):
        resp={}
        db=self.couch['monitoring']
        look=db.view('views/dates',startkey=start,endkey=end)
        cnt=0
        for app in apps:
            resp[app]={}
            resp[app]['proc']=0.0
            resp[app]['msg']=0
        resp['cpu']=0.0
        resp['load']=0.0
        for p in look:
            cnt=cnt+1
            doc=db[p.value]
            #print("New Doc from :"+doc['date'])
            app_p=doc['apps']['processing']
            for app in apps:
                if app in app_p:
                    a_proc=app_p[app]
                    #print(a_proc)
                    resp[app]['proc']=resp[app]['proc']+float(a_proc)
            dev=doc['apps']['device']
            for app in apps:
                if app in dev:
                    num=dev[app]
                    #print(num)
                    resp[app]['msg']=resp[app]['msg']+int(num)
            ram=doc['gateway']['processor']['ram']
            cpu=doc['gateway']['processor']['cpu']
            load=doc['gateway']['processor']['load']
            #print(ram)
            #print(cpu)
            resp['cpu']=resp['cpu']+float(cpu)
            #print(load)
            resp['load']=resp['load']+float(load)
        #App
        resp['msg']=0
        for app in apps:
            resp[app]['proc']=resp[app]['proc']/float(cnt)/4.0
            resp[app]['msg']=resp[app]['msg']/float(cnt)/10.0
            resp['msg']=resp['msg']+resp[app]['msg']
        #Other
        resp['cpu']=resp['cpu']/float(cnt)
        resp['load']=resp['load']/float(cnt)
        del(resp['load'])
        return resp
            
    
if __name__ == "__main__":
   m=monitor("admin","hunter")
   apps=["Testing_App","Testing_App2"]
   end=datetime.datetime.now()
   start=end-datetime.timedelta(minutes=15)
   start=start.strftime("%Y-%m-%d %H:%M:%S")
   end=end.strftime("%Y-%m-%d %H:%M:%S")
   dataset=[["2017-03-15 13:19:04","2017-03-15 13:20:52"]]
   resp={}
   for data in dataset:
       resp=m.getData(data[0],data[1],apps)
       print(resp)
