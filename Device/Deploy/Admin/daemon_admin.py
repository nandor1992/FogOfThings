#!/usr/bin/env python
import pika
import datetime
import Route
import Karaf
import Device
import Resource
import json
import time
import os,sys
import ConfigParser
import Region
import ast
import random
from string import ascii_letters,digits
from Init import Init,InitReq
from daemon import Daemon
import logging
#Config Settings
Config=ConfigParser.ConfigParser()
conf_loc="/home/pi/FogOfThings/Device/config.ini"
Config.read(conf_loc)
PIDFILE1="/home/pi/FogOfThings/Device/pid/admin.pid"
LOGFILE = Config.get("Log","location")+'/admin.log'
logging.basicConfig(filename=LOGFILE,level=logging.DEBUG)
logging.getLogger("pika").setLevel(logging.ERROR)

class admin():
#class admin(Daemon):

    def resolve(payload):
        logging.debug(payload)
        response="Error"
        components=payload.split(' ')
        if components[0]=='route':
            logging.debug("Routing Task")
            if components[1]=='add':
                logging.debug("Add route")
                response=self.routeTask("add"," ".join(components[2:]))
            elif components[1]=='remove':
                logging.debug("Delete route")
                response=self.routeTask("remove","  ".join(components[2:]))
            else:
                logging.debug("No subtask found")
        elif components[0]=='bundle':
            print ("Bundle Task")
            if components[1]=='deploy':
                logging.debug("Deploy Bundle")
                response=self.deployTask(" ".join(components[2:]))
            elif components[1]=='remove':
                logging.debug("Remove Bundle")
                response=self.removeTask(" ".join(components[1:]))
            else:
                logging.debug("No subtask found")
        elif components[0]=='cluster':
            logging.debug("Cluster")
            if components[1]=='dicover':
                logging.debug("Discover Cluster")
                response=self.discoverRegion()
            elif components[1]=='new':
                logging.debug("Create new Cluster")
                #To-Do Create new Cluster 
            elif components[1]=='join':
                logging.debug("Delete region")
                #Join cluster on ip
            elif components[1]=='resolve':
                logging.debug("Delete region")
                #Do discovery and everything to find peers
            else:
                logging.debug("No subtask found")
        elif components[0]=='register':
            logging.debug("Register")
            response="ok"
            if components[1]=='add':
                logging.debug("Add Node to Existing Cluster (4 admin)") ##Working Case 
            ##Only works fro Admin, modify to allow peers to add Node as well
            ##To-Do
                ret=ast.literal_eval("  ".join(components[2:]))
                self.reg.addGwToDatabase(ret['peer_name'],ret['peer_ip'],ret['peer_mac'])
                self.reg.addCouchNode(ret['peer_ip'])
                self.reg.addUpstream("admin","hunter",ret['peer_ip'],"test")
            ##Add node to Couchdb and Rabbitmq cluster, update Database with it's value
            elif components[1]=='remove':
                logging.debug("Remove Node")
                ##Remove node from Rabbitmq and Couchdb, update Database with it's value 
            elif components[1]=='update':
                logging.debug("Update Node, for new master ip")
                ##De-register rabbitmq and CLuster and register with new Admin 
            elif components[1]=='deregister':
                logging.debug("Deregister node and start over ")
                ##Delete all nodes from CouchDB and Rabbitmq and start registration process again
            elif components[1]=='self':
                logging.debug("Self")
                if components[2]=='nothing':
                    logging.debug("Update Variables received but nothing else to do")
                    ret=ast.literal_eval("  ".join(components[3:]))
                    if 'master' in ret:
                        logging.debug("Node") ## Working Case - Done 
                        self.modifyConfig(ret['reg_api'],ret['name'],ret['reg_name'],ret['master'])
                    else:
                        logging.debug("Master")   ## Working Case - Done
                        self.modifyConfig(ret['reg_api'],ret['name'],ret['reg_name'],None)   
                elif components[2]=='init':
                    logging.debug("Initialize node to be added to Cluster") ## Working Case
                    ##To-Do
                    ret=ast.literal_eval("  ".join(components[3:]))
                    self.modifyConfig(ret['reg_api'],ret['name'],ret['reg_name'],ret['master'])
                    ##Add Uploding Rabbitmq file with configs
                    self.ini.initRabbitmq(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))+"/RabbitVersions/rabbit_bare.json")
                    self.reg.setClustQueue(ret['name'])
                    self.reg.addUpstream("admin","hunter",ret['master'],"test")
                elif components[2]=='initClust':
                    logging.debug("Initialize new Cluster you are Master") ## Working Case - Done
                    ##To-Do
                    ret=ast.literal_eval("  ".join(components[3:]))
                    self.modifyConfig(ret['reg_api'],ret['name'],ret['reg_name'],None)
                    self.ini.initRabbitmq(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))+"/RabbitVersions/rabbit_bare.json")
                    self.ini.initCouchDB(Config.items("DeviceQ"))
                    self.reg.setClustQueue(ret['name'])
                    self.reg.initClustDatabase(ret['reg_name'],ret['reg_api'],ret['name'],reg.myIp(),reg.myMac())
                elif components[2]=='update':
                    logging.debug("New Ip for me the Master")
                ##To-Do
        else:
            logging.debug("No task found")
        return response


    def modifyConfig(self,reg_api,name,clust_name,admin):
        Config.set('General','gateway_name',name)
        Config.set('Cluster','cluster_name',clust_name)
        Config.set('Cluster','cluster_api',reg_api)
        if admin!=None:
            Config.set('Cluster','cluster_admin',admin)
        else:
            Config.set('Cluster','cluster_admin',"This")
        with open(conf_loc,'wb') as configfile:
            Config.write(configfile)


    def discoverRegion(self):
        return self.reg.getDevsOnWan(Config.get("Cluster","peer_hardware"))

    def routeTask(self,kind,payload):
        my_j=jsonize(payload)
        if my_j==None:
            return "Error:jsonize"
        else:
            source=my_j.get("source")
            dest_name=my_j.get("dest_name")
            print "Source:"+source+" Dest_name:"+dest_name
            args={}
            result=""
            for item in my_j["header"]:
                args[item["property"]]=item["value"]
            if kind=="add":
                result=route.add(source,dest_name,args)
            if kind=="remove":
                result=route.remove(source,dest_name,args)
            return result

    def deployTask(payload):
        d_son=self.jsonize(payload)
        logging.debug(json.dumps(d_son,indent=2,sort_keys=False))
        if d_son==None:
            return "Error:jsonize"
        else:
            #ToDo:verify cloud,device,region,name,deployment_config
            if self.deployVerify(d_son)!=None:
                return "Error:Verify"
            else:
                #Get Variables for werk"
                list_conf=[]
                cloud=d_son.get("comm").get("cloud")
                region=d_son.get("comm").get("region")
                apps=d_son.get("comm").get("apps")
                devices=d_son.get("comm").get("devices")
                resource=d_son.get("comm").get("resources")
                name=str(d_son.get("name"))
                desc=str(d_son.get("description"))
                app_f=str(d_son.get("file"))
                conf=d_son.get("deployment").get("config").get("custom_params")
                conf_f=str(d_son.get("deployment").get("config").get("file"))
                #Add Device Name
                list_conf.append("name = "+name)
                
                #Cloud Stuff
                if cloud!=None:
                    logging.debug("Cloud Config Started")
                    conf_cloud=""
                    for con in cloud:
                        result1=self.route.add("cloud_resolve",str(con),{"app":name,"cloud":str(con)})
                        conf_cloud=conf_cloud+con+":"
                    result1b=self.route.add("apps_resolve","karaf_app",{"app":name})
                    list_conf.append("cloud = "+conf_cloud[:-1])
                    if result1!="ok" or result1b!="ok":
                        return "Error: Cloud Connection Setup"
                    else:
                        print ("Cloud connection configuration successfull")
                #Device Stuff
                if devices!=None:
                    logging.debug("Devices Config Started")
                    for dev in devices:
                        dev_l=self.device.getSpecDevList(dev["type"],dev_status,controller_name) #Change Idle to Available
                        if len(dev_l)<int(dev["required"]):
                            return "Error: Not Enough Required Devices"
                    for dev in devices:
                        dev_l=self.device.getSpecDevList(dev["type"],dev_status,controller_name) #Change Idle to Available
                        dev_conf=""
                        if dev["cnt"]=="":
                            for dev_s in dev_l:
                                dev_conf=dev_conf+":"+str(dev_s["id"])
                                result1=self.route.add("apps_resolve","karaf_app",{"device":dev_s["id"]})
                                if dev["reserve"]=="No":
                                    result2=self.route.add("device_resolve",dev_s["driver"],{"device":dev_s["id"]})
                                else:
                                    result2=self.route.add("device_resolve",dev_s["driver"],{"device":dev_s["id"],"app":name})
                        else:
                            for i in range(0,int(dev["cnt"])):
                                dev_conf=dev_conf+":"+str(dev_l[i]["id"])
                                result1=self.route.add("apps_resolve","karaf_app",{"device":dev_l[i]["id"]})
                                if dev["reserve"]=="No":
                                    result2=self.route.add("device_resolve",dev_l[i]["driver"],{"device":dev_l[i]["id"]})
                                else:
                                    result2=self.route.add("device_resolve",dev_l[i]["driver"],{"device":dev_l[i]["id"],"app":name})
                        list_conf.append("dev_"+dev["type"]+" = "+dev_conf[1:])
                    if result1!="ok" or result2!="ok":
                        return "Error: Devices Connection Setup"
                    print ("Device connection configuration successfull")               

                #Region Stuff
                #ToDO: Add Part to Notify Region of this maybe
                if region!=None:
                    logging.debug("Region Config Started")
                    region_conf=""
                    for reg in region:
                        result2=self.route.addQueue("reg_"+str(reg["name"]))
                        region_conf=region_conf+reg["name"]+":"
                        if str(reg["key"])=="":
                            result2b=rself.oute.add("region_resolve","reg_"+str(reg["name"]),{"app":name,"region":str(reg["name"])})
                            result2d=self.route.addExBind("region","apps_resolve",{"app":name,"region":str(reg["name"])})
                            result3=self.route.add("apps_resolve","karaf_app",{"app":name})
                        else:
                            result2b=self.route.add("region_resolve","reg_"+str(reg["name"]),{"app":name,"region":str(reg["name"])})
                            result2d=self.route.addExBind("region","apps_resolve",{"app":name,"region":str(reg["name"]),"key":str(reg["key"])})
                            result3=self.route.add("apps_resolve","karaf_app",{"app":name})
                    result2c=self.route.add("apps_resolve","karaf_app",{"app":name})
                    list_conf.append("region = "+region_conf[:-1])
                    if result2!="ok" or result2b!="ok" or result2c!="ok" or result2b!="ok" or result3!="ok":
                        return "Error: Region Connection Setup"
                    else:
                        print ("Region connection configuration successfull")

                #Apps Stuff
                if apps!=None:
                    logging.debug("Apps Config Started")
                    must_l=self.karaf.getDeployedApps(apps["required_apps"])
                    int_l=self.karaf.getDeployedApps(apps["interrested_apps"])
                    if len(apps["required_apps"])!=len(must_l):
                        return "Error: Required Apps Not met"
                    apps_list=":".join(must_l)
                    apps_list=apps_list+":"+":".join(int_l)
                    list_conf.append("apps = "+apps_list)
                    print ("Apps connection configuration successfull")

                #Resource Stuff
                #ToDo: Add part to notify/resolve Resource
                if resource!=None:
                    logging.debug("Resource Config Started")
                    res_list=""
                    for res_1 in resource:
                        res_queue=self.res.getResourceQue(str(res_1))
                        if res_queue!=None:
                            result0=self.res.initializeRes(res_1,name)
                            result1=self.route.add("resource_resolve",res_queue,{"app":name,"res":str(res_1)})
                            res_list=res_list+res_1+":"
                    if result0!="ok" or result1!="ok":
                        return "Error: Resource does not exist"
                    self.route.add("apps_resolve","karaf_app",{"app":name})
                    list_conf.append("resources = "+res_list[:-1])
                    print ("Resource connection configuration successfull")

                #Create file with added params and existing ones from previous components
                if conf!=None and conf_f!=None:
                    logging.debug("Conf-File Config Started")
                    for param in conf:
                        list_conf.append(""+param+" = "+conf[param])
                    if self.karaf.createConfig(conf_f,list_conf)!="ok":
                        return "Error: Config Not Written to File"
                    else:
                        print "Config file Written"
                    print ("Conf-File configuration successfull")                

                #Check if file available if not Download
                if self.karaf.verifyBundleExists(app_f)!="ok":
                    if self.karaf.getApp(app_f)!="ok":
                        return "Error: App Not found on Repo"

                #Deploy Bundle do not start yet
                depl_resp=self.karaf.deployBundle(app_f)
                if str(depl_resp)[:5]=="error":
                    return "Error: Bundle Not deployed"

                #Loop to check if deployed if not after 10 checks return erro
                cnt=0
                depl_resp="error"
                while depl_resp[:5]=="error" and cnt<=10:
                    depl_resp=str(self.karaf.getBundleId(app_f))
                    cnt=cnt+1
                    time.sleep(0.1)

                #Final Check
                if str(depl_resp)[:5]!="error":
                    logging.debug("Bundle Deployed with id: "+str(depl_resp))
                else:
                    return "Error: Bundle Id not retreived"
                
                #Start Application
                if self.karaf.startBundle(depl_resp)!="ok":
                    return "Error Starting app"
                else:
                    logging.debug("Bundle Started")

                #delay 100ms or something
                bundle_info=self.karaf.getBundleInfo(depl_resp)
                print bundle_info
                
                #Save config file to configs with name
                if self.karaf.saveDeployFile(name,payload)!="ok":
                    print "Deployment file could not be saved"
                else:
                    print "Deployment file saved"
                #Verify if application started and return stuff
                
                return "success "+str(bundle_info).replace(' ','')

    def removeTask(self,payload):
        d_son=jsonize(payload)
        logging.debug(json.dumps(d_son,indent=2,sort_keys=False))
        if d_son==None:
            return "Error:jsonize"
        else:
            #ToDo:verify cloud,device,region,name,deployment_config
            if self.removeVerify(d_son)!=None:
                return "Error:Verify"
            else:
            #Do Removal Stuff
                return "ok"

    def migrateTask(self,payload):
        d_son=self.jsonize(payload)
        logging.debug(json.dumps(d_son,indent=2,sort_keys=False))
        if d_son==None:
            return "Error:jsonize"
        else:
            #ToDo:verify cloud,device,region,name,deployment_config
            if migrateVerify(d_son)!=None:
                return "Error:Verify"
            else:
                #Do Removal Stuff
                return "ok"

    def deployVerify(self,d_son):
        return None

    def removeVerify(self,d_son):
        return None

    def migrateVerify(self,d_son):
        return None

    def jsonize(self,payload):
        payload=payload.replace("'", '"').replace('\n','').replace('\r','')
        try:
            logging.debug(payload)
            my_json=json.loads(payload);
            return my_json
        except ValueError:
            print "Value Erro, probs something stupid happened"
            return None

    def checkAuth(self,key):
        #Maybe need to consider other mqtt-keys or maybe not 
        if key==Config.get("Mqtt1","admin_api"):
            return True
        else:
            return False

    def on_request(self,ch, method, properties, body):
        cloud_conn=properties.headers.get("cloud")
        source=properties.headers.get("source")
        uuid=properties.headers.get("uuid")
        api_key=properties.headers.get("api_key")
        if (cloud_conn!=None and source!=None and uuid != None and self.checkAuth(api_key)):
            logging.debug("-----Received Request from Cloud-----")
            response = self.resolve(body)
            properties_m=pika.BasicProperties(headers={'name':self.controller_name,'api_key':api_key,'cloud':""+self.cloud_conn, 'source':""+source , 'uuid':uuid, 'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            ch.basic_publish(exchange='cloud_resolve', routing_key='', properties=properties_m ,body=str(response))
            logging.debug("---Request processed and Reponse Sent----")
        else:
            logging.debug("Missing components or failed Auth")
        ch.basic_ack(delivery_tag = method.delivery_tag)

    def getGwInfo(self):
    ##Do with actuall Data From Gateway
        return {"peripherals":["rf24","bluetooth","rf434","Xbee"],"resources":["database","location","metadata"],"apps":"None"}

    def generateRequest(self):
        data={}
        data['request']='register'
        data['name']='Temp_GW_'+str(int(random.random()*8999+1000))
        if (Config.get("General","gateway_uuid").strip()=="None"):
            uuid=''.join(random.choice(ascii_letters) for i in range(16))
            data['uuid']=uuid
            Config.set("General","gateway_uuid",uuid)
            with open(conf_loc,'wb') as configfile:
                Config.write(configfile)
        else:
            data['uuid']=Config.get("General","gateway_uuid").strip()
        data['local_ip']=self.reg.myIp()
        data['hw_addr']=self.reg.myMac()
        data['api_key']=Config.get("Mqtt1","admin_api")
        data['peers']=[self.discoverRegion()]
        data['info']=self.getGwInfo()
        return data

    def initialRequest(self):
        ##Finish custom payload
        payload=self.generateRequest()
        req=str(payload).replace("'",'"')
        logging.debug(req)
        inir=InitReq(Config.get("Mqtt1","user"),Config.get("Mqtt1","pass"),Config.get("Mqtt1","address"),int(Config.get("Mqtt1","port")),payload['name'])
        resp=inir.register(req)
        try:
            my_json=json.loads(resp);
            reg=resolve(my_json['payload'])
            return reg
        except ValueError:
            return "Value Erro on returning Json"

    def init(self):
        credentials = pika.PlainCredentials(Config.get("Amqp","user"),Config.get("Amqp","pass"))
        parameters = pika.ConnectionParameters('localhost',int(Config.get("Amqp","port")),Config.get("Amqp","virt"), credentials)
        self.connection = pika.BlockingConnection(parameters);

        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)        

        self.ini=Init(Config.get("Amqp","user"),Config.get("Amqp","pass"),Config.get("couchDB","user"),Config.get("couchDB","pass"));
        self.channel.basic_consume(self.on_request, queue=Config.get("Admin","queue"))
        self.dev_status=Config.get("Admin","dev_status")
        self.route = Route.Route(self.channel)
        self.karaf=Karaf.Karaf(Config.get("Karaf","user"),Config.get("Karaf","pass"),Config.get("Admin","app_storage"),Config.get("General","location")+"/apps/",Config.get("General","location")+"/configs/",Config.get("Karaf","location")+"/")
        self.device=Device.Device(Config.get("couchDB","user"),Config.get("couchDB","pass"),Config.items("DeviceQ"))
        self.res=Resource.Resource(Config.get("couchDB","user"),Config.get("couchDB","pass"),Config.get("General","Gateway_Name"),Config.items("ResourceQ")) ##Redo Resource so that they are store in config not admin 
        self.reg=Region.Region(Config.get("Amqp","user"),Config.get("Amqp","pass"),Config.get("Amqp","virt"),Config.get("couchDB","user"),Config.get("couchDB","pass"))

        #Do Initial Request and Modify what needs to be modified
        logging.debug("Sending Initial Request to Cloud")
        self.initialRequest()
        #Set variables for later use and start RPC request queueu    
        self.controller_name= Config.get("General","Gateway_Name")


    def shutdown(self):
        self.channel.stop_consuming()
        self.channel.close()
        self.connection.close()

    def run(self):
        self.init()
        try:
            self.channel.start_consuming()
        except Exception,e:
            logging.error(e)
            self.shutdown()
            logging.debug("Exiting Main Thread - Error")
        except KeyboardInterrupt:
            self.shutdown()
            logging.debug("Exiting Main Thread - Keyboard")

if __name__ == "__main2__":
    daemon = admin(PIDFILE)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            try:
                daemon.start()
            except:
                pass
        elif 'stop' == sys.argv[1]:
            print("Stopping ...")
            logging.debug("Driver Stopped")
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            print( "Restaring ...")
            logging.debug("Driver Restarted")
            daemon.restart()
        elif 'status' == sys.argv[1]:
            try:
                pf = file(PIDFILE,'r')
                pid = int(pf.read().strip())
                pf.close()
            except IOError:
                pid = None
            except SystemExit:
                pid = None

            if pid:
                print( 'YourDaemon is running as pid %s' % pid)
            else:
                print( 'YourDaemon is not running.')
        else:
            print( "Unknown command")
            sys.exit(2)
            sys.exit(0)
    else:
        print( "usage: %s start|stop|restart|status" % sys.argv[0])
        sys.exit(2)

if __name__ == "__main__":
    admin=admin()
    try:
        admin.run()
    except Exception , e:
        logging.debug(e)
        admin.shutdown()
        logging.debug("Exiting Main Thread - Keyboard")
    except KeyboardInterrupt:
        admin.shutdown()
        logging.debug("Exiting Main Thread - Keyboard")
