#!usr/bin/python
import pika
import datetime
import json
import time
import os,sys
import uuid
import ConfigParser
import GatewayResolver
class AmqpClient:
    def __init__(self,host,user,passw,port,virt,api_key,res):
        
        self.credentials = pika.PlainCredentials(user,passw)
        self.parameters = pika.ConnectionParameters(host,port,virt,self.credentials)
        self.connection = pika.BlockingConnection(self.parameters);
        self.channel = self.connection.channel()
        self.api_key = api_key
        self.channel.basic_consume(self.callback,queue="admin",no_ack=True)
        self.resolver=res

    def close(self):
        self.channel.close()
        self.connection.close()

    def start(self):
        self.channel.start_consuming()

    def resolveReg(self,gw_name,uuid,ip,hw_addr,peers,gw_info):
        resp=self.resolver.resolveGateway(uuid,ip,hw_addr,peers,gw_info)
        if resp['task']=="None":
            print("Nothing to do device")
            del(resp['task'])
            self.publishMsg(gw_name,resp)
        elif resp['task']=="Add New":
            del(resp['task'])
            print(resp)
            print("Notify Cluster leader to add GW")
            #Send message to Leader with info, might modify this 
            msg={'task':'add','peer_ip':ip,'peer_name':resp['name']}
            self.publishMsg(resp['new_clust'],msg)
            #Message for Peer
            del(resp['new_clust'])
            self.publishMsg(gw_name,resp)
        elif resp['task']=="Remove Old":
            del(resp['task'])
            print(resp)
            print("Notify Leader Remove gateway from cluster")
            #Send message to Leader with info, might modify this 
            for clust in resp['old_clust']:
                msg={'task':'remove','peer_name':resp['name']}
                self.publishMsg(clust,msg)
            #Message for Peer
            del(resp['old_clust'])
            self.publishMsg(gw_name,resp)
        elif resp['task']=="New Master":
            del(resp['task'])
            print(resp)
            print("Notify all nodes in cluster that master has changed")
            #Send message to old peers that leader has changed ip
            for peer in resp['peers']:
                msg={'task':'update master','master_ip':ip}
                self.publishMsg(peer,msg)
            #Message for Peer
            del(resp['peers'])
            self.publishMsg(gw_name,resp)
        elif resp['task']=="Remove Old Add New":
            del(resp['task'])
            print(resp)
            print("Remove Node from one cluster add to another notify both Leaders")
            #Send message to Leader with info, might modify this 
            msg={'task':'add','peer_ip':ip,'peer_name':resp['name']}
            self.publishMsg(resp['new_clust'],msg)
            #Send message to Leader with info, might modify this 
            for clust in resp['old_clust']:
                msg={'task':'remove','peer_name':resp['name']}
                self.publishMsg(clust,msg)
            #Message for Peer
            del(resp['new_clust'])
            del(resp['old_clust'])
            self.publishMsg(gw_name,resp)
        elif resp['task']=="Notify Workers Add New":
            del(resp['task'])
            print(resp)
            print("Notify Workers of cluster master deletion re-register Add Gw to new cluster ")
            #Notify Workers about master Going Down
            for node in resp['old_peers']:
                msg={'task':'lost master','master':resp['name']}
                self.publishMsg(node,msg)
            #Send message to Leader with info, might modify this 
            msg={'task':'add','peer_ip':ip,'peer_name':resp['name']}
            self.publishMsg(resp['new_clust'],msg)
            #Message for Peer
            del(resp['new_clust'])
            del(resp['old_peers'])
            self.publishMsg(gw_name,resp)

    def publishMsg(self,name,msg):
        print("Sending to: "+name+" Message: "+str(msg))
        ret=json.dumps(msg)
        rt_key="receive."+name
        self.channel.basic_publish(exchange='amq.topic', routing_key=rt_key, body=ret)


    def callback(self,ch,method,properties,body):
        try:
            body=body.replace('\n', '').replace('\r', '')
            body=body.replace("'",'"')
            print("--------------------New Message Received")
            print(body)
            my_json=json.loads(body);
        except ValueError:
            print "Non json payload"
        try:
            gw_name=method.routing_key.split(".")[1]
            uuid=my_json["uuid"]
            ip=my_json["local_ip"]
            hw_addr=my_json["hw_addr"]
            peers=my_json["peers"]
            gw_info=my_json["info"]
            req=my_json["request"]
            if my_json["api_key"]==self.api_key:
                print("All values okay")
                if (req=="register"):
                    self.resolveReg(gw_name,uuid,ip,hw_addr,peers,gw_info)
                else:
                    print("It wants to do something else")
            else:
                print("Wrong Api Key!")
        except ValueError or IndexError:
            print("Key Error or Incomplete Values!")



if __name__ == '__main__':
    #Config Settings#
    print("Starting Cloud Admin")

    Config=ConfigParser.ConfigParser()
    Config.read(os.path.dirname(os.path.realpath(__file__))+"/config.ini")
    #Configurator Init
    res=GatewayResolver.GatewayResolver(Config.get("Database","user"),Config.get("Database","pass"),Config.get("Database","host"))
    #Setting for AMQP Init
    amqp=AmqpClient(Config.get("Messaging","host"),Config.get("Messaging","user"),Config.get("Messaging","pass"),int(Config.get("Messaging","port")),Config.get("Messaging","virt"),Config.get("Messaging","api_key"),res)   
    try:
        amqp.start()
    except KeyboardInterrupt:
        print("Keyboard baby")
        amqp.close()
        print("Exited Everything!")
    print("End")
