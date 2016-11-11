#!/usr/bin/env python

class Resource:
    def __init__(self):
        self.name="resource"

    def getResourceQue(self,name):
        return "res_"+name
        #else return None

    def initializeRes(self,res,app):
        return "ok"
