#!/usr/bin/python

import sqlite3
import datetime
import couchdb
couch = couchdb.Server('http://admin:hunter@127.0.0.1:5984/')
#db=couch['blue']
#db=couch['rf24']
db=couch['rf434']
#db = couch.create('xbee') # newly created
#db= couch['test']
#print(db['2fd23a3905ce773e2c5acc63ec000bba'])
#couch.delete('blue')
#path ='/home/pi/databases/atmega128rfa1.db'
#path='/home/pi/databases/ardu_blue.db'
#path='/home/pi/databases/zigbeedb.db'
#path ='/home/pi/FogOfThings/Device/databases/ardu_blue.db'
#path ='/home/pi/FogOfThings/Device/databases/ardu_rf24.db'
path ='/home/pi/FogOfThings/Device/databases/atmega128rfa1.db'
conn = sqlite3.connect(path)
c=conn.cursor()
c.execute("SELECT * FROM devices")
result=c.fetchone()
while result!=None:
    print result
    sensors=[]
    c2=conn.cursor()
    c2.execute("SELECT * FROM sensors WHERE dev_id='"+result[0]+"'")
    res2=c2.fetchone()
    while res2!=None:
        sensors.append({res2[1]:res2[2]})
        res2=c2.fetchone()
    print sensors
    db.save({'dev_id': result[0],'dev_type': result[1],'mac': result[2],'version': result[3],'date': result[4],'status': result[5],'sensors':sensors})
    result=c.fetchone()
conn.close()
