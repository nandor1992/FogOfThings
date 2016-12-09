#! /usr/bin/env python
# vim: set fenc=utf8 ts=4 sw=4 et :
#
# Layer 2 network neighbourhood discovery tool
# written by Benedikt Waldvogel (mail at bwaldvogel.de)

from __future__ import absolute_import, division, print_function
import logging
import scapy.config
import scapy.layers.l2
import scapy.route
import socket
import math
import errno
import pycurl
import os, sys
import json
from StringIO import StringIO

class Region:
    def __init__(self,rab_user,rab_pass,vhost,c_user,c_pass):
        self.rab_user=rab_user
        self.rab_pass=rab_pass
        self.rab_vhost=vhost
        self.c_user=c_user
        self.c_pass=c_pass

    def addCouchNode(self,ip,user,passw):
        buffer=StringIO()
        c=pycurl.Curl()
        host="http://10.0.0.68:5986/_nodes/couchdb@"+ip
        c.setopt(c.URL,host)
        c.setopt(c.WRITEDATA,buffer)
        c.setopt(c.USERPWD,'%s:%s' %(self.c_user,self.c_pass))
        data = '{}'
        c.setopt(c.POSTFIELDS,data)
        c.setopt(c.CUSTOMREQUEST,"PUT")
        c.perform()
        resp=c.getinfo(c.RESPONSE_CODE)
        c.close()
        print(resp)
        print(buffer.getvalue())
        if resp==200:
            return buffer.getvalue()
        else:
            return "Error"         

    def removeCouchNode(self,ip,user,passw):
        buffer=StringIO()
        c=pycurl.Curl()
        host="http://10.0.0.68:5984/_nodes/couchdb@"+ip
        c.setopt(c.URL,host)
        c.setopt(c.WRITEDATA,buffer)
        c.setopt(c.USERPWD,'%s:%s' %(self.c_user,self.c_pass))
        data = '{}'
        c.setopt(c.POSTFIELDS,data)
        c.setopt(c.CUSTOMREQUEST,"DELETE")
        c.perform()
        resp=c.getinfo(c.RESPONSE_CODE)
        c.close()
        print(resp)
        print(buffer.getvalue())
        if resp==200:
            return buffer.getvalue()
        else:
            return "Error"     

        
    def getCouchNodes(self):
        buffer=StringIO()
        c=pycurl.Curl()
        host="http://127.0.0.1:5984/_membership"
        c.setopt(c.URL,host)
        c.setopt(c.WRITEDATA,buffer)
        c.setopt(c.USERPWD,'%s:%s' %(self.c_user,self.c_pass))
        c.setopt(c.CUSTOMREQUEST,"GET")
        c.perform()
        resp=c.getinfo(c.RESPONSE_CODE)
        c.close()
        if resp==200:
            return buffer.getvalue()
        else:
            return "Error"         

    def setClustQueue(self,name):
        c=pycurl.Curl()
        #c.setopt(c.URL,"http://localhost:15672/api/paremeters/federation-upstream/%2f/my-upstream")
        c.setopt(c.URL,"http://localhost:15672/api/exchanges/"+self.rab_vhost+"/federation."+name)
        c.setopt(c.CUSTOMREQUEST,"PUT")
        c.setopt(pycurl.HTTPHEADER,['Content-type: application/json'])
        data = '{"auto_delete":false,"durable":true}'
        c.setopt(c.POSTFIELDS,data)
        c.setopt(c.USERPWD,'%s:%s' %(self.rab_user,self.rab_pass))
        c.perform()
        resp=c.getinfo(c.HTTP_CODE)
        c.close()
        if resp==204:
            return "ok"
        else:
            return "Error"

    def createFedPolicy(self):
        buffer=StringIO()
        c=pycurl.Curl()
        #c.setopt(c.URL,"http://localhost:15672/api/paremeters/federation-upstream/%2f/my-upstream")
        host="http://localhost:15672/api/policies/"+self.rab_vhost+"/federate-me"
        c.setopt(c.URL,host)
        c.setopt(c.WRITEDATA,buffer)
        c.setopt(c.USERPWD,'%s:%s' %(self.rab_user,self.rab_pass))
        c.setopt(pycurl.HTTPHEADER,['Content-type: application/json'])
        data2 = json.dumps({"pattern":"^federation\.","definition":{"federation-upstream-set":"all"},"apply-to":"exchanges"})
        c.setopt(pycurl.POSTFIELDS,data2)
        c.setopt(c.CUSTOMREQUEST,"PUT")
        c.perform()
        resp=c.getinfo(c.RESPONSE_CODE)
        c.close()
        if resp==204:
            return "ok"
        else:
            return "Error"

    def addUpstream(self,user,passw,addr,virt):
        buffer=StringIO()
        c=pycurl.Curl()
        host="http://localhost:15672/api/parameters/federation-upstream/"+self.rab_vhost+"/Fed-upstream"
        c.setopt(c.URL,host)
        c.setopt(c.WRITEDATA,buffer)
        c.setopt(c.USERPWD,'%s:%s' %(self.rab_user,self.rab_pass))
        c.setopt(pycurl.HTTPHEADER,['Content-type: application/json'])
        data2 = json.dumps({"value":{"uri":"amqp://"+user+":"+passw+"@"+addr+"/"+virt,"ack-mode":"on-confirm","trust-user-id":True}})
        print(data2)
        c.setopt(pycurl.POSTFIELDS,data2)
        c.setopt(c.CUSTOMREQUEST,"PUT")
        c.perform()
        resp=c.getinfo(c.RESPONSE_CODE)
        c.close()
        if resp==204:
            return "ok"
        else:
            return "Error"        
        
    ## Below only for Discovery of Stuff
    def long2net(self,arg):
        if (arg <= 0 or arg >= 0xFFFFFFFF):
            raise ValueError("illegal netmask value", hex(arg))
        return 32 - int(round(math.log(0xFFFFFFFF - arg, 2)))


    def to_CIDR_notation(self,bytes_network, bytes_netmask):
        network = scapy.utils.ltoa(bytes_network)
        netmask = self.long2net(bytes_netmask)
        net = "%s/%s" % (network, netmask)
        if netmask < 16:
            print("%s is too big. skipping" % net)
            return None
        return net


    def scan_and_print_neighbors(self,net, interface, ref, timeout=1):
        results=[]
        try:
            ans, unans = scapy.layers.l2.arping(net, iface=interface, timeout=timeout, verbose=False)
            for s, r in ans.res:
                try:
                    hostname = socket.gethostbyaddr(r.psrc)
                    if (r.sprintf("%Ether.src%")[0:8].upper()==ref.upper()):
                        results.append([r.sprintf("%Ether.src%"),r.sprintf("%ARP.psrc%"),hostname[0]])
                except socket.herror:
                # failed to resolve
                    pass
        except socket.error as e:
            if e.errno == errno.EPERM:     # Operation not permitted
                print("%s. Did you run as root?", e.strerror)
            else:
                raise
        return results

    def getNetw(self):
        networks=[]
        for network, netmask, _, interface, address in scapy.config.conf.route.routes:
            if network == 0 or interface == 'lo' or address == '127.0.0.1' or address == '0.0.0.0':
                continue
            if netmask <= 0 or netmask == 0xFFFFFFFF:
                continue
            if interface != scapy.config.conf.iface:
            # see http://trac.secdev.org/scapy/ticket/537
                print("skipping %s because scapy currently doesn't support arping on non-primary network interfaces", net)
                continue
            net = self.to_CIDR_notation(network, netmask)
            if net:
                networks.append([net,interface])
        return networks

    def getDevsOnWan(self,ref):
        networks = self.getNetw()
        res=[]
        for [net,interface] in networks:
            res=res+reg.scan_and_print_neighbors(net, interface,ref)
        return res
    
if __name__ == "__main__":
    reg=Region("admin","hunter","test","admin","hunter")
    print(reg.getCouchNodes())
   # print(reg.removeCouchNode("10.0.0.68","admin","hunter"))
    print(reg.addCouchNode("10.0.0.67","admin","hunter"))
    #print(reg.setClustQueue('test'))
    #print(reg.createFedPolicy()) # This is Raspi
    #print(reg.addUpstream("admin","hunter","10.0.0.68","test"))
