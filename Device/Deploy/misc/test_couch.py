#!/usr/bin/python

import datetime
import couchdb
couch = couchdb.Server('http://admin:hunter@127.0.0.1:5984/')
db=couch['admin']
db.save({'type':'deviec','database':["blue","rf24","xbee","rf434"],'queue':["ardu_blue","ardu_rf24","ardu_xbee","atmega_rfa1"]})
#db=couch.create('admin')
#couch.delete('database')
#map_fun = '''function(doc){
    #    emit(doc.dev_type,[doc.dev_id,doc.sensors]);
  #     }'''
#result=db.query(map_fun)
#res=None
#for p in result['ardUnoTemp']:
#    res=p.value[1][1]
#print res
    
