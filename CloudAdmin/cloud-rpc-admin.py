#!usr/bin/python
import pika
import datetime
import json
import time
import os,sys
import uuid
import ConfigParser
import GatewayResolver
import AppResolver
import random
import ast
from string import ascii_letters
class AmqpClient:
    def __init__(self,host,user,passw,port,virt,api_key,res,resA):
        
        self.credentials = pika.PlainCredentials(user,passw)
        self.parameters = pika.ConnectionParameters(host,port,virt,self.credentials)
        self.connection = pika.BlockingConnection(self.parameters);
        self.channel = self.connection.channel()
        self.api_key = api_key
        self.channel.basic_consume(self.callback,queue="admin",no_ack=True)
        self.resolver=res
        self.resolverApp=resA

    def close(self):
        self.channel.close()
        self.connection.close()

    def start(self):
        self.channel.start_consuming()

    def resolveMigrate(self,cluster,uuid,gw,app):
        print("For Cluster: "+cluster+" with uuid: "+uuid+" Migrate App: "+app +" To host: "+gw)
        data_app=self.resolver.checkApp(app,cluster,gw)
        print(data_app)
        if data_app['type']=='O->N':
            #Migrating app to new GW
            #Tell Host to Migrate Away
            self.publishDeplMsg(data_app['host'],uuid,'migrate away',app+" "+gw)
            #Tell New Host to Receive App 
            self.publishDeplMsg(gw,uuid,'migrate add',app+" "+data_app['host'])
        elif data_app['type']=='N->O':
            #Tell Host to migrate app back
            self.publishDeplMsg(gw,uuid,'migrate back',app+" "+data_app['current'])
            #Tell Old Host to Forget App
            self.publishDeplMsg(data_app['current'],uuid,'migrate remove',app+" "+gw)
        elif data_app['type']=='N->N':
            #Tell Host to Migrate to other 
            self.publishDeplMsg(data_app['host'],uuid,'migrate change',app+" "+gw)
            #Tell Old Host to Forget App
            self.publishDeplMsg(data_app['current'],uuid,'migrate remove',app+" "+data_app['host'])
            self.publishDeplMsg(gw,uuid,'migrate add',app+" "+data_app['host'])
        else:
            #Either Nothing to do or App not in Clust or GW not in clust
            return "Error: Nothing to Do or No way of Doing it"
        #Save Changes to DB
        self.resolver.updateApp(app,gw)
        return "Request Processed and Sent to Gw(s)"


    def resolveReg(self,gw_name,uuid,ip,hw_addr,peers,gw_info):
        resp=self.resolver.resolveGateway(uuid,ip,hw_addr,peers,gw_info)
        print(resp)
        if resp['task']=="None":
            print("Nothing to do device")
            del(resp['task'])
            self.publishMsg(gw_name,"self nothing",resp)
        elif resp['task']=="Init":
            print("New Cluster Initialize")
            del(resp['task'])
            self.publishMsg(gw_name,"self initClust",resp)
        elif resp['task']=="Add New":
            del(resp['task'])
            print(resp)
            print("Notify Cluster leader to add GW")
            #TO-DO : Send to peers
            #Send message to Leader with info, might modify this to send to peers !!!!!!!!!!
            msg={'peer_ip':ip,'peer_name':resp['name'],'peer_mac':hw_addr}
            self.publishMsg(resp['new_clust'],"add",msg)
            #Message for Peer
            ind=resp['old_peers'][0].index(resp['name'])
            del(resp['old_peers'][0][ind])
            del(resp['old_peers'][1][ind])
            print(resp['old_peers'])
            for peep in resp['old_peers'][0]:
                if peep != resp['new_clust']:
                    self.publishMsg(peep,"addPeer",msg)
            #Message to new unit
            del(resp['new_clust'])
            self.publishMsg(gw_name,"self init",resp)
        elif resp['task']=="Remove Old":
            del(resp['task'])
            print(resp)
            print("Notify Leader Remove gateway from cluster")
            #Send message to Leader with info, might modify this 
            for clust in resp['old_clust']:
                msg={'peer_name':resp['name']}
                self.publishMsg(clust,"remove",msg)
            #Message for Peer
            del(resp['old_clust'])
            self.publishMsg(gw_name,"self initClust",resp)
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
            msg={'peer_ip':ip,'peer_name':resp['name'],'peer_mac':hw_addr}
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

    def resolveDeploy(self,cluster,main_gw,payload,task,uuid):
        print("For Clust: "+cluster+" and GW: "+str(main_gw))
        print(payload)
        print(task)
        if self.resolver.checkIfClustGW(cluster,[main_gw])=="ok":
            print("Gateways and Cluster Found!")
            #GW 0 is always the main Gateway 
            ##Retreive App Info
            if task=="bundle deploy":
                app_data=self.resolverApp.getData(payload)
                add_gw=self.resolver
                if app_data==None:
                    return "App Not Found in Database"
                else:      
                    self.publishDeplMsg(main_gw,uuid,task,app_data)
            else:
                self.publishDeplMsg(main_gw,uuid,task,payload)
            return "Bundle Resolved and Published to GW(s)"
        else:
            return "Bundle Gateways not found so not deploying"


    def publishDeplMsg(self,name,uuid,task,payload):
        send={'type':'admin','source':'Cloud_Controller','uuid':uuid,'api_key':self.api_key}
        if task=="bundle deploy":
            ret=json.dumps(payload)
            send['payload']=""+task+" "+ret.replace('"',"'")
        elif task=="bundle remove":
            send['payload']="bundle remove "+payload
        else:
            send['payload']=str(task)+" "+payload
        print("Sending to: "+name+" Message: "+str(send))
        snd=json.dumps(send)
        rt_key="receive."+name
        self.channel.basic_publish(exchange='amq.topic', routing_key=rt_key, body=snd)

    def responseResolve(self,uuid,name,payload,datetime):
        print("Response Received with uuid: "+uuid+" name: "+name+" datetime: "+datetime+" payload: "+payload)
    
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
            body2=body.replace('\n', '').replace('\r', '')
            body2=body2.replace("'",'"')
            print("--------------------New Message Received--------------------")
            print(body2)
            my_json=json.loads(body2);
        except ValueError:
            print "Non json payload"
            try:
                my_json=ast.literal_eval(body)
            except ValueError:
                print("Very Non Json Payload")
                return None
        try:
            #gw_name=method.routing_key.split(".")[2]
            req=my_json["request"]
            if req!="None":
                if my_json["api_key"]==self.api_key:
                    if req=="register":
                        if set(['source','uuid' , 'name', 'payload' ,'datetime' , 'api_key']).issubset(my_json):
                            print("Response Values okay")
                            self.responseResolve(my_json['uuid'],my_json['name'],my_json['payload'],my_json['datetime'])
                        elif set(['local_ip' , 'uuid' , 'name' ,"hw_addr" , "peers" , "info" , "request" , "api_key"]).issubset(my_json):
                            gw_name=my_json["name"]
                            uuid=my_json["uuid"]
                            ip=my_json["local_ip"]
                            hw_addr=my_json["hw_addr"]
                            peers=my_json["peers"]
                            gw_info=my_json["info"]
                            req=my_json["request"]
                            print("All values okay")
                            self.resolveReg(gw_name,uuid,ip,hw_addr,peers,gw_info)
                        else:
                            print("Doesn't fit anything!")
                    elif req=="deploy bundle":
                        print("Deploy Bundle")
                        if set(['name','cluster','gateway','uuid','payload']).issubset(my_json):
                            name=my_json['name']
                            clust=my_json['cluster']
                            gw=my_json['gateway']
                            uuid=my_json['uuid']
                            resp=self.resolveDeploy(clust,gw,my_json['payload'],"bundle deploy",uuid)
                            send={'type':'admin','source':'Cloud_Controller','uuid':uuid,'api_key':self.api_key}
                            send['payload']=resp
                            print("Sending to: "+name+" Message: "+str(send))
                            snd=json.dumps(send)
                            rt_key="receive."+name
                            self.channel.basic_publish(exchange='amq.topic', routing_key=rt_key, body=snd)
                        else:
                            print("Stuff not Given!")
                    elif req=="remove bundle":
                        print("remove bundle")
                        if set(['name','cluster','gateway','uuid']).issubset(my_json):
                            name=my_json['name']
                            clust=my_json['cluster']
                            gw=my_json['gateway']
                            uuid=my_json['uuid']
                            resp=self.resolveDeploy(clust,gw,my_json['payload'],"bundle remove",uuid)
                            send={'type':'admin','source':'Cloud_Controller','uuid':uuid,'api_key':self.api_key}
                            send['payload']=resp
                            print("Sending to: "+name+" Message: "+str(send))
                            snd=json.dumps(send)
                            rt_key="receive."+name
                            self.channel.basic_publish(exchange='amq.topic', routing_key=rt_key, body=snd)
                        else:
                            print("Stuff not Given!")
                    elif req=="migrate bundle":
                        print("Migrate Bundle")
                        if set(['name','cluster','uuid','gateway']).issubset(my_json):
                            name=my_json['name']
                            gw=my_json['gateway']
                            clust=my_json['cluster']
                            uuid=my_json['uuid'] 
                            resp=self.resolveMigrate(clust,uuid,gw,str(my_json['payload']))
                            send={'type':'admin','source':'Cloud_Controller','uuid':uuid,'api_key':self.api_key}
                            send['payload']=resp
                            print("Sending to: "+name+" Message: "+str(send))
                            snd=json.dumps(send)
                            rt_key="receive."+name
                            self.channel.basic_publish(exchange='amq.topic', routing_key=rt_key, body=snd)
                        else:
                            print("Stuff not Given!")
                    elif req=="response":
                        print("Response from GW")
                        try:
                            save=ast.literal_eval(my_json['payload'])
                            if self.resolver.saveDeployment(save) =="ok":
                                print("Deployment Saved to Cloud")
                            else:
                                print("Error with saving!")
                        except:
                            print("Non Json or Python type")
                            print(my_json['payload'])
                    else:
                        print("Request Unknown!")
                else:
                    print("Wrong API Key!")
            else:
                print("No request found!")
        except Exception,e:
        #except KeyboardInterrupt,e:
            print("Key Error or Incomplete Values or Else!"+str(e))



if __name__ == '__main__':
    #Config Settings#
    print("Starting Cloud Admin")

    Config=ConfigParser.ConfigParser()
    Config.read(os.path.dirname(os.path.realpath(__file__))+"/config.ini")
    #Configurator Init
    res=GatewayResolver.GatewayResolver(Config.get("Database","user"),Config.get("Database","pass"),Config.get("Database","host"))
    resA=AppResolver.AppResolver(Config.get("Database","user"),Config.get("Database","pass"),Config.get("Database","host"))
    #Setting for AMQP Init
    amqp=AmqpClient(Config.get("Messaging","host"),Config.get("Messaging","user"),Config.get("Messaging","pass"),int(Config.get("Messaging","port")),Config.get("Messaging","virt"),Config.get("Messaging","api_key"),res,resA)   
    try:
        amqp.start()
    except KeyboardInterrupt:
        print("Keyboard baby")
        amqp.close()
        print("Exited Everything!")
    print("End")
