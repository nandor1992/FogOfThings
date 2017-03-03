#!/usr/bin/env python
import couchdb
class monitor():
    def __init__(self,c_user,c_pass):
        self.c_user=c_user
        self.c_pass=c_pass
        self.couch=couchdb.Server('http://'+c_user+':'+c_pass+'@127.0.0.1:5984/')

    def getData(self,start,end):
        db=self.couch['monitoring']
        look=db.view('views/dates',startkey=start,endkey=end)
        for p in look:
            print(p.value)

if __name__ == "__main__":
   m=monitor("admin","hunter")
   start="2017-03-02 10:51"
   end="2017-03-03 10:01"
   m.getData(start,end)
