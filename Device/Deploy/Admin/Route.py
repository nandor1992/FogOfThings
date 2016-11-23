#!/usr/bin/env python
import pika

class Route:
    def __init__(self,channel):
        self.channel=channel;

    def add(self, source, dest_name, args):
        self.channel.queue_bind(dest_name,source,routing_key="",arguments=args)
        return "ok"

    def addExBind(self,source,dest,args):
        self.channel.exchange_bind(dest,source,routing_key="",arguments=args)
        return "ok"

    def addExUnBind(self,source,dest,args):
        self.channel.exchange_unbind(dest,source,routing_key="",arguments=args)
        return "ok"

    def remove(self, source, dest_name, args):
        self.channel.queue_unbind(dest_name,source,routing_key="",arguments=args)
        return "ok"

    def addQueue(self,name):
        self.channel.queue_declare(queue=name,durable=True)
        return "ok"

    def removeQueue(self,name):
        self.channel.queue_delete(queue=name)
        return "ok"

#credentials = pika.PlainCredentials('admin', 'hunter')
#parameters = pika.ConnectionParameters('localhost',5672,'test', credentials)
#connection = pika.BlockingConnection(parameters);
#channel = connection.channel()

#r=Route(channel)
#r.removeQueue("test2")
#channel.close()
#connection.close()
