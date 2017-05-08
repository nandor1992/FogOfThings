#Code Snippets
#!/usr/bin/env python
#Not Actually working code, just old code that was taken out and might be usefull (a code base of some sorts)
class Snippet():
    
    def migrateTask(self,payload):
        ##Migration Resolving
        migrate=self.jsonize(payload)
        gate_n=migrate['gateway']
        name=migrate['name']
        if migrate==None:
            return "Error:jsonize"
        else:
            gate_v=migrate
            logging.debug("Migrating Started!")
            ##Devices -- add queue and add device to type
            if 'devices' in gate_v:
                for dev_t in gate_v['devices'].keys():
                    #Route
                    logging.debug("Add route for dev_type: "+dev_t+" devs:"+str(gate_v['devices'][dev_t]))
                    dev_l=self.device.getSpecDevList(dev_t,self.dev_status,self.controller_name) #Change Idle to Available
                    driver=""
                    for dev_s in dev_l:
                        driver=Config.get("DeviceQ",dev_s["driver"])
                    for d in gate_v['devices'][dev_t]:
                        self.route.add("federation."+self.controller_name,driver,{"app":name,"device":d})
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
                    self.route.addQueue("reg_"+str(r["name"]))
                    if 'key' in r:
                        self.route.add("federation."+self.controller_name,"reg_"+str(r['name']),{"app":name,"region":str(r['name']),"key":str(r['key'])})
                        self.route.addExBind("region","federation."+gate_n,{"app":name,"region":str(r['name']),"key":str(r['key'])})
                    else:
                        self.route.add("federation."+self.controller_name,"reg_"+str(r['name']),{"app":name,"region":str(r['name'])})
                        self.route.addExBind("region","federation."+gate_n,{"app":name,"region":str(r['name'])})

            ##Apps 
            if 'apps' in gate_v:
                #Route
                for a in gate_v['apps']:
                    logging.debug("Add Route for App:" +str(a))
                    self.route.add("federation."+self.controller_name,"karaf_app",{"app_rec":a})
                    self.route.addExBind("apps","federation."+gate_n,{"app":a})
                    self.karaf.addMigratedApp([a],"forward")
                self.route.add("federation."+self.controller_name,"karaf_app",{"app_rec":name})
                self.route.addExBind("apps","federation."+gate_n,{"app_rec":name})
                self.karaf.addMigratedApp([name],"backward");
            ##Resources
            if 'resources' in gate_v:
                #Route
                for re in gate_v['resources']:
                    logging.debug("Add Route for Resource:" +str(re))
                    res_queue=self.res.getResourceQue(str(re))
                    if res_queue!=None:
                       self.res.initializeRes(re,name)
                       self.route.add("federation."+self.controller_name,res_queue,{"app":name,"res":str(re)})
                       self.route.addExBind("resource","federation."+gate_n,{"app":name})
                       
        logging.debug("Migration configuration successfull")

    def demigrateTask(self,payload):
        ##DeMigration Resolving
        migrate=self.jsonize(payload)
        gate_n=migrate['gateway']
        name=migrate['name']
        if migrate==None:
            return "Error:jsonize"
        else:
            gate_v=migrate
            logging.debug("UnMigrating Started!")
            ##Devices -- add queue and add device to type
            if 'devices' in gate_v:
                for dev_t in gate_v['devices'].keys():
                    #Route
                    logging.debug("Remove route for dev_type: "+dev_t+" devs:"+str(gate_v['devices'][dev_t]))
                    dev_l=self.device.getSpecDevList(dev_t,self.dev_status,self.controller_name) #Change Idle to Available
                    driver=""
                    for dev_s in dev_l:
                        driver=Config.get("DeviceQ",dev_s["driver"])
                    for d in gate_v['devices'][dev_t]:
                        self.route.remove("federation."+self.controller_name,driver,{"app":name,"device":d})
                        ##self.route.addExUnBind("device","federation."+gate_n,{"device":d})
            ##Cloud
            if 'cloud' in gate_v:
                #Route
                for c in gate_v['cloud']:
                    logging.debug("Remove route for cloud conn: "+str(c))
                    ##Maybe need to check queue for cloud and refractor everything to always check for this 
                    self.route.addExUnBind("cloud","federation."+gate_n,{"app":name,"cloud":c})
                    self.route.addExUnBind("federation."+self.controller_name,"cloud_resolve",{"app":name,"cloud":c})

            ##Region
            if 'region' in gate_v:
                #Route
                logging.debug("Remove route for region conn: "+str(r['name']))
                self.route.removeQueue("reg_"+str(r["name"]))
                if 'key' in r:
                    self.route.remove("federation."+self.controller_name,"reg_"+str(r['name']),{"app":name,"region":str(r['name']),"key":str(r['key'])})
                    self.route.addExUnBind("region","federation."+gate_n,{"app":name,"region":str(r['name']),"key":str(r['key'])})
                else:
                    self.route.remove("federation."+self.controller_name,"reg_"+str(r['name']),{"app":name,"region":str(r['name'])})
                    self.route.addExUnBind("region","federation."+gate_n,{"app":name,"region":str(r['name'])})

            ##Apps 
            if 'apps' in gate_v:
                #Route
                for a in gate_v['apps']:
                    logging.debug("Remove Route for App:" +str(a))
                    ###Mayvbe others using same apps
                    ##ToDo: Need to delete the configurations for forwarding inside as well
                    self.route.remove("federation."+self.controller_name,"karaf_app",{"app_rec":a})
                    self.route.addExUnBind("apps","federation."+gate_n,{"app":a})                            
                    self.karaf.removeMigratedApp([a])
                self.route.remove("federation."+self.controller_name,"karaf_app",{"app_rec":name})
                self.route.addExUnBind("apps","federation."+gate_n,{"app_rec":name})
                self.karaf.removeMigratedApp([name]);    
            ##Resources
            if 'resources' in gate_v:
                #Route
                for re in gate_v['resources']:
                    logging.debug("Remove Route for Resource:" +str(re))
                    res_queue=self.res.getResourceQue(str(re))
                    if res_queue!=None:
                       self.res.deleteRes(re,name)
                       self.route.remove("federation."+self.controller_name,res_queue,{"app":name,"res":str(re)})
                       self.route.addExUnBind("resource","federation."+gate_n,{"app":name})
                       
        logging.debug("Migration configuration successfull")

    def removeTask2(self,payload):
        name=str(payload).strip()
        logging.debug(name)
        doc=self.res.getDeployFile(name)
        if doc==None:
            return "Error: "+name+" not found"
        else:
            #ToDo:verify cloud,device,region,name,deployment_config
            if self.removeVerify(doc)!=None:
                return "Error:Verify"
            else:
            #Do Removal Stuff
                #Get Variables for werk"
                if 'comm' in doc:
                    if 'cloud' in doc['comm']:
                        cloud=doc["comm"]["cloud"]
                    else:
                        cloud=None
                    if 'region' in doc['comm']:
                        region=doc["comm"]["region"]
                    else:
                        region=None
                    if 'devices' in doc['comm']:
                        devices=doc["comm"]["devices"]
                    else:
                        devices=None
                    if 'resources' in doc['comm']:
                        resource=doc["comm"]["resources"]
                    else:
                        resource=None
                    if 'apps' in doc['comm']:
                        apps=doc.get("comm").get("apps")
                    else:
                        apps=None
                else:
                    cloud=None
                    region=None
                    devices=None
                    resource=None
                    apps=None
                if 'migration' in doc:
                    migrate=doc["migration"]
                else:
                    migration=None
                if 'deployment' in doc:
                    conf_f=str(doc["deployment"]["config"]["file"])
                    conf=doc["deployment"]["config"]["custom_params"]
                else:
                    conf_f=None
                    conf=None
                if 'file' in doc:
                    app_f=str(doc["file"])
                else:
                    app_f=None

                name=str(doc["name"])
                desc=str(doc["description"])
                #Connection Stuff
                ##ToDo: See if app had connection if yes delete that one
                ##Do Cloud
                if len(cloud)!=0:
                    logging.debug("Cloud Unconfig Started")
                    for con in cloud:
                        self.route.remove("cloud_resolve",str(con),{"app":name,"cloud":str(con)})
                    self.route.remove("apps_resolve","karaf_app",{"app":name})
                ##Do Device - Check if other apps have connections
                ##Nothing to do with devices locked to app

                ##Fix Device Stuff
                if 'fix_devices' in doc.get("comm"):
                    fix=d_son.get("comm").get("fix_devices")
                    logging.debug("Fix Device UnConfig started")
                    for dev_t in fix.keys():
                    #Route
                        logging.debug("Remove route for dev_type: "+dev_t+" devs:"+str(fix[dev_t]))
                        dev_l=self.device.getSpecDevList(dev_t,self.dev_status,self.controller_name) #Change Idle to Available
                        driver=""
                        for dev_s in dev_l:
                            driver=Config.get("DeviceQ",dev_s["driver"])
                        for d in fix[dev_t]:
                            self.route.remove("device_resolve",driver,{"device":d,"app":name})
                    logging.debug("Fix Device UnConfig successfull")
                    
                ##Do Region - Delete Regions connection for this app
                if len(region)!=0:
                    logging.debug("Region Deconfig Started")
                    for reg in region:
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
                if len(resource)!=0:
                    logging.debug("Resource Un-Config Started")
                    for res_1 in resource:
                        res_queue=self.res.getResourceQue(str(res_1))
                        if res_queue!=None:
                            self.res.deleteRes(res_1,name)
                            self.route.remove("resource_resolve",res_queue,{"app":name,"res":str(res_1)})
                    self.route.remove("apps_resolve","karaf_app",{"app":name})
                    logging.debug("Resource connection un-configuration successfull")
                
                ##Check if anything migrated to app, delete those connections
                if migrate!=None:
                    logging.debug("Migration Un-Config Started")
                    ##Do magic Here
                    ##Basically forward anything and everything that has the correct name to karaf app and app_resolver ? 
                    for gate_n in migrate.keys():
                        gate_v=migrate[gate_n]
                        logging.debug("Working on: "+gate_n)
                        ##Devices -- add queue and add device to type
                        if 'devices' in gate_v:
                            for dev_t in gate_v['devices'].keys():
                                #Route
                                logging.debug("Rmoving route for dev_type: "+dev_t+" devs:"+str(gate_v['devices'][dev_t]))
                                for d in gate_v['devices'][dev_t]:
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
                            #Route
                            logging.debug("Remove route for region conn: "+str(r['name']))
                            if 'key' in r:
                                self.route.remove("federation."+self.controller_name,"karaf_app",{"app":name,"region":r['name'],"key":r['key']})
                                self.route.addExUnBind("apps","federation."+gate_n,{"app":name,"region":r['name'],"key":r['key']})
                            else:
                                self.route.remove("federation."+self.controller_name,"karaf_app",{"app":name,"region":r['name']})
                                self.route.addExUnBind("apps","federation."+gate_n,{"app":name,"region":r['name']})                                

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

                #Housekeeping
                ## Resource done at comm    
                ## Delete bundle from Karaf
                logging.debug("Deleting Bundle from Karaf")
                del_id=str(self.karaf.getBundleId(app_f))
                if self.karaf.delBundle(del_id)=="ok":
                    logging.debug("Deleted Bundle: "+del_id)
                else:
                    return "Error: Deletin App"
                    
                ##Delte Conf-file
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
                
                return "success: Removed "+name+" from Gateway"

    def MigrationPart(self):
                    ##To-Do: Figure Out how to modify the freaking Config to Suit This!!!!
                if migrate!=None:
                    logging.debug("Migration Config Started")
                    ##Do magic Here
                    ##Basically forward anything and everything that has the correct name to karaf app and app_resolver ? 
                    for gate_n in migrate.keys():
                        gate_v=migrate[gate_n]
                        logging.debug("Working on: "+gate_n)
                        ##Devices -- add queue ande add device to type
                        if 'devices' in gate_v:
                            for dev_t in gate_v['devices'].keys():
                                #Config
                                dev_n=gate_v['devices'][dev_t]
                                if 'dev_'+dev_t in list_conf:
                                    list_conf['dev_'+dev_t]=list_conf['dev_'+dev_t]+":"+":".join(dev_n)
                                else:
                                    list_conf['dev_'+dev_t]=":".join(dev_n)
                                #Route
                                logging.debug("Add route for dev_type: "+dev_t+" devs:"+str(dev_n))
                                for d in dev_n:
                                    conn_devs.append(d)
                                    self.route.add("federation."+self.controller_name,"karaf_app",{"device":d})
                                    self.route.addExBind("apps","federation."+gate_n,{"app":name,"device":d})
                        ##Cloud
                        if 'cloud' in gate_v:
                            #Config
                            if 'cloud' in list_conf:
                                list_conf['cloud']=list_conf['cloud']+":"+":".join(gate_v['cloud'])
                            else:
                                list_conf['cloud']=":".join(gate_v['cloud'])
                            #Route
                            for c in gate_v['cloud']:
                                logging.debug("Add route for cloud conn: "+str(c))
                                self.route.add("federation."+self.controller_name,"karaf_app",{"app":name,"cloud":c})
                                self.route.addExBind("apps","federation."+gate_n,{"app":name,"cloud":c})
                        ##Region
                        if 'region' in gate_v:
                            for r in gate_v['region']:
                                #Config
                                if 'region' in list_conf:
                                    if 'key' in r:
                                        list_conf['region']=list_conf['region']+":"+str(r['name']+";"+str(r['key']))
                                    else:
                                        list_conf['region']=list_conf['region']+":"+str(r['name'])+";None"
                                else:
                                    if 'key' in r:
                                        list_conf['region']=str(r['name'])+";"+str(r['key'])
                                    else:
                                        list_conf['region']=str(r['name'])+";None"
                                #Route
                                logging.debug("Add route for region conn: "+str(r['name']))
                                if 'key' in r:
                                    self.route.add("federation."+self.controller_name,"karaf_app",{"app":name,"region":r['name'],"key":r['key']})
                                    self.route.addExBind("apps","federation."+gate_n,{"app":name,"region":r['name'],"key":r['key']})
                                else:
                                    self.route.add("federation."+self.controller_name,"karaf_app",{"app":name,"region":r['name']})
                                    self.route.addExBind("apps","federation."+gate_n,{"app":name,"region":r['name']})                                

                        ##Apps ###Modify amqp to event
                        if 'apps' in gate_v:
                            #Config
                            if 'apps' in list_conf:
                                list_conf['apps']=list_conf['apps']+":"+":".join(gate_v['apps'])
                            else:
                                list_conf['apps']=":".join(gate_v['apps'])
                            #Route
                            for a in gate_v['apps']:
                                logging.debug("Add Route for App:" +str(a))
                                self.route.add("federation."+self.controller_name,"karaf_app",{"app_rec":a})
                                self.route.addExBind("apps","federation."+gate_n,{"app_rec":a})
                                self.karaf.addMigratedApp([a],"backward")
                            self.route.add("federation."+self.controller_name,"karaf_app",{"app_rec":name})
                            self.route.addExBind("apps","federation."+gate_n,{"app":name})
                            self.karaf.addMigratedApp([name],"forward")
                        ##Resources
                        if 'resources' in gate_v:                         
                            #Config
                            if 'resources' in list_conf:
                                list_conf['resources']=list_conf['resources']+":"+":".join(gate_v['resources'])
                            else:
                                list_conf['resources']=":".join(gate_v['resources'])
                            #Route
                            for re in gate_v['resources']:
                                logging.debug("Add Route for Resource:" +str(re))
                                self.route.add("federation."+self.controller_name,"karaf_app",{"app":name,"res":re})
                                self.route.addExBind("apps","federation."+gate_n,{"app":name,"res":re}) 
                    logging.debug("Migration configuration successfull")
     
