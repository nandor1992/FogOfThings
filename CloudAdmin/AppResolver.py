#!usr/bin/python

import couchdb

class AppResolver:

	def __init__(self,db_usr,db_pass,host):
		self.couch=couchdb.Server('http://'+db_usr+':'+db_pass+'@'+host+':5984/')


	def getData(self,app):
		db=self.couch['apps']
		look=db.view('views/name')
		for p in look[app]:
			doc=db[p.value]
			doc=dict(doc)
			del(doc['_attachments'])
			del(doc['_rev'])
			return doc
		return None


if __name__ == '__main__':
    #Config Settings#
    print("App Resolver")
    app=AppResolver("admin","hunter","10.0.0.134")
    print(app.getData("Test_App1"))