#!/usr/bin/env python
import couchdb
import datetime
class monitor():
    def __init__(self,c_user,c_pass):
        self.c_user=c_user
        self.c_pass=c_pass
        self.couch=couchdb.Server('http://'+c_user+':'+c_pass+'@127.0.0.1:5984/')

    def getData(self,start,end,apps,gw):
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
            doc=db[p.value]
            if doc['Gateway']==gw:
                cnt=cnt+1
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
   apps=["Testing_App","Testing_App2","Testing_App3","Testing_App4","Testing_App5","Testing_App6","Testing_App7"]
   gws=["Vazquez_7663","Erickson_2204","Walters_1212","Olson_8701"]
   end=datetime.datetime.now()
   start=end-datetime.timedelta(minutes=15)
   start=start.strftime("%Y-%m-%d %H:%M:%S")
   end=end.strftime("%Y-%m-%d %H:%M:%S")
   dataset2=[["2017-03-31 16:37:23","2017-03-31 16:41:23"],
            ["2017-03-31 16:43:04","2017-03-31 16:47:04"],
            ["2017-03-31 16:49:12","2017-03-31 16:53:11"],
            ["2017-03-31 17:00:43","2017-03-31 17:04:42"],
            ["2017-03-31 17:06:54","2017-03-31 17:10:54"],
            ["2017-03-31 17:12:31","2017-03-31 17:16:30"],
            ["2017-03-31 17:18:13","2017-03-31 17:22:12"],
            ["2017-03-31 17:23:56","2017-03-31 17:27:55"]]
   dataset3=[["2017-03-31 17:30:27","2017-03-31 17:34:26"],
            ["2017-03-31 17:36:12","2017-03-31 17:40:11"],
            ["2017-03-31 17:41:53","2017-03-31 17:45:52"],
            ["2017-03-31 18:00:44","2017-03-31 18:04:43"],
            ["2017-03-31 17:55:00","2017-03-31 17:58:59"],
            ["",""],
            ["",""],]
   dataset4=[["2017-03-31 21:06:56","2017-03-31 21:10:55"],
            ["2017-03-31 21:20:27","2017-03-31 21:24:29"],
            ["2017-03-31 21:36:27","2017-03-31 21:40:26"],
            ["2017-03-31 21:43:42","2017-03-31 21:47:49"],
            ["2017-03-31 21:51:17","2017-03-31 21:55:17"],]
   dataset5=[["2017-04-01 00:48:04","2017-04-01 00:52:03"],
             ["2017-04-01 01:06:58","2017-04-01 01:10:52"],
             ["2017-04-01 01:14:28","2017-04-01 01:18:21"],
             ["2017-04-01 01:21:46","2017-04-01 01:25:46"],
             ["2017-04-01 01:28:55","2017-04-01 01:32:48"],]
   dataset=[["2017-04-02 15:13:28","2017-04-02 15:17:28"]]
   resp={}
   gw=0
   print("Gateway : "+gws[gw])
   for data in dataset:
       resp=m.getData(data[0],data[1],apps,gws[gw])
       print("-------------------------------")
       print(resp)
