#!flask/bin/python
from flask import Flask, request
import pika
import datetime
import json
import time
import os,sys
import ConfigParser


class AmqpClient:
    def __init__(self,user,passw,port,virt):
        
        self.credentials = pika.PlainCredentials(user,passw)
        self.parameters = pika.ConnectionParameters('localhost',port,virt,self.credentials)
        self.connection = pika.BlockingConnection(self.parameters);

        self.channel = self.connection.channel()
    def consume(self,queue_m):
        try:
            self.channel.basic_consume(self.on_response, no_ack=True,queue=queue_m)
            self.channel.confirm_delivery()
        except:
            return "error"
        return "ok"

    def on_response(self, ch, method, props, body):
       # if self.corr_id == props.correlation_id:
        self.response = body

    def call(self, payload,app,region,key):
        self.response = None
          #self.corr_id = str(uuid.uuid4())
        try:
            if key == None:
                properties_m=pika.BasicProperties(headers={'app':app,'region': region})
                self.channel.publish(exchange='region', routing_key='', body=payload, properties=properties_m,mandatory=True)
            else:
                properties_m=pika.BasicProperties(headers={'app':app,'region': region,'key':key})
                self.channel.publish(exchange='region', routing_key='', body=payload, properties=properties_m,mandatory=True)
        except:
           return "{'error':'Application or/and key is wrong!'}"
        while self.response is None:
            self.connection.process_data_events()
        return self.response
    
    def close(self):
        self.channel.close()
        self.connection.close()

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello World!"

@app.route('/region/<region>/<app_name>/<key>',methods=['GET','POST'])
def region(region,app_name,key):
    content = request.data
    Config=ConfigParser.ConfigParser()
    Config.read(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))+"/config.ini")
    amqp=AmqpClient(Config.get("Amqp","user"),Config.get("Amqp","pass"),int(Config.get("Amqp","port")),Config.get("Amqp","virt"))
    if amqp.consume(region)=="error":
        return "{'error':'Region Not found!'}"
    val=amqp.call(content,app_name,region,key)
    amqp.close()
    return val

if __name__ == '__main__':
    #Config Settings
    app.run(debug=True,host='0.0.0.0')
