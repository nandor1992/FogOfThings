#!usr/bin/python
import pika
import datetime
import json
import time
import os,sys
import uuid
import ConfigParser
import GatewayResolver
import random
from string import ascii_letters
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
            self.publishMsg(gw_name,"self nothing",resp)
        elif resp['task']=="Add New":
            del(resp['task'])
            print(resp)
            print("Notify Cluster leader to add GW")
            #Send message to Leader with info, might modify this 
            msg={'task':'add','peer_ip':ip,'peer_name':resp['name']}
            self.publishMsg(resp['new_clust'],"add",msg)
            #Message for Peer
            del(resp['new_clust'])
            self.publishMsg(gw_name,"self init",resp)
        elif resp['task']=="Remove Old":
            del(resp['task'])
            print(resp)
            print("Notify Leader Remove gateway from cluster")
            #Send message to Leader with info, might modify this 
            for clust in resp['old_clust']:
                msg={'task':'remove','peer_name':resp['name']}
                self.publishMsg(clust,"remove",msg)
            #Message for Peer
            del(resp['old_clust'])
            self.publishMsg(gw_name,"self init",resp)
        elif resp['task']=="New Master":
            del(resp['task'])
            print(resp)
            print("Notify all nodes in cluster that master has changed")
            #Send message to old peers that leader has changed ip
            for peer in resp['peers']:
                msg={'master_ip':ip}
                self.publishMsg(peer,"update",msg)
            #Message for Peer
            del(resp['peers'])
            self.publishMsg(gw_name,"self update",resp)
        elif resp['task']=="Remove Old Add New":
            del(resp['task'])
            print(resp)
            print("Remove Node from one cluster add to another notify both Leaders")
            #Send message to Leader with info, might modify this 
            msg={'peer_ip':ip,'peer_name':resp['name']}
            self.publishMsg(resp['new_clust'],"add",msg)
            #Send message to Leader with info, might modify this 
            for clust in resp['old_clust']:
                msg={'peer_name':resp['name']}
                self.publishMsg(clust,"remove",msg)
            #Message for Peer
            del(resp['new_clust'])
            del(resp['old_clust'])
            self.publishMsg(gw_name,"self init",resp)
        elif resp['task']=="Notify Workers Add New":
            del(resp['task'])
            print(resp)
            print("Notify Workers of cluster master deletion re-register Add Gw to new cluster ")
            #Notify Workers about master Going Down
            for node in resp['old_peers']:
                msg={'master':resp['name']}
                self.publishMsg(node,"deregister",msg)
            #Send message to Leader with info, might modify this 
            msg={'peer_ip':ip,'peer_name':resp['name']}
            self.publishMsg(resp['new_clust'],"add",msg)
            #Message for Peer
            del(resp['new_clust'])
            del(resp['old_peers'])
            self.publishMsg(gw_name,"self init",resp)

    def responseResolve(self,uuid,name,payload,datetime):
        print("Response Received with uuid: "+,uuid+" name: "+name+" datetime: "+datetime+" payload: "+payload)
    
    def publishMsg(self,name,what,msg):
        uuid=reg_api=''.join(random.choice(ascii_letters) for i in range(16))
        send={'type':'admin','source':'Cloud_Controller','uuid':uuid,'api_key':self.api_key}
        ret=json.dumps(msg)
        send['payload']="register "+what+" "+ret.replace('"',"'")
        print("Sending to: "+name+" Message: "+str(send))
        snd=json.dumps(send)
        rt_key="receive."+name
        self.channel.basic_publish(exchange='amq.topic', routing_key=rt_key, body=snd)


    def callback(self,ch,method,properties,body):
        try:
            body=body.replace('\n', '').replace('\r', '')
            body=body.replace("'",'"')
            print("--------------------New Message Received--------------------")
            print(body)
            my_json=json.loads(body);
        except ValueError:
            print "Non json payload"
        try:
            #gw_name=method.routing_key.split(".")[2]
            if 'source' and 'uuid' and 'name'and 'payload' and 'datetime' and 'api_key' in my_json:
                if my_json["api_key"]==self.api_key:
                    print("Response Values okay")
                    self.responseResolve(my_json['uuid'],my_json['name'],my_json['payload'],my_json['datetime'])
                else:
                    print("Wrong Api Key!")
            elif 'local_ip' and 'uuid' and 'name' and "hw_addr" and "peers" and "info" and "request" and "api_key" in my_json:
                gw_name=my_json["name"]
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
        except:
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
