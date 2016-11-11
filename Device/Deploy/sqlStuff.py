#!/usr/bin/python

import sqlite3
import datetime
#path ='/home/pi/databases/atmega128rfa1.db'
#path='/home/pi/databases/ardu_blue.db'
#path='/home/pi/databases/zigbeedb.db'
path ='/home/pi/databases/ardu_rf24.db'
conn = sqlite3.connect(path)
c=conn.cursor()
#c.execute('''CREATE TABLE devices (dev_id text,type text,mac text,ver text,last_update DATETIME)''')
#c.execute('''CREATE TABLE sensors (dev_id text,name text,unit text)''')
#c.execute("INSERT INTO devices VALUES ('123abc13','atmega128rfa1','123mac123','1','2015-04-23 4:14:00')")
#c.execute("INSERT INTO sensors VALUES ('123abc123','random','')")
#c.execute("INSERT INTO sensors VALUES ('123abc123','light','adc')")
#conn.commit()
#c.execute("SELECT * FROM sensors")
#print c.fetchall()
#string="UPDATE devices SET status='Idle', last_update='"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"' WHERE dev_id= 'OWaDMY9V'"
#print string
#string="ALTER TABLE devices ADD status text"
#c.execute(string)
#conn.commit()
c.execute("SELECT dev_id,type,status FROM devices")
print c.fetchall()
conn.close()
