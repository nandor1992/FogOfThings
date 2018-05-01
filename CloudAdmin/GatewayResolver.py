#!usr/bin/python
from faker import Factory
import random
import couchdb
from string import ascii_letters,digits
class GatewayResolver:
	def __init__(self,db_usr,db_pass,host):
		self.fake=Factory.create("en_AU")
		self.couch=couchdb.Server('http://'+db_usr+':'+db_pass+'@'+host+':5984/')

	def resolveGateway(self,uuid,ip,hw,peers,info):
		gw=self.checkIfExists(uuid,ip,hw)
		clust=self.checkIfCluster(ip,hw,peers)
		if gw!=None:
			my_clust=self.checkIfCluster(gw[0],gw[3],[[gw[3],gw[0]]])
		else:
			my_clust=self.checkIfCluster(ip,hw,[[hw,ip]])			
		print(gw)
		print(my_clust)
		print(clust)
		if gw==None:
			print("New GW Create it")
			new_gw=self.registerGw(uuid,ip,hw,peers,info)
			if clust==None:
				print("New Clust as Well Create Both")
				new_cls=self.registerNewClust(new_gw,ip,hw)
				new_cls['name']=new_gw
				new_cls['task']="Init"
				return new_cls
			elif clust['reg_role']=="new_slave":
				print("New Node Inside existing cluster")
				new_cls=self.addGwToCluster(clust['_id'],ip,new_gw,hw)
				clust['old_peers']=self.getClusterIPs(clust['_id'])
				clust['reg_role']="slave"
				clust['task']="Add New"
				del(clust['_id'])
				clust['name']=new_gw
				clust['new_clust']=new_cls
				return clust
			else:
				print("New Gateway but it exists inside Cluster - Strange but still Error!")
		else:
			print("Existing Gw")
			self.updateGatewayInfo(gw[2],uuid,ip,hw,peers,info)
			if clust==None:
				print("No Cluster found for Peers")
				if my_clust==None:
					print("No Cluster Found for GW")
					new_cls=self.registerNewClust(gw[1],ip,hw)
					new_cls['name']=gw[1]
					new_cls['task']="Init"
					return  new_cls
				elif my_clust['reg_role']=='master':
					print("Existing Cluster for GW")
					del(my_clust['_id'])
					my_clust['name']=gw[1]
					my_clust['task']="None"
					return my_clust
				else:
					print("Gateway not part of previous cluster anymore Create new")
					old_cls=self.deleteGatewayFromOthers(gw[3],gw[0])
					new_cls=self.registerNewClust(gw[1],ip,hw)
					new_cls['name']=gw[1]
					new_cls['task']="Remove Old"
					new_cls['old_clust']=old_cls
					return  new_cls

			elif clust['reg_role']!="new_slave" and clust['reg_role']!="new_master":
				print("Existing Gateway with known config, just return info")
				del(clust['_id'])
				clust['name']=gw[1]
				clust['task']="None"
				return clust
			elif clust['reg_role']=="new_master":
				print("New Master")
				peers=self.updateClusterInfo(clust['_id'],ip)
				del(clust['_id'])
				clust['name']=gw[1]
				clust['reg_role']="master"
				clust['task']="New Master"
				clust['peers']=peers
				return clust
			else:
				print("Existing Gateway that Switched Cluster ")
				[size,old_peers]=self.checkMyCluster(my_clust['_id'],gw[1])
				old_cls=self.deleteGatewayFromOthers(gw[3],gw[0])
				new_cls=self.addGwToCluster(clust['_id'],ip,gw[1],hw)
				del(clust['_id'])
				clust['name']=gw[1]
				clust['reg_role']="slave"
				if size!=0:
					clust['task']="Notify Workers Add New"
					clust['new_clust']=new_cls
					clust['old_peers']=old_peers
				else:
					if old_cls==[]:
						clust['task']="Add New"
						clust['new_clust']=new_cls
					else:
						clust['task']="Remove Old Add New"
						clust['old_clust']=old_cls
						clust['new_clust']=new_cls
				return clust

	##Check Migration stuff
	def checkApp(self,app,clust,gw):
		ret={}
		a_id=None
		db=self.couch['deployments']
		look=db.view('views/name')
		for p in look[app]:
			a_id=p.value
		c_id=None
		db2=self.couch['clusters']
		look2=db2.view('cluster/unique')
		for p in look2[clust]:
			c_id=p.value
		##Check if everything is where it should be
		if a_id==None or c_id==None:
			ret['type']='Error'
		else:
			doc=db[a_id]
			doc2=db2[c_id]
			if doc['cluster']!=clust or doc['current_gateway']==gw or (gw not in doc2['nodes_name']):
				ret['type']='Error Misfit'
			else:
				#Figure out the type of operation and return variables
				ret['host']=doc['host_gateway']
				ret['current']=doc['current_gateway']
				if doc['current_gateway']==doc['host_gateway']:
					ret['type']='O->N'
				elif doc['host_gateway']==gw:
					ret['type']='N->O'
				else:
					ret['type']='N->N'
		return ret

	

	def updateApp(self,app,gw):
		print("Update Deployment")
		a_id=None
		db=self.couch['deployments']
		look=db.view('views/name')
		for p in look[app]:
			a_id=p.value
		if a_id!=None:
			doc=db[a_id]
			doc['current_gateway']=gw
			##Comment out for actual work
			db[doc.id]=doc
			return "ok"
		else:
			return "Error ID None"
	##Check My Cluster Stuff
	def checkMyCluster(self,id,name):
		db=self.couch['clusters']
		doc=db[id]
		if len(doc['nodes_name'])==1:
			return [0,[]]
		elif doc['master'][1]!=name:
			return [0,[]]
		else:
			ret=[]
			for peer in doc['nodes_name']:
				if peer!=doc['master'][1]:
					ret.append(peer)
			return [len(doc['nodes_name'])-1,ret]

	def getClusterIPs(self,id):
		db=self.couch['clusters']
		doc=db[id]
		return [doc['nodes_name'],doc['nodes_ip']]
	
	def checkIfExists(self,uuid,ip,hw):
		db=self.couch['gateways']
		look=db.view('gateways/find')
		for p in look[[uuid,hw]]:
			return p.value
		return None

	def checkIfCluster(self,ip,hw,peers):
		print(peers)
		db=self.couch['clusters']
		look=db.view('cluster/find')
		clust=None
		for peer in peers:
			for p in look[peer]:
				clust=p.value
		print(clust)
		if clust==None:
			return None
		else:
			if clust[3][0]==ip and clust[2][0]==hw:
				return {'_id': p.value[0],'reg_role':'master','reg_api':p.value[5],'reg_name':p.value[4]}
			elif ip in clust[1] and clust[2][clust[1].index(ip)]==hw:
				return {'_id': p.value[0],'reg_role':'slave','master':p.value[3][0],'reg_api':p.value[5],'reg_name':p.value[4]}
			elif clust[2][0]==hw:
				return {'_id': p.value[0],'reg_role':'new_master','reg_api':p.value[5],'reg_name':p.value[4]}
			else:
				return {'_id': p.value[0],'reg_role':'new_slave','master':p.value[3][0],'reg_api':p.value[5],'reg_name':p.value[4]}

	def registerGw(self,uuid,ip,hw,peers,info):
		#Check if Exists
		print("Register Gw")
		unique=0
		while unique==0:
			name=self.fake.name().split(" ")[1]
			num=int(random.random()*8999+1000)
			ret= name +"_"+str(num)
			db=self.couch['gateways']
			look=db.view('gateways/unique')
			unique=1
			for p in look[ret]:
				unique=0
		##Comment out for actual work
		db.save({'name': ret,'uuid': uuid,'ip': ip,'peers': peers,'hw_addr': hw,'info': info})
		return ret

	def registerNewClust(self,gw_name,ip,hw):
		#Check if exists
		print("Register Cluster")
		unique=0
		while unique==0:
			name=self.fake.name().split(" ")[0]
			num=int(random.random()*8999+1000)
			ret= "Cluster_"+name +"_"+str(num)
			reg_api=''.join(random.choice(ascii_letters) for i in range(16))
			db=self.couch['clusters']
			look=db.view('cluster/unique')
			unique=1
			for p in look[ret]:
				unique=0
		#Comment out for actual work
		db.save({'reg_api': reg_api,'reg_name': ret,'nodes_ip': [ip],'nodes_name': [gw_name],'nodes_mac': [hw],'master': [ip,gw_name]})
		return {'reg_role':'master','reg_api':reg_api,'reg_name':ret}

	def addGwToCluster(self,id,ip,name,mac):
		print("Add Gw To Existing Cluster")
		db=self.couch['clusters']
		doc=db[id]
		doc['nodes_mac'].append(mac)
		doc['nodes_name'].append(name)
		doc['nodes_ip'].append(ip)
		##Comment out for actual work
		db[doc.id]=doc
		return doc['master'][1]

	def deleteGatewayFromOthers(self,mac,ip):
		print("Delete Gateway from existing cluster")
		db=self.couch['clusters']
		look=db.view('cluster/find')
		clusts=[]
		for p in look[mac,ip]:
			doc=db[p.value[0]]
			##Comment out for actual work
			if doc['master'][0]==ip:
				db.delete(doc) 
				pass
			else:
				node_index=doc['nodes_mac'].index(mac)
				doc['nodes_mac'].pop(node_index)
				doc['nodes_name'].pop(node_index)
				doc['nodes_ip'].pop(node_index)
				clusts.append(doc['master'][1])
				db[doc.id]=doc
		return clusts

	def updateGatewayInfo(self,id,uuid,ip,hw,peers,info):
		print("Updating Gateway Info")
		db=self.couch['gateways']
		doc=db[id]
		doc['uuid']=uuid
		doc['ip']=ip
		doc['hw_addr']=hw
		doc['info']=info
		doc['peers']=peers
		##Comment out for actual work
		db[doc.id]=doc

	def updateClusterInfo(self,id,ip):
		print("Updating Cluster Info")
		db=self.couch['clusters']
		doc=db[id]
		doc['master'][0]=ip
		##Comment out for actual work
		db[doc.id]=doc
		peers = []
		leader=doc['master'][1]
		for names in doc['nodes_name']:
			if names!=leader:
				peers.append(names)
		return peers

	def checkIfClustGW(self,clust,gw):
		db=self.couch['clusters']
		look=db.view('cluster/unique')
		for p in look[clust]:
			doc=db[p.value]
			if set(gw).issubset(doc['nodes_name']):
				return "ok"
		return "Not Found"

	def saveDeployment(self, my_json):
		db=self.couch['deployments']
		try:
			print(my_json)
			del(my_json['_id'])
			del(my_json['_rev'])
			db.save(my_json)
			return "ok"
		except Exception,e:
			print(e)
			return "Error"

if __name__ == '__main__':
    #Config Settings#
    print("Gateway Resolver")
    gw=GatewayResolver("admin","hunter","10.0.0.134")
    print(gw.checkApp("Test_App1","Cluster_Jasmine_1529","James_2345"))
    #print(gw.deleteGatewayFromOthers("b9:27:eb:c5:ed:e4","10.0.0.68"))
    #ip="10.0.0.23";uuid="TestUUIDG41W1";hw="b84:27:eb:c5:ed:e4"; peers=[["b9:27:eb:c5:ed:e4","10.0.0.68"]]                                     # Cluster Master
    #ip="10.0.0.71";uuid="TestUUIDGW1";hw="b8:27:eb:c5:ed:e4"; peers=[["b1:27:eb:c5:ed:e4","10.0.0.69"]]                                     # Cluster Master moved as slave to new cluster
    #ip="10.0.0.71";uuid="TestUUIDGW1";hw="b8:27:eb:c5:ed:e4"; peers=[["b9:27:eb:c5:ed:e4","10.0.0.68"]]                                     # Cluster Master changed ip address 
    #ip="10.0.0.68";uuid="TestUUIDGW2"; hw="b9:27:eb:c5:ed:e4"; peers=[["b8:27:eb:c5:ed:e4","10.0.0.67"]]    								# Cluster Slave
    #ip="10.0.0.23";uuid="TestUUIDGW2"; hw="b9:27:eb:c5:ed:e4"; peers=[["b8:27:eb:c5:ed:e4","10.0.0.67"]]    								# Cluster Slave new ip 
    #ip="10.0.0.68";uuid="TestUUIDGW2"; hw="b9:27:eb:c5:ed:e4"; peers=[]                                   # Cluster Slave Moved to New Clust
    #ip="10.0.0.69";uuid="TestUUIDGW3";hw="b1:27:eb:c5:ed:e4";peers=[["b8:27:eb:c5:ed:e4","10.0.0.67"],["b9:27:eb:c5:ed:e4","10.0.0.68"]]   # Existing Gateway New Cluster
    #ip="10.0.0.70";uuid="TestUUIDGW3";hw="b1:27:eb:c5:ed:e4"; peers=[]   																	 # Existing Gateway No Peers 
    #ip="10.0.0.267";uuid="TestUUIDGW4";hw="b3:27:eb:c5:ed:e4"; peers=[["b8:27:eb:c5:ed:e4","10.0.0.67"],["b9:27:eb:c5:ed:e4","10.0.0.68"]]  # New GW in cluster
    #ip="10.0.0.368";uuid="TestUUIDGW5";hw="b3:27:ef:c5:ed:e4"; peers=[["b3:27:eb:c5:ed:e4","10.0.0.367"]]                                    # New Gw new cluster
    #print(gw.resolveGateway(uuid,ip,hw,peers,"Just some random info to add, probs should be json 2"))
    #print(gw.checkIfClustGW("Cluster_Jasmine_1529","James_2344"))
    #print(gw.getClusterIPs('697bbbe0e7f3d065ae4652d71000b0ea'))
    #print(gw.checkIfClustGW("Cluster_Cindy_1636",["Erickson_2204"]))
    #print(gw.checkIfClustGW("Cluster_Cindy_1636",["Vazquez_7663","Erickson_2204","Sunny Side Up "]))  
    #print(gw.checkIfCluster("Cluster_Cindy_16326",["Erickson_2204"])) 
    #gw.checkIfCluster("10.0.0.51","gr9fafaf",[["b8:27:eb:57:e7:84","10.0.0.68"]])
