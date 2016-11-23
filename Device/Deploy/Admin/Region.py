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

class Region:
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
                    print(r.sprintf("%Ether.src%")[0:8]+" - "+r.sprintf("%ARP.psrc%"))
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
        reg=Region()
        print(reg.getDevsOnWan("B8:27:EB")) # This is Raspi
