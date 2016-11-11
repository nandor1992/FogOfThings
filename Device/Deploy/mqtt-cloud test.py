
#!/usr/bin/env python
import pika
import time
import datetime
import paho.mqtt.client as mqtt
import json
import csv

count = 0
tot_count=400
start_millis = datetime.datetime.now()
b=open('data.csv','w')
a=csv.writer(b)
first=1

def on_connect(client, userdata, rc):
    print("Connected with result code "+str(rc))
	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.
    client.subscribe("receive/gateway1",1)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global count
    global start_millis
    count=count+1
    print(msg.topic+" "+str(msg.payload))
    time_now=datetime.datetime.now()
    diff_millis=time_now-start_millis
    print diff_millis
    a.writerow([count,diff_millis.microseconds])
#    time.sleep(0.1)
    start_millis=datetime.datetime.now()
    if (count<tot_count):
        data='{"dev_type": "ardUnoTemp", "comm": "Gateway-RF24", "device": "OWaDMY9V", "dev_number": "0", "payload": [{"n": "temp", "v": "25.00"}, {"n": "hum", "v": "34.00"}, {"n": "dew", "v": "8.07"}], "datetime": "2016-05-17 12:13:01"}'
        client.publish("send/gateway1",payload=data,qos=1)
    else:
        client.loop_stop()


client = mqtt.Client(client_id="test1_py",clean_session=True);
client.username_pw_set('admin','hunter')
client.connect("10.0.0.133", 1883,60)
client.on_connect = on_connect
client.on_message = on_message
start_millis=datetime.datetime.now()
while (count<tot_count):
    client.loop()
client.disconnect()
b.close()
print("Done")
