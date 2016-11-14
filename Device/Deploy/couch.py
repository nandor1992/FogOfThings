import couchdb
couch = couchdb.Server('http://admin:hunter@127.0.0.1:5984/')
#db = couch.create('test') # newly created
db= couch['test']
print(db['2fd23a3905ce773e2c5acc63ec000bba'])
couch.delete('test')
