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
PIDFILE="/home/pi/FogOfThings/Device/pid/admin.pid"
LOGFILE = Config.get("Log","location")+'/admin.log'
logging.basicConfig(filename=LOGFILE,level=logging.DEBUG)
logging.getLogger("pika").setLevel(logging.ERROR)

class admin():
#class admin(Daemon):

    def resolve(self,payload):
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
            logging.debug("Bundle Task")
            if components[1]=='deploy':
                logging.debug("Deploy Bundle")
                response=self.deployTask(" ".join(components[2:]))
            elif components[1]=='remove':
                logging.debug("Remove Bundle")
                response=self.removeTask(" ".join(components[2:]))
            else:
                logging.debug("No subtask found")
        elif components[0]=='migrate':
            logging.debug("Migrate Task")
            app=components[2]
            gw=components[3]
            if components[1]=='add':
                logging.debug("Set up migration")
                response=self.migrateAdd(app,gw)
            elif components[1]=='remove':
                logging.debug("Remove migration setup ")
                response=self.migrateRemove(app,gw)
            elif components[1]=='away':
                logging.debug("Migrate app away")
                response=self.migrateAway(app,gw)
            elif components[1]=='back':
                logging.debug("Migrate app back")
                response=self.migrateBack(app,gw)
            elif components[1]=='change':
                logging.debug("Change Destination of App migrate")
                response=self.migrateChange(app,gw)
            else:
                logging.debug("Command Not Found")
                response="Sub Migrate Not Found"
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
                ret=ast.literal_eval("  ".join(components[2:]))
                self.reg.addGwToDatabase(ret['peer_name'],ret['peer_ip'],ret['peer_mac'])
                self.reg.addCouchNode(ret['peer_ip'])
                self.reg.addUpstream("admin","hunter",ret['peer_ip'],"test")
            ##Add node to Couchdb and Rabbitmq cluster, update Database with it's value
            elif components[1]=='addAsNode':
                ## Add new node as upstream for Star Connection
                ret=ast.literal_eval("  ".join(components[2:]))
                self.reg.addUpstream("admin","hunter",ret['peer_ip'],"test")
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
                    self.ini.initRabbitmq(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))+"/RabbitVersions/rabbit_bare.json")
                    self.reg.setClustQueue(ret['name'])
                    #To-Do:Modify to add Updstream for all Other Nodes
                    self.reg.createFedPolicy(ret['name'])
                    self.reg.addUpstream("admin","hunter",ret['master'],"test")
                elif components[2]=='initClust':
                    logging.debug("Initialize new Cluster you are Master") ## Working Case - Done
                    ##To-Do
                    ret=ast.literal_eval("  ".join(components[3:]))
                    self.modifyConfig(ret['reg_api'],ret['name'],ret['reg_name'],None)
                    self.ini.initRabbitmq(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))+"/RabbitVersions/rabbit_Base_04-18.json")
                    self.ini.initCouchDB(Config.items("DeviceQ"))
                    self.reg.setClustQueue(ret['name'])
                    self.reg.createFedPolicy(ret['name'])
                    self.reg.initClustDatabase(ret['reg_name'],ret['reg_api'],ret['name'],self.reg.myIp(),self.reg.myMac())
                elif components[2]=='update':
                    logging.debug("New Ip for me the Master")
                ##To-Do
        else:
            logging.debug("No task found")
        return response


    def modifyConfig(self,reg_api,name,clust_name,admin):
        Config.set('General','gateway_name',name)
        Config.set('General','configured',True)
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
            logging.debug("Source:"+source+" Dest_name:"+dest_name)
            args={}
            result=""
            for item in my_j["header"]:
                args[item["property"]]=item["value"]
            if kind=="add":
                result=route.add(source,dest_name,args)
            if kind=="remove":
                result=route.remove(source,dest_name,args)
            return result

    def migrateAdd(self,app,gw):
        logging.debug("Migration Add for App: "+app+" Gateway: "+gw)
        doc=self.res.getDeployFile(app,gw)
        if doc==None:
            return "Error: "+app+" not found"
        else:
            name=app
            gate_n=gw
            if 'device' in doc:
                for dev_t in doc['device'].keys():
                    #Route
                    for d in doc['device'][dev_t]:
                        logging.debug("Add route for dev_type: "+dev_t+" dev:"+str(d))
                        self.route.add("federation."+self.controller_name,"karaf_app",{"device":d})
                        self.route.addExBind("apps","federation."+gw,{"app":app,"device":d})
            if 'cloud' in doc:
                for c in doc['cloud']:
                    logging.debug("Add route for cloud conn: "+str(c))
                    self.route.add("federation."+self.controller_name,"karaf_app",{"app":app,"cloud":c})
                    self.route.addExBind("apps","federation."+gw,{"app":app,"cloud":c})
            if 'region' in doc:
                for r in doc['region']:
                #Route
                    logging.debug("Add route for region conn: "+str(r['name']))
                    if 'key' in r:
                        self.route.add("federation."+self.controller_name,"karaf_app",{"app":name,"region":r['name'],"key":r['key']})
                        self.route.addExBind("apps","federation."+gw,{"app":name,"region":r['name'],"key":r['key']})
                    else:
                        self.route.add("federation."+self.controller_name,"karaf_app",{"app":name,"region":r['name']})
                        self.route.addExBind("apps","federation."+gw,{"app":name,"region":r['name']})
            if 'apps' in doc:
                #Route
                for a in doc['apps']:
                    logging.debug("Add Route for App:" +str(a))
                    self.route.add("federation."+self.controller_name,"karaf_app",{"app":a})
                    self.route.addExBind("apps","federation."+gate_n,{"app_rec":a})
                    self.karaf.addMigratedApp([a],"backward")
                self.route.add("federation."+self.controller_name,"karaf_app",{"app_rec":name})
                self.route.addExBind("apps","federation."+gate_n,{"app":name})
                self.karaf.addMigratedApp([name],"forward")
            if 'resources' in doc:                         
                #Route
                for re in doc['resources']:
                    logging.debug("Add Route for Resource:" +str(re))
                    self.route.add("federation."+self.controller_name,"karaf_app",{"app":name,"res":re})
                    self.route.addExBind("apps","federation."+gate_n,{"app":name,"res":re})

                            #Create file with added params and existing ones from previous components
            if 'config' in doc and 'config_file' in doc:
                logging.debug("Conf-File Config Started")
                conf_f=doc['config_file']
                lst=[]
                for param in doc['config']:
                        lst.append(""+param+" = "+doc['config'][param])
                if self.karaf.createConfig(conf_f,lst)!="ok":
                    return "Error: Config Not Written to File"
                else:
                   logging.debug("Config file Written")
                logging.debug("Conf-File configuration successfull")                

            #Check if file available if not Download
            if 'file' in doc and 'AppId' in doc:
                app_f=doc['file']
                app_uuid=doc['AppId']
                if self.karaf.verifyBundleExists(app_f)!="ok":
                    if self.karaf.getApp(app_uuid,app_f)!="ok":
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
                logging.debug(bundle_info)
            return "ok"
        
    def migrateRemove(self,app,gw):
        logging.debug("Migration Remove for App: "+app+" Gateway: "+gw)
        doc=self.res.getDeployFile(app,gw)
        if doc==None:
            return "Error: "+app+" not found"
        else:
            name=app
            gate_n=gw
            gate_v=doc
            logging.debug("Migration Un-Config Started")
            ##Do magic Here
            ##Basically forward anything and everything that has the correct name to karaf app and app_resolver ? 
            if 'device' in gate_v:
                for dev_t in gate_v['device'].keys():
                    #Route
                    logging.debug("Rmoving route for dev_type: "+dev_t+" devs:"+str(gate_v['device'][dev_t]))
                    for d in gate_v['device'][dev_t]:
                        if len(self.device.checkAppsForDev(gw,self.controller_name,d))==0:
                        ##Need to check if anyone else needs it for these 
                            self.route.addExUnBind("device","federation."+gate_n,{"device":d})
                        ##Need to check if anyone else needs it for these 
                        ##self.route.remove("federation."+self.controller_name,"karaf_app",{"device":d})
                        self.route.addExUnBind("apps","federation."+gate_n,{"app":name,"device":d})
            ##Cloud
            if 'cloud' in gate_v:
                #Route
                for c in gate_v['cloud']:
                    logging.debug("Remove route for cloud conn: "+str(c))
                    self.route.remove("federation."+self.controller_name,"karaf_app",{"app":name,"cloud":c})
                    self.route.addExUnBind("apps","federation."+gate_n,{"app":name,"cloud":c})
            ##Region
            if 'region' in gate_v:
                for r in gate_v['region']:
                    #Route
                    logging.debug("Add route for region conn: "+str(r['name']))
                    if 'key' in r:
                        self.route.remove("federation."+self.controller_name,"karaf_app",{"app":name,"region":str(r['name']),"key":str(r['key'])})
                        self.route.addExUnBind("apps","federation."+gate_n,{"app":name,"region":str(r['name']),"key":str(r['key'])})
                    else:
                        self.route.remove("federation."+self.controller_name,"karaf_app",{"app":name,"region":str(r['name'])})
                        self.route.addExUnBind("apps","federation."+gate_n,{"app":name,"region":str(r['name'])})                                            

            ##Apps ###Modify amqp to event
            if 'apps' in gate_v:
                #Route
                ##To-Do: Add app forwarding removal as well
                for a in gate_v['apps']:
                    logging.debug("Remove Route for App:" +str(a))
                    self.route.remove("federation."+self.controller_name,"karaf_app",{"app_rec":a})
                    self.route.addExUnBind("apps","federation."+gate_n,{"app_rec":a})                            
                    self.karaf.removeMigratedApp([a])
                self.route.remove("federation."+self.controller_name,"karaf_app",{"app_rec":name})
                self.route.addExUnBind("apps","federation."+gate_n,{"app":name})
                self.karaf.removeMigratedApp([name])
            ##Resources
            if 'resources' in gate_v:
                #Route
                for re in gate_v['resources']:
                    logging.debug("Remove Route for Resource:" +str(re))
                    self.route.remove("federation."+self.controller_name,"karaf_app",{"app":name,"res":re})
                    self.route.addExUnBind("apps","federation."+gate_n,{"app":name,"res":re}) 
            logging.debug("Migration un-configuration successfull")

            ##Housekeeping
            logging.debug("Deleting Bundle from Karaf")
            if 'file' in doc:
                app_f=doc["file"]
                del_id=str(self.karaf.getBundleId(app_f))
                if self.karaf.delBundle(del_id)=="ok":
                    logging.debug("Deregleted Bundle: "+del_id)
                else:
                    return "Error: Deletin App"
                
            ##Delte Conf-file
            if 'config_file' in doc:
                conf_f=doc.get("config_file")
                if conf_f!=None:
                    logging.debug("Conf-File Removal Started")
                    if self.karaf.delConfig(conf_f)!="ok":
                        return "Error: Config File not deleted"
                    else:
                        logging.debug("Config file Deleted")
                logging.debug("Conf-File removal successfull")                       
            return "ok"

    
    def migrateAway(self,app,gw):
        logging.debug("Migration Away for App: "+app+" Gateway: "+gw)
        doc=self.res.getDeployFile(app,self.controller_name)
        if doc==None:
            return "Error: "+app+" not found"
        else:
            name=app
            gate_n=gw
            gate_v=doc
            #Remove Current Config
            #Do Cloud
            logging.debug("Cloud Unconfig Started")
            if 'cloud' in doc:
                self.route.remove("apps_resolve","karaf_app",{"app":name})

            ###Do Devices
            if 'device' in doc:
                devs=doc["device"]
                for dev_type in devs:
                    for dev in devs[dev_type]:
                        self.route.remove("apps_resolve","karaf_app",{"device":dev})
                        logging.debug("Removed Dev Type: "+dev_type+" Device:"+dev)
                
            ##Do Region - Delete Regions connection for this app
            logging.debug("Region Deconfig Started")
            if 'region' in doc:
                for reg in doc["region"]:
                    if str(reg["key"])=="":
                        self.route.remove("region_resolve","reg_"+str(reg["name"]),{"app":name,"region":str(reg["name"])})
                        self.route.addExUnBind("region","apps_resolve",{"app":name,"region":str(reg["name"])})
                    else:
                        self.route.remove("region_resolve","reg_"+str(reg["name"]),{"app":name,"region":str(reg["name"])})
                        self.route.addExUnBind("region","apps_resolve",{"app":name,"region":str(reg["name"]),"key":str(reg["key"])})
                self.route.remove("apps_resolve","karaf_app",{"app":name})
                logging.debug("Region connection un-configuration successfull") 

            ##Do Resource
            logging.debug("Resource Un-Config Started")
            if 'resources' in doc:
                self.route.remove("apps_resolve","karaf_app",{"app":name})
                logging.debug("Resource connection un-configuration successfull")
            ###    
            #Add Migration Stuff
            ###
            if 'device' in gate_v:
                for dev_t in gate_v['device'].keys():
                    #Route
                    logging.debug("Add route for dev_type: "+dev_t+" devs:"+str(gate_v['device'][dev_t]))
                    for d in gate_v['device'][dev_t]:
                        self.route.addExBind("federation."+self.controller_name,"device_resolve",{"app":name,"device":d})
                        self.route.addExBind("device","federation."+gate_n,{"device":d})
            ##Cloud
            if 'cloud' in gate_v:
                #Route
                for c in gate_v['cloud']:
                    logging.debug("Add route for cloud conn: "+str(c))
                    ##Maybe need to check queue for cloud and refractor everything to always check for this 
                    self.route.addExBind("cloud","federation."+gate_n,{"app":name,"cloud":c})
                    self.route.addExBind("federation."+self.controller_name,"cloud_resolve",{"app":name,"cloud":c})

            ##Region
            if 'region' in gate_v:
                for r in gate_v['region']:
                    #Route
                    logging.debug("Add route for region conn: "+str(r['name']))
                    if 'key' in r:
                        self.route.add("federation."+self.controller_name,"reg_"+str(r['name']),{"app":name,"region":str(r['name']),"key":str(r['key'])})
                        self.route.addExBind("region","federation."+gate_n,{"app":name,"region":str(r['name']),"key":str(r['key'])})
                    else:
                        self.route.add("federation."+self.controller_name,"reg_"+str(r['name']),{"app":name,"region":str(r['name'])})
                        self.route.addExUnBind("region","federation."+gate_n,{"app":name,"region":str(r['name'])})           

            ##Apps 
            if 'apps' in gate_v:
                #Route
                for a in gate_v['apps']:
                    logging.debug("Add Route for App:" +str(a))
                    self.route.add("federation."+self.controller_name,"karaf_app",{"app_rec":a})
                    self.route.addExBind("apps","federation."+gate_n,{"app":a})
                    self.karaf.addMigratedApp([a],"forward")
                self.route.add("federation."+self.controller_name,"karaf_app",{"app":name})
                self.route.addExBind("apps","federation."+gate_n,{"app_rec":name})
                self.karaf.addMigratedApp([name],"backward");
            ##Resources
            if 'resources' in gate_v:
                #Route
                for re in gate_v['resources']:
                    logging.debug("Add Route for Resource:" +str(re))
                    res_queue=self.res.getResourceQue(str(re))
                    if res_queue!=None:
                       self.route.add("federation."+self.controller_name,res_queue,{"app":name,"res":str(re)})
                       self.route.addExBind("resource","federation."+gate_n,{"app":name,"res":str(re)})
            ##Housekeeping
            logging.debug("Deleting Bundle from Karaf")
            if 'file' in doc:
                app_f=doc["file"]
                del_id=str(self.karaf.getBundleId(app_f))
                if self.karaf.delBundle(del_id)=="ok":
                    logging.debug("Deregleted Bundle: "+del_id)
                else:
                    return "Error: Deletin App"
                
            ##Delte Conf-file
            if 'config_file' in doc:
                conf_f=doc.get("config_file")
                if conf_f!=None:
                    logging.debug("Conf-File Removal Started")
                    if self.karaf.delConfig(conf_f)!="ok":
                        return "Error: Config File not deleted"
                    else:
                        logging.debug("Config file Deleted")
                logging.debug("Conf-File removal successfull")
            #Set Current Gw and save Deployment File
            self.res.updateDeplFile(app,self.controller_name,gw)
            return "ok"
    
    def migrateBack(self,app,gw):
        logging.debug("Migration Back for App: "+app+" Gateway: "+gw)
        doc=self.res.getDeployFile(app,self.controller_name)
        if doc==None:
            return "Error: "+app+" not found"
        else:
            name=app
            gate_n=doc['current_gateway']
            gate_v=doc
            #Remove old Config
            if 'device' in gate_v:
                for dev_t in gate_v['device'].keys():
                    #Route
                    logging.debug("Removing route for dev_type: "+dev_t+" devs:"+str(gate_v['device'][dev_t]))
                    for d in gate_v['device'][dev_t]:
                        self.route.addExUnBind("federation."+self.controller_name,"device_resolve",{"device":d,"app":app})
                        if len(self.device.checkAppsForDev(self.controller_name,app,d))==0:
                        ##Need to check if anyone else needs it for these 
                            self.route.addExUnBind("device","federation."+gate_n,{"device":d})
            ##Cloud
            if 'cloud' in gate_v:
                #Route
                for c in gate_v['cloud']:
                    logging.debug("Remove route for cloud conn: "+str(c))
                    self.route.addExUnBind("federation."+self.controller_name,"cloud_resolve",{"app":name,"cloud":c})
                    self.route.addExUnBind("cloud","federation."+gate_n,{"app":name,"cloud":c})
            ##Region
            if 'region' in gate_v:
                for r in gate_v['region']:
                    #Route
                    logging.debug("Add route for region conn: "+str(r['name']))
                    if 'key' in r:
                        self.route.remove("federation."+self.controller_name,"reg_"+str(r['name']),{"app":name,"region":str(r['name']),"key":str(r['key'])})
                        self.route.addExUnBind("region","federation."+gate_n,{"app":name,"region":str(r['name']),"key":str(r['key'])})
                    else:
                        self.route.remove("federation."+self.controller_name,"reg_"+str(r['name']),{"app":name,"region":str(r['name'])})
                        self.route.addExUnBind("region","federation."+gate_n,{"app":name,"region":str(r['name'])})                           

            ##Apps
            if 'apps' in gate_v:
                #Route
                ##To-Do: Add app forwarding removal as well
                for a in gate_v['apps']:
                    logging.debug("Remove Route for App:" +str(a))
                    self.route.remove("federation."+self.controller_name,"karaf_app",{"app_rec":a})
                    self.route.addExUnBind("apps","federation."+gate_n,{"app":a})                            
                    self.karaf.removeMigratedApp([a])
                self.route.remove("federation."+self.controller_name,"karaf_app",{"app":name})
                self.route.addExUnBind("apps","federation."+gate_n,{"app_rec":name})
                self.karaf.removeMigratedApp([name])
            ##Resources
            if 'resources' in gate_v:
                #Route
                for re in gate_v['resources']:
                    logging.debug("Remove Route for Resource:" +str(re))
                    self.route.remove("federation."+self.controller_name,"res_"+str(re),{"app":name,"res":re})
                    self.route.addExUnBind("resource","federation."+gate_n,{"app":name,"res":re}) 
            logging.debug("Migration un-configuration successfull")
            #####
            #Add new Config
            if 'cloud' in doc:
                self.route.add("apps_resolve","karaf_app",{"app":name})

            ###Do Devices
            if 'device' in doc:
                devs=doc["device"]
                for dev_type in devs:
                    for dev in devs[dev_type]:
                        self.route.add("apps_resolve","karaf_app",{"device":dev})
                        logging.debug("Removed Dev Type: "+dev_type+" Device:"+dev)
                
            ##Do Region - Delete Regions connection for this app
            logging.debug("Region Deconfig Started")
            if 'region' in doc:
                for reg in doc["region"]:
                    if str(reg["key"])=="":
                        self.route.add("region_resolve","reg_"+str(reg["name"]),{"app":name,"region":str(reg["name"])})
                        self.route.addExBind("region","apps_resolve",{"app":name,"region":str(reg["name"])})
                        self.route.add("apps_resolve","karaf_app",{"app":name})
                    else:
                        self.route.add("region_resolve","reg_"+str(reg["name"]),{"app":name,"region":str(reg["name"])})
                        self.route.addExBind("region","apps_resolve",{"app":name,"region":str(reg["name"]),"key":str(reg["key"])})
                        self.route.add("apps_resolve","karaf_app",{"app":name})
                    self.route.add("apps_resolve","karaf_app",{"app":name})
                logging.debug("Region connection un-configuration successfull") 

            ##Do Resource
            logging.debug("Resource Un-Config Started")
            if 'resources' in doc:
                self.route.add("apps_resolve","karaf_app",{"app":name})
                logging.debug("Resource connection un-configuration successfull")
            ##To-Do Re-deploy app

                             #Create file with added params and existing ones from previous components
            if 'config' in doc and 'config_file' in doc:
                logging.debug("Conf-File Config Started")
                conf_f=doc['config_file']
                lst=[]
                for param in doc['config']:
                        lst.append(""+param+" = "+doc['config'][param])
                if self.karaf.createConfig(conf_f,lst)!="ok":
                    return "Error: Config Not Written to File"
                else:
                   logging.debug("Config file Written")
                logging.debug("Conf-File configuration successfull")                

            #Check if file available if not Download
            if 'file' in doc and 'AppId' in doc:
                app_f=doc['file']
                app_uuid=doc['AppId']
                if self.karaf.verifyBundleExists(app_f)!="ok":
                    if self.karaf.getApp(app_uuid,app_f)!="ok":
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
                logging.debug(bundle_info)
            #Set Current Gw and save Deployment File
            self.res.updateDeplFile(app,self.controller_name,self.controller_name)
            return "ok"

    
    def migrateChange(self,app,gw):
        logging.debug("Migration Change for App: "+app+" Gateway: "+gw)
        doc=self.res.getDeployFile(app,self.controller_name)
        if doc==None:
            return "Error: "+app+" not found"
        else:
            name=str(app)
            gate_n=str(doc['current_gateway'])
            gate_v=doc
            #Remove old Config
            if 'device' in gate_v:
                for dev_t in gate_v['device'].keys():
                    #Route
                    logging.debug("Removing route from gw: "+gate_n+" for dev_type: "+dev_t+" devs:"+str(gate_v['device'][dev_t]))
                    for d in gate_v['device'][dev_t]:
                        if len(self.device.checkAppsForDev(self.controller_name,app,d))==0:
                        ##Need to check if anyone else needs it for these 
                            self.route.addExUnBind("device","federation."+gate_n,{"device":d})
            ##Cloud
            if 'cloud' in gate_v:
                #Route
                for c in gate_v['cloud']:
                    logging.debug("Remove route for cloud conn: "+str(c))
                    self.route.addExUnBind("cloud","federation."+gate_n,{"app":name,"cloud":c})

            ##Region
            if 'region' in gate_v:
                for r in gate_v['region']:
                    #Route
                    logging.debug("Add route for region conn: "+str(r['name']))
                    if 'key' in r:
                        self.route.addExUnBind("region","federation."+gate_n,{"app":name,"region":str(r['name']),"key":str(r['key'])})
                    else:
                        self.route.addExUnBind("region","federation."+gate_n,{"app":name,"region":str(r['name'])})                                    

            ##Apps ###Modify amqp to event
            if 'apps' in gate_v:
                #Route
                ##To-Do: Add app forwarding removal as well
                for a in gate_v['apps']:
                    logging.debug("Remove Route for App:" +str(a))
                    self.route.addExUnBind("apps","federation."+gate_n,{"app":a})                            
                    self.karaf.removeMigratedApp([a])
                self.route.addExUnBind("apps","federation."+gate_n,{"app_rec":name})
                self.karaf.removeMigratedApp([name])
            ##Resources
            if 'resources' in gate_v:
                #Route
                for re in gate_v['resources']:
                    logging.debug("Remove Route for Resource:" +str(re))
                    self.route.addExUnBind("resource","federation."+gate_n,{"app":name,"res":re}) 
            logging.debug("Migration un-configuration successfull")
            #Add new Config
            #Set new Gw as default gate_n
            gate_n=gw
            if 'device' in gate_v:
                for dev_t in gate_v['device'].keys():
                    #Route
                    logging.debug("Add route for dev_type: "+dev_t+" devs:"+str(gate_v['device'][dev_t]))
                    for d in gate_v['device'][dev_t]:
                        self.route.addExBind("device","federation."+gate_n,{"device":d})
            ##Cloud
            if 'cloud' in gate_v:
                #Route
                for c in gate_v['cloud']:
                    logging.debug("Add route for cloud conn: "+str(c))
                    ##Maybe need to check queue for cloud and refractor everything to always check for this 
                    self.route.addExBind("cloud","federation."+gate_n,{"app":name,"cloud":c})

            ##Region
            if 'region' in gate_v:
                for r in gate_v['region']:
                    #Route
                    logging.debug("Add route for region conn: "+str(r['name']))
                    if 'key' in r:
                        self.route.addExBind("region","federation."+gate_n,{"app":name,"region":str(r['name']),"key":str(r['key'])})
                    else:
                        self.route.addExBind("region","federation."+gate_n,{"app":name,"region":str(r['name'])})

            ##Apps 
            if 'apps' in gate_v:
                #Route
                for a in gate_v['apps']:
                    logging.debug("Add Route for App:" +str(a))
                    self.route.addExBind("apps","federation."+gate_n,{"app":a})
                    self.karaf.addMigratedApp([a],"forward")
                self.route.addExBind("apps","federation."+gate_n,{"app_rec":name})
                self.karaf.addMigratedApp([name],"backward");
            ##Resources
            if 'resources' in gate_v:
                #Route
                for re in gate_v['resources']:
                    logging.debug("Add Route for Resource:" +str(re))
                    res_queue=self.res.getResourceQue(str(re))
                    if res_queue!=None:
                       self.route.addExBind("resource","federation."+gate_n,{"app":name,"res":str(re)})
            #Set Current Gw and save Deployment File
            self.res.updateDeplFile(app,self.controller_name,gw)
        return "ok"
    
    def deployTask(self,payload):
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
                list_conf={}
                if 'comm' in d_son:
                    if 'cloud' in d_son['comm']:
                        cloud=d_son["comm"]["cloud"]
                    else:
                        cloud=None
                    if 'region' in d_son['comm']:
                        region=d_son["comm"]["region"]
                    else:
                        region=None
                    if 'devices' in d_son['comm']:
                        devices=d_son["comm"]["devices"]
                    else:
                        devices=None
                    if 'resources' in d_son['comm']:
                        resource=d_son["comm"]["resources"]
                    else:
                        resource=None
                    if 'apps' in d_son['comm']:
                        apps=d_son.get("comm").get("apps")
                    else:
                        apps=None
                else:
                    cloud=None
                    region=None
                    devices=None
                    resource=None
                    apps=None
                if 'migration' in d_son:
                    migrate=d_son["migration"]
                else:
                    migration=None
                if 'deployment' in d_son:
                    conf_f=str(d_son["deployment"]["config"]["file"])
                    conf=d_son.get("deployment").get("config").get("custom_params")
                else:
                    conf_f=None
                    conf=None
                if 'file' in d_son:
                    app_f=str(d_son["file"])
                else:
                    app_f=None
                if '_id'in d_son and 'name' in d_son and 'description' in d_son:
                    app_uuid=str(d_son.get("_id"))
                    name=str(d_son.get("name"))
                    desc=str(d_son.get("description"))
                else:
                    return "Error: App uuid, or name or description not present"

                #Add Device Name
                list_conf["name"]=name
                deployment={}
                deployment['name']=name
                deployment['AppId']=app_uuid
                deployment['host_gateway']=Config.get("General","gateway_name")
                deployment['current_gateway']=Config.get("General","gateway_name")
                deployment['cluster']=Config.get("Cluster","cluster_name")
                deployment['cloud']=[]
                deployment['device']={}
                deployment['apps']=[]
                deployment['resources']=[]
                deployment['region']=[]
                deployment['config']={}
                deployment['config_file']=conf_f
                deployment['file']=app_f
                #Cloud Stuff
                if cloud!=None:
                    logging.debug("Cloud Config Started")
                    conf_cloud=""
                    deployment['cloud']=[str(i) for i in cloud]
                    for con in cloud:
                        result1=self.route.add("cloud_resolve",str(con),{"app":name,"cloud":str(con)})
                        conf_cloud=conf_cloud+con+":"
                    result1b=self.route.add("apps_resolve","karaf_app",{"app":name})
                    list_conf["cloud"]=str(conf_cloud[:-1])
                    if result1!="ok" or result1b!="ok":
                        return "Error: Cloud Connection Setup"
                    else:
                        logging.debug("Cloud connection configuration successfull")
                #Device Stuff
                ##To-DO: Add Configured Devices to Deployment part of config maybe
                conn_devs=[]
                if devices!=None:
                    logging.debug("Devices Config Started")
                    for dev in devices:
                        dev_l=self.device.getSpecDevList(dev["type"],self.dev_status,self.controller_name) #Change Idle to Available
                        if len(dev_l)<int(dev["required"]):
                            return "Error: Not Enough Required Devices"
                    for dev in devices:
                        dev_l=self.device.getSpecDevList(dev["type"],self.dev_status,self.controller_name) #Change Idle to Available
                        dev_conf=""
                        deployment['device'][str(dev['type'])]=[]
                        if dev["cnt"]=="":
                            for dev_s in dev_l:
                                dev_conf=dev_conf+":"+str(dev_s["id"])
                                deployment['device'][str(dev['type'])].append(str(dev_s['id']))
                                result1=self.route.add("apps_resolve","karaf_app",{"device":dev_s["id"]})
                                conn_devs.append(dev_s["id"])

                                if dev["reserve"]=="No":
                                    result2=self.route.add("device_resolve",Config.get("DeviceQ",dev_s["driver"]),{"device":dev_s["id"]})
                                else:
                                    result2=self.route.add("device_resolve",Config.get("DeviceQ",dev_s["driver"]),{"device":dev_s["id"],"app":name})
                        else:
                            for i in range(0,int(dev["cnt"])):
                                dev_conf=dev_conf+":"+str(dev_l[i]["id"])
                                deployment['device'][str(dev['type'])].append(str(dev_l[i]["id"]))
                                result1=self.route.add("apps_resolve","karaf_app",{"device":dev_l[i]["id"]})
                                conn_devs.append(dev_l[i]["id"])
                                if dev["reserve"]=="No":
                                    result2=self.route.add("device_resolve",Config.get("DeviceQ",dev_l[i]["driver"]),{"device":dev_l[i]["id"]})
                                else:
                                    result2=self.route.add("device_resolve",Config.get("DeviceQ",dev_l[i]["driver"]),{"device":dev_l[i]["id"],"app":name})
                        list_conf["dev_"+dev["type"]]=str(dev_conf[1:])                      
                        if result1!="ok" or result2!="ok":
                            return "Error: Devices Connection Setup"
                    logging.debug("Device connection configuration successfull")               

                ##Fix Device Stuff
                if 'comm' in d_son:
                    if 'fix_devices' in d_son.get("comm"):
                        fix=d_son.get("comm").get("fix_devices")
                        logging.debug("Fix Device Config started")
                        for dev_t in fix.keys():
                        #Route
                            logging.debug("Add route for dev_type: "+dev_t+" devs:"+str(fix[dev_t]))
                            dev_l=self.device.getSpecDevList(dev_t,self.dev_status,self.controller_name) #Change Idle to Available
                            driver=""
                            for dev_s in dev_l:
                                driver=Config.get("DeviceQ",dev_s["driver"])
                            for d in fix[dev_t]:
                                
                                self.route.add("apps_resolve","karaf_app",{"device":d})
                                self.route.add("device_resolve",driver,{"device":d,"app":name})
                                #Config
                                if 'dev_'+dev_t in list_conf:
                                    list_conf['dev_'+dev_t]=list_conf['dev_'+dev_t]+":"+":".join(d)
                                    deployment['device'][dev_t].append(d)
                                else:
                                    list_conf['dev_'+dev_t]=":".join(d)
                                    deployment['device'][dev_t]=[]
                                    deployment['device'][dev_t].append(d)
                        logging.debug("Fix device Config successfull")
                    
                #Region Stuff
                #ToDO: Add Part to Notify Region of this maybe
                if region!=None:
                    logging.debug("Region Config Started")
                    region_conf=""
                    for reg in region:
                        result2=self.route.addQueue("reg_"+str(reg["name"]))
                        if str(reg["key"])=="":
                            deployment['region'].append({'name':str(reg['name'])})
                            region_conf=region_conf+str(reg["name"])+";None:";
                            result2b=self.route.add("region_resolve","reg_"+str(reg["name"]),{"app":name,"region":str(reg["name"])})
                            result2d=self.route.addExBind("region","apps_resolve",{"app":name,"region":str(reg["name"])})
                            result3=self.route.add("apps_resolve","karaf_app",{"app":name})
                        else:
                            deployment['region'].append({'name':str(reg['name']),'key':str(reg['key'])})
                            region_conf=region_conf+str(reg["name"])+";"+str(reg['key'])+":";
                            result2b=self.route.add("region_resolve","reg_"+str(reg["name"]),{"app":name,"region":str(reg["name"])})
                            result2d=self.route.addExBind("region","apps_resolve",{"app":name,"region":str(reg["name"]),"key":str(reg["key"])})
                            result3=self.route.add("apps_resolve","karaf_app",{"app":name})
                    result2c=self.route.add("apps_resolve","karaf_app",{"app":name})
                    list_conf["region"]=str(region_conf[:-1])
                    if result2!="ok" or result2b!="ok" or result2c!="ok" or result2b!="ok" or result3!="ok":
                        return "Error: Region Connection Setup"
                    else:
                        logging.debug("Region connection configuration successfull")

                #Apps Stuff
                if apps!=None:
                    logging.debug("Apps Config Started")
                    must_l=self.res.getDeployedApps(apps["required_apps"])
                    int_l=self.res.getDeployedApps(apps["interrested_apps"])
                    if len(apps["required_apps"])!=len(must_l):
                        return "Error: Required Apps Not met"
                    deployment['apps']=must_l+int_l
                    apps_list=":".join(must_l)+":".join(int_l)
                    if len(must_l)+len(int_l)!=0:
                        list_conf["apps"]=str(apps_list)
                    logging.debug("Apps connection configuration successfull")

                #Resource Stuff
                #ToDo: Add part to notify/resolve Resource
                if resource!=None:
                    deployment['resources']=[str(i) for i in resource]
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
                    list_conf["resources"]=str(res_list[:-1])
                    logging.debug("Resource connection configuration successfull")

                ##Migration Resolving!!!!!!!!!!!!!!!!!!
                ##Figure out a way of Doing this!!!!

                    
                #Create file with added params and existing ones from previous components
                if conf_f!=None:
                    logging.debug("Conf-File Config Started")
                    lst=[]
                    for param in list_conf.keys():
                        lst.append(""+param+" = "+list_conf[param])
                        deployment['config'][str(param)]=str(list_conf[param])
                    if conf!=None:
                        for param in conf:
                            lst.append(""+param+" = "+conf[param])
                            deployment['config'][str(param)]=str(conf[param])
                    if self.karaf.createConfig(conf_f,lst)!="ok":
                        return "Error: Config Not Written to File"
                    else:
                       logging.debug("Config file Written")
                    logging.debug("Conf-File configuration successfull")                

                #Check if file available if not Download
                if self.karaf.verifyBundleExists(app_f)!="ok":
                    if self.karaf.getApp(app_uuid,app_f)!="ok":
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
                logging.debug(bundle_info)
                #Addig Devices to payload
                logging.debug(deployment)
                #Save config file to configs with name
                if self.res.deleteDeployedFile(name)=="ok":
                    if self.res.saveDeployFile(name,deployment)!="ok":
                        logging.debug("Deployment file could not be saved")
                    else:
                        logging.debug("Deployment file saved")
                #Verify if application started and return stuff
                
                return deployment

    

    def removeTask(self,payload):
        logging.debug("Remove App: "+payload)
        doc=self.res.getDeployFile(payload,Config.get("General","gateway_name"))
        if doc==None:
            return "Error: "+name+" not found"
        else:
            #ToDo:verify cloud,device,region,name,deployment_config
            if self.removeVerify(doc)!=None:
                return "Error:Verify"
            else:
                name=doc.get("name")
                #Do Cloud
                logging.debug("Cloud Unconfig Started")
                for con in doc.get("cloud"):
                    self.route.remove("cloud_resolve",str(con),{"app":name,"cloud":str(con)})
                    self.route.remove("apps_resolve","karaf_app",{"app":name})


                ###Do Devices
                devs=doc.get("device")
                for dev_type in devs:
                    for dev in devs[dev_type]:
                        if len(self.device.checkAppsForDev(self.controller_name,name,dev))==0:
                            driver=self.device.getDriverForDev(dev)
                            self.route.remove("apps_resolve","karaf_app",{"device":dev})
                            self.route.remove("device_resolve",driver,{"device":dev,"app":name})
                            self.route.remove("device_resolve",driver,{"device":dev})
                        else:
                            self.route.remove("device_resolve",driver,{"device":dev,"app":name})
                        logging.debug("Removed Dev Type: "+dev_type+" Device:"+dev)
                    
                ##Do Region - Delete Regions connection for this app
                logging.debug("Region Deconfig Started")
                for reg in doc.get("region"):
                    self.route.removeQueue("reg_"+str(reg["name"]))
                    if str(reg["key"])=="":
                        self.route.remove("region_resolve","reg_"+str(reg["name"]),{"app":name,"region":str(reg["name"])})
                        self.route.addExUnBind("region","apps_resolve",{"app":name,"region":str(reg["name"])})
                        self.route.remove("apps_resolve","karaf_app",{"app":name})
                    else:
                        self.route.remove("region_resolve","reg_"+str(reg["name"]),{"app":name,"region":str(reg["name"])})
                        self.route.addExUnBind("region","apps_resolve",{"app":name,"region":str(reg["name"]),"key":str(reg["key"])})
                        self.route.remove("apps_resolve","karaf_app",{"app":name})
                    self.route.remove("apps_resolve","karaf_app",{"app":name})
                logging.debug("Region connection un-configuration successfull") 

                ##Do Resource
                logging.debug("Resource Un-Config Started")
                for res_1 in doc.get("resources"):
                    res_queue=self.res.getResourceQue(str(res_1))
                    if res_queue!=None:
                        self.res.deleteRes(res_1,name)
                        self.route.remove("resource_resolve",res_queue,{"app":name,"res":str(res_1)})
                self.route.remove("apps_resolve","karaf_app",{"app":name})
                logging.debug("Resource connection un-configuration successfull")

                #HouseKeeping
                logging.debug("Deleting Bundle from Karaf")
                app_f=doc.get("file")
                del_id=str(self.karaf.getBundleId(app_f))
                if self.karaf.delBundle(del_id)=="ok":
                    logging.debug("Deregleted Bundle: "+del_id)
                else:
                    return "Error: Deletin App"
                    
                ##Delte Conf-file
                conf_f=doc.get("config_file")
                if conf_f!=None:
                    logging.debug("Conf-File Removal Started")
                    if self.karaf.delConfig(conf_f)!="ok":
                        return "Error: Config File not deleted"
                    else:
                        logging.debug("Config file Written")
                logging.debug("Conf-File removal successfull")                       

                ##Delete Deploy file
                if self.res.deleteDeployedFile(name)!="ok":
                    logging.debug("Deployment file could not be deleted")
                else:
                    logging.debug("Deployment file deleted")
                

        return "success: Removed App "+name+" from Gateway"


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
            logging.debug("Value Erro, probs something stupid happened")
            return None

    def checkAuth(self,key):
        #Maybe need to consider other mqtt-keys or maybe not 
        if key==Config.get("Mqtt1","admin_api") or key==Config.get("Cluster","cluster_api"):
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
            response = str(self.resolve(body))
            properties_m=pika.BasicProperties(headers={'name':self.controller_name,'api_key':api_key,'request':'response','cloud':""+cloud_conn, 'source':""+source , 'uuid':uuid, 'datetime':""+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
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
        data['peers']=self.discoverRegion()
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
            reg=self.resolve(my_json['payload'])
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
        self.reg=Region.Region(Config.get("Amqp","user"),Config.get("Amqp","pass"),Config.get("Amqp","virt"),Config.get("couchDB","user"),Config.get("couchDB","pass"))

        #Do Initial Request and Modify what needs to be modified
        logging.debug("Sending Initial Request to Cloud")
        self.initialRequest()
        #Set variables for later use and start RPC request queueu    
        self.controller_name= Config.get("General","gateway_name")
        self.res=Resource.Resource(Config.get("couchDB","user"),Config.get("couchDB","pass"),self.controller_name,Config.items("ResourceQ"))

    def shutdown(self):
        self.channel.stop_consuming()
        self.channel.close()
        self.connection.close()

    def run(self):
        self.init()
        try:
            logging.debug("Awaiting Requests!")
            self.channel.start_consuming()
       # except Exception,e:
         #   logging.error(e)
          #  self.shutdown()
         #   logging.debug("Exiting Main Thread - Error")
        except KeyboardInterrupt:
            self.shutdown()
            logging.debug("Exiting Main Thread - Keyboard")

if __name__ == "__main_2_":
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
  #  except Exception , e:
       # logging.debug(e)
       # admin.shutdown()
       # logging.debug("Exiting Main Thread - Keyboard")
    except KeyboardInterrupt:
        admin.shutdown()
        logging.debug("Exiting Main Thread - Keyboard")
