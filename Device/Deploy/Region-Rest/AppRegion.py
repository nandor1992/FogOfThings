#!flask/bin/python
from flask import Flask, request
import pika
import datetime
import json
import time
import os,sys
import ConfigParser
import uuid

class AmqpClient:
    def __init__(self,user,passw,port,virt):
        
        self.credentials = pika.PlainCredentials(user,passw)
        self.parameters = pika.ConnectionParameters('localhost',port,virt,self.credentials)
        self.connection = pika.BlockingConnection(self.parameters);

        self.channel = self.connection.channel()
    def consume(self,queue_m):
        try:
            self.channel.basic_consume(self.on_response, no_ack=False,queue=queue_m)
            self.channel.confirm_delivery()
        except:
            return "error"
        return "ok"

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.headers.get("uuid"):
            self.response = body
            ch.basic_ack(delivery_tag = method.delivery_tag)
        else:
            ch.basic_nack(delivery_tag = method.delivery_tag, requeue = True)

    def call(self, payload,app,region,key):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        try:
            if key == None:
                properties_m=pika.BasicProperties(headers={'app':app,'region': region,'uuid':self.corr_id})
                self.channel.publish(exchange='region', routing_key='', body=payload, properties=properties_m,mandatory=True)
            else:
                properties_m=pika.BasicProperties(headers={'app':app,'region': region,'key':key,'uuid':self.corr_id})
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

@app.route('/region/')
def index():
    return "<p>Hello World!</p><p>For a better hello world view try: /region/[region_name]/[app_name]/[key]</p> <p> If you don't know what these are you are probably lost, sorry </p>"

@app.route('/region/<region>/<app_name>/<key>',methods=['POST'])
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

@app.route('/region/<region>/<app_name>/<key>',methods=['GET'])
def region_get(region,app_name,key):
    content = "GET"
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
