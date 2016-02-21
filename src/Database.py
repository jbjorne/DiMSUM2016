import time
import os
import shutil
import dataset

class Database():
    def __init__(self, filePath=None, copyFrom=None, clear=False):
        self.filePath = filePath
        self.verbose = True
        self.db = self._openDB(filePath, copyFrom=copyFrom, clear=clear)
        self.defaultCacheSize = 100000
        self.cacheSize = {}
        self.cache = {}
        self.dbPath = None
    
    def _openDB(self, dbPath, copyFrom=None, clear=False):
        if (clear or (copyFrom != None)) and os.path.exists(dbPath):
            print "Removing existing database at", dbPath
            os.remove(dbPath)
        if copyFrom:
            print "Copying database from", dbPath
            shutil.copy2(copyFrom, dbPath)
        dbPath = "sqlite:///" + os.path.abspath(dbPath)
        self.dbPath = dbPath
        print "Opening database at", dbPath
        return dataset.connect(dbPath)
    
    def _reconnect(self):
        if self.dbPath:
            self.db = dataset.connect(self.dbPath)
    
    def exists(self, tableName):
        rows = [x for x in self.db.query("SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';".replace("{table_name}", tableName))]
        return len(rows) > 0
        #self._reconnect()
        #print tableName, self.db._tables, self.db.tables, (tableName in self.db._tables), (tableName in self.db.tables)
        #return (tableName in self.db._tables) and (tableName in self.db.tables)
    
    def drop(self, name, reInitCacheSize=-1):
        print "Dropping table", name
        self.db[name].drop()
        assert not self.exists(name)
        assert name not in self.db._tables
        if reInitCacheSize > -1:
            self.initCache(name, reInitCacheSize)
    
    def dropTables(self, names, reInitCacheSize=-1):
        for name in names:
            self.drop(name, reInitCacheSize)
    
    def initCache(self, table, cacheSize=None):
        self.cache[table] = []
        self.cacheSize[table] = self.defaultCacheSize if (cacheSize == None) else cacheSize
    
    def insert(self, table, row, immediate=False):
        if table not in self.cache:
            self.initCache(table)
        self.cache[table].append(row)
        self._insertCached(table, 0 if immediate else self.cacheSize[table])
    
    def insert_many(self, table, rows, immediate=False):
        if table not in self.cache:
            self.initCache(table)
        self.cache[table].extend(rows)
        self._insertCached(table, 0 if immediate else self.cacheSize[table])
    
    def flush(self):
        for table in sorted(self.cache.keys()):
            self._insertCached(table)
    
    def _insertCached(self, tableName, chunkSize=0):
        if chunkSize == 0: # insert all available rows
            chunkSize = len(self.cache[tableName])
        # Insert rows if enough are available
        rows = self.cache[tableName]
        if len(rows) >= chunkSize and len(rows) > 0:
            if not self.exists(tableName):
                #print self.db.tables, self.db.metadata.tables.keys(), self.db._tables.keys()
                print "Inserting initial row for table", self.db[tableName]
                #print self.db.tables, self.db.metadata.tables.keys(), self.db._tables.keys()
                self.db[tableName].insert(rows[0], ensure=True)
                rows[:1] = [] # remove first row
            if len(rows) > 0:
                startTime = time.time()
                #print self.db.tables, self.db.metadata.tables.keys(), self.db._tables.keys()
                print "Inserting", len(rows), "rows to", str(self.db[tableName]) + "...",
                #print self.db.tables, self.db.metadata.tables.keys(), self.db._tables.keys()
                self.db[tableName].insert_many(rows, chunk_size=chunkSize, ensure=False)
                rows[:] = [] # clear the cache
                print "done in %.2f" % (time.time() - startTime)