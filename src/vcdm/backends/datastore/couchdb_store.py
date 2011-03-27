import couchdb
import datetime
from uuid import uuid4
from vcdm.interfaces.datastore import IDatastore

from vcdm import c
from vcdm.errors import InternalError


class CouchDBStore(IDatastore):

    db = None
    
    def __init__(self, initialize = False):
        server = couchdb.Server(c('local', 'datastore.endpoint'))
        if initialize:
            self.db = server.create('meta')
        else:
            # already created?
            self.db = server['meta']
        # make sure we have a top-level folder
        if self.find_by_path('/', 'container')[0] is None:
            self.write({
                        'object': 'container',            
                        'fullpath': '/',
                        'path': '/',
                        'parent_container': '/', 
                        'children': {},
                        'ctime': str(datetime.datetime.now())}, None)
    
    def read(self, docid):        
        return self.db[docid]
    
    def write(self, data, docid = None):
        doc = None
        print "writing data to uid %s\n%s" %(docid, data)
        if docid is None:
            docid = uuid4().hex
            data['_id'] = docid
            self.db.save(data)
        else:
            doc = self.db[docid]
            doc.update(data)
            print "new data\n", doc
            self.db.save(doc)
                                 
        return docid
    
    def exists(self, docid):
        return (docid in self.db)
    
    def delete(self, docid):
        del self.db[docid]
    
    def find_uid_match(self, pattern):
        """ Return UIDs that correspond to a objects with a path matching the pattern """
        
        dirn_fun = '''
        function(doc) {
           if (doc.fullpath.match(/^%s/)) {
               emit(doc.id, doc.fullpath);
           }
        }
        ''' % pattern.replace("/", "\\/")
                  
        return list(self.db.query(dirn_fun))
        
    
    def find_by_path(self, path, object_type = None, fields = None):
        """ Find an object at a given path.
        
        - object_type - optional filter by the type of an object (e.g. blob, container, ...)
        - fields - fields to retrieve from the database. By default only gets UID of an object
        """
        comparision_string = 'true'
        if object_type is not None:
            comparision_string = "doc.object == '%s'" % object_type
                 
        if fields is not None:
            fields = '{' + ','.join([f + ': doc.' + f for f in fields]) + '}'
        else:
            fields = 'null'    
                            
        fnm_fun = '''function(doc) {
            if (doc.fullpath == '%s' && %s ) {
                emit(doc.id, %s);            
            }
        }         
        ''' % (path, comparision_string, fields)
        res = self.db.query(fnm_fun)
        if len(res) == 0:
            return (None, None)
        elif len(res) > 1:
            # XXX: does CDMI allow this in case of references/...?
            raise InternalError("Namespace collision: more than one UID corresponds to an object.")
        else:
            tmp_res = list(res)[0]
            return  (tmp_res.id, tmp_res.value)    
        
    def find_path_uids(self, paths):
        """Return a list of IDs of container objects that correspond to the specified path."""
        comparision_string = ['doc.fullpath == "' + p + '"' for p in paths]
        fnm_fun = '''function(doc) {
            if (doc.object == 'container' && (%s)) {
                emit(doc.id, null);            
            }
        } 
        ''' % ' || '.join(comparision_string)
        res = self.db.query(fnm_fun)
        if len(res) == 0:
            return None        
        else:
            return list(res)
    