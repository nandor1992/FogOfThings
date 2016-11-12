
#!/usr/bin/env python
import pika
import time
import paho.mqtt.client as mqtt
import json
import os,sys

clientId="gateway2"
conn_name='mqtt_conn1'

credentials = pika.PlainCredentials('admin', 'hunter')
parameters = pika.ConnectionParameters('localhost',5672,'test', credentials)
connection = pika.BlockingConnection(parameters);

channel = connection.channel()

client = mqtt.Client(client_id=clientId+"_Send",clean_session=True);
client.username_pw_set('admin','hunter')
client.connect("clem-rasp01.coventry.ac.uk",15672 ,10)

f=open('/home/pi/log/amqp_to_mqtt.log','a')
sys.stdout=f
    
print("Broker started: "+time.strftime('%X %x %Z'))
print(' [*] Waiting for messages. To exit press CTRL+C')

def callback(ch,method,properties,body):
    print("[x] Received %r"%body)
    try:
        try:
            my_json=json.loads('{"payload":'+body+'}')
        except ValueError:
            print "Non json payload"
            body=body.replace('"',"'")
            my_json=json.loads('{"payload":"'+body+'"}')
        for names in properties.headers:
            temp={names:properties.headers.get(names)}
            my_json.update(temp)
        data=json.dumps(my_json)
        print data
        client.reconnect()
        (result,mid)=client.publish("send/"+clientId,payload=data,qos=1)
        while result!=mqtt.MQTT_ERR_SUCCESS:
            print("MQTT Disconnected "+time.strftime('%X %x %Z')+ ", Reconnecting")
            client.reconnect()
            (result,mid)=client.publish("send/"+clientId,payload=data,qos=1)
        print("Message Sent with result: "+str(result)+" Message Id: "+str(mid))
            
    except (ValueError, TypeError) as e:
            print "Nor Json or valid string data"
    sys.stdout.flush()
    
channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,queue=conn_name,no_ack=True)
sys.stdout.flush()
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print "Keyboard baby"
    client.disconnect()
    connection.close()
    print "Exiting Main Thread"
    sys.stdout.flush()
