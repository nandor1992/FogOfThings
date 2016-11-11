#!/usr/bin/env python
import sqlite3
import os
import datetime
class Device:
    def __init__(self,path):
        self.path=path;
       #self.conn = sqlite3.connect(path)
       #self.c=conn.cursor()

    
    
    def getDevList(self):
        devices=[]
        files=[f for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path,f))]
        if len(files)!=0:
            for file in files:
                conn = sqlite3.connect(self.path+file)
                c=conn.cursor()
                c.execute("SELECT * FROM devices")
                value=c.fetchone()
                while value:
                    devices.append({"driver":""+file[:-3],"id":str(value[0]),
                                "type":str(value[1]),"mac":str(value[2]),
                                "version":str(value[3]),"date":str(value[4]),
                                "status":str(value[5])})
                    value=c.fetchone()
                conn.close()
            return devices
        else:
            return None

    def getSpecDevList(self,type_d,type_s):
        devices=[]
        files=[f for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path,f))]
        if len(files)!=0:
            for file in files:
                conn = sqlite3.connect(self.path+file)
                c=conn.cursor()
                c.execute("SELECT * FROM devices WHERE status='"+type_s+"' and type='"+type_d+"' ORDER BY last_update DESC")
                value=c.fetchone()
                while value:
                    devices.append({"driver":""+file[:-3],"id":str(value[0]),
                                "type":str(value[1]),"mac":str(value[2]),
                                "version":str(value[3]),"date":str(value[4]),
                                "status":str(value[5])})
                    value=c.fetchone()
                conn.close()
            return devices
        else:
            return None        

    def getSensorList(self,driver,dev):
        sense=[]
        conn = sqlite3.connect(self.path+driver+".db")
        c=conn.cursor()
        c.execute("SELECT * FROM sensors WHERE dev_id='"+dev+"'")
        value=c.fetchone()
        while value:
            sense.append({"name":str(value[1]),"unit":str(value[2])})
            value=c.fetchone()
        conn.close()
        return sense

    def modifyDevStatus(self,driver,dev,value):
        conn = sqlite3.connect(self.path+driver+".db")
        c=conn.cursor()
        string="UPDATE devices SET status='"+value+"', last_update='"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"' WHERE dev_id= '"+dev+"'"
        c.execute(string)
        conn.commit()
        conn.close()

#d=Device("/home/pi/databases/")
#d.modifyDevStatus("ardu_rf24","OWaDMY9V","Idle")
#print(d.getDevList())
#print(d.getSensorList("ardu_rf24","OWaDMY9V"))
