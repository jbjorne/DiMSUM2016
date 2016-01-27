#from collections import OrderedDict
#import json
import time
import os
import shutil
import dataset

# ###############################################################################
# # Output directory processing
# ###############################################################################
# 
# def getProjects(dirname, filter=None, numTopFeatures=0, returnPaths=False):
#     projects = {}
#     print "Reading results from", dirname
#     filenames = os.listdir(dirname)
#     index = 0
#     if filter == None:
#         filter = {}
#     for dirpath, dirnames, filenames in os.walk(dirname):
#         for filename in filenames:
#             index += 1
#             filePath = os.path.join(dirpath, filename)
#             found = True
#             if filter.get("filename") != None:
#                 for substrings in filter["filename"]:
#                     if isinstance(substrings, basestring):
#                         substrings = [substrings]
#                     match = False
#                     for substring in substrings: 
#                         if substring in filename:
#                             match = True
#                     if not match:
#                         found = False
#                         break
#             if found and os.path.isfile(filePath) and filePath.endswith(".json"):
#                 # Read project results
#                 meta = Meta(filePath)
#                 options = {}
#                 optionsList = meta["experiment"]["options"]
#                 if optionsList != None:
#                     optionsList = optionsList.split(",")
#                     for optionPair in optionsList:
#                         key, value = optionPair.split("=")
#                         options[key] = value
#                 # Filter by features
#                 if filter.get("features") == None or ("features" in options and options["features"] == filter.get("features")):
#                     # Add results for project...
#                     projectName = meta["template"]["project"]
#                     if projectName not in filter.get("projects"):
#                         continue
#                     if projectName not in projects:
#                         projects[projectName] = {}
#                     project = projects[projectName]
#                     # ... for experiment ...
#                     experimentName = meta["experiment"]["name"]
#                     if experimentName not in filter.get("experiments"):
#                         continue
#                     if experimentName not in project:
#                         project[experimentName] = {}
#                     experiment = project[experimentName]
#                     # ... for classifier ...
#                     classifierName = meta["results"]["best"]["classifier"]
#                     if classifierName not in filter.get("classifiers"):
#                         continue
#                     if returnPaths:
#                         experiment[classifierName] = filePath
#                     else:
#                         experiment[classifierName] = meta
#                     print "Read", filename, str(index+1) #+ "/" + str(len(filenames))
#                     #experiment["classifier"] = meta["results"]["best"]["classifier"]
#     return projects
# 
# def compareFeatures(a, b):
#     if isinstance(a, int) and isinstance(b, int):
#         return a - b
#     elif isinstance(a, dict) and isinstance(b, int):
#         return -1
#     elif isinstance(a, int) and isinstance(b, dict):
#         return 1
#     elif "sort" in a and "sort" in b:
#         return -cmp(a["sort"], b["sort"])
#     elif "sort" in a:
#         return -1
#     elif "sort" in b:
#         return 1
#     else: # a and b are dict, neither has a sort attribute
#         return a["id"] - b["id"]

class Meta():
    def __init__(self, filePath=None, copyFrom=None, clear=False):
        self.filePath = filePath
        self.verbose = True
        self.db = self._openDB(filePath, copyFrom=copyFrom, clear=clear)
        self.defaultCacheSize = 10000
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
                print "Inserting initial row for metadata table", self.db[tableName]
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
        
#     ###############################################################################
#     # JSON metadata read/write
#     ###############################################################################
#     
#     def read(self):
#         if self.filePath == None:
#             raise Exception("Metadata file path not defined")
#         print "Reading metadata from", self.filePath
#         f = open(self.filePath, "rt")
#         self.meta = json.load(f, object_pairs_hook=OrderedDict)
#         f.close()
#     
#     def write(self, filePath=None):
#         if filePath == None:
#             filePath = self.filePath
#         if filePath == None:
#             raise Exception("Metadata file path not defined")
#         self.meta["features"] = self.getFeaturesSorted()
#         self.sortKeys()
#         print "Saving metadata to", filePath
#         f = open(filePath, "wt")
#         json.dump(self.meta, f, indent=4)
#         f.close()    
#     
#     ###############################################################################
#     # Categories
#     ###############################################################################
#     
#     def __delitem__(self, key):
#         del self.meta[key]
#     
#     def __getitem__(self, key):
#         return self.meta[key]
#     
#     def __setitem__(self, key, value):
#         self.meta[key] = value
#     
#     def remove(self, key):
#         if key in self.meta:
#             del self.meta[key]
#     
#     def hasKey(self, key):
#         return key in self.meta
# 
#     ###############################################################################
#     # Individual examples and features
#     ###############################################################################
# 
#     def countExamples(self):
#         counts = {"1":0, "-1":0}
#         for example in self.meta["examples"]:
#             counts[example["label"]] += 1
#         return counts
#     
#     def getExampleFromSet(self, index, setName):
#         i = -1
#         for example in self.meta["examples"]:
#             if example["set"] == setName:
#                 i += 1
#             if i == index:
#                 return example
#     
#     def getExample(self, index):
#         return self.meta["examples"][index]
#     
#     def getExamples(self, indices):
#         return {i:self.meta["examples"][i] for i in indices}
#     
#     def getFeaturesByIndex(self):
#         featuresByIndex = {}
#         for name, index in self.meta["features"].iteritems():
#             if isinstance(index, int):
#                 featuresByIndex[index] = name
#             else:
#                 featuresByIndex[index["id"]] = name
#         return featuresByIndex
#     
#     def getFeature(self, index, featuresByIndex=None):
#         if featuresByIndex == None:
#             featuresByIndex = self._getFeaturesByIndex()
#         name = featuresByIndex[index]
#         if isinstance(self.meta["features"][name], int):
#             self.meta["features"][name] = {"id":self.meta["features"][name]}
#         return self.meta["features"][name]
#     
#     def getFeatures(self, indices, featuresByIndex=None):
#         if featuresByIndex == None:
#             featuresByIndex = self._getFeaturesByIndex()
#         rv = {}
#         features = self.meta["features"]
#         for index in indices:
#             name = featuresByIndex[index]
#             if isinstance(features[name], int):
#                 rv[index] = {"id":features[name]}
#             else:
#                 rv[index] = features[name]
#         return rv
#     
#     def getFeaturesSorted(self, featuresByIndex=None, addRank=True):
#         if featuresByIndex == None:
#             featuresByIndex = self.getFeaturesByIndex()
#         # Sort features
#         featureValues = self.meta["features"].values()
#         featureValues.sort(cmp=compareFeatures)
#         features = OrderedDict()
#         for index, feature in enumerate(featureValues):
#             if isinstance(feature, int):
#                 features[featuresByIndex[feature]] = feature
#             else:
#                 features[featuresByIndex[feature["id"]]] = feature
#                 if addRank:
#                     feature["rank"] = index + 1
#         return features
# 
#     ###############################################################################
#     # Utilities
#     ###############################################################################
#     
#     def sortKeys(self):
#         keys = self.meta.keys()
#         sortedKeys = []
#         for named in ["experiment", "template", "classes", "results", "analysis", "features", "examples"]:
#             if named in keys:
#                 sortedKeys.append(named)
#                 keys.remove(named)
#         sortedKeys += sorted(keys)
#         sortedMeta = OrderedDict()
#         for key in sortedKeys:
#             sortedMeta[key] = self.meta[key]
#         self.meta = sortedMeta
    
    
