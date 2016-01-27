import sys, os
from learn.HiddenSet import HiddenSet
from utils.common import getOptions
from _collections import defaultdict
from collections import OrderedDict
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
import math
import time
#import data.hidden as hidden
from Meta import Meta
from ExampleIO import SVMLightExampleIO

class Experiment(object):
    def _queryExamples(self):
        if self.projects != None:
            assert "/*{FILTER}*/" in self.query
            if "=" in self.projects:
                rules = getOptions(self.projects)
            else:
                rules = {"specimen.project_code":self.projects.split(",")}
            expressions = []
            for key in rules:
                mode = "LIKE" if "%" in "".join(self.projects) else "IN"
                values = rules[key]
                if isinstance(values, basestring):
                    values = [values]
                expressions.append(" ".join([key, mode, "('" + "','".join(values) + "')"]))
            self.query = self.query.replace("/*{FILTER}*/", " AND ".join(expressions) + " AND ")
        print "=========================== Example generation query ==========================="
        print self.query
        print "================================================================================"
        return [dict(x) for x in self.getConnection().execute(self.query)]
    
    def getLabel(self, example):
        raise NotImplementedError
    
    def getConnection(self):
        if self._connection == None:
            if not os.path.exists(self.databasePath):
                raise Exception("No database at " + str(self.databasePath))
            print "Using database at", self.databasePath
            self._connection = sqlite3.connect(self.databasePath) # @UndefinedVariable
            self._connection.row_factory = sqlite3.Row # @UndefinedVariable
            self._connection.create_function("log", 1, math.log)
        return self._connection
    
    def __init__(self):
        # Processing
        #self.debug = False
        # Database
        self.databasePath = None
        self._connection = None
        # Id sets
        self.featureIds = {}
        self.classIds = {'True':1, 'False':-1}
        # General
        self.projects = None
        self.balanceBy = None
        
        self.query = None
        self.exampleTable = "clinical"
        self.exampleFields = "icgc_donor_id,icgc_specimen_id,project_code,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup"
        self.exampleWhere = None
        self.featureGroups = None
        #self.filter = None
        self.hiddenCutoff = 0.3
        self.includeSets = ("train", "hidden")
        # Generated data
        #self.examples = None
        self.meta = None
        #self.unique = None
        self.baseClassVars = None
        self.baseClassVars = set(vars(self).keys())
    
#     def generateOrNot(self, example, verbose=True):
#         if not self.includeHiddenSet and example["hidden"] < self.hiddenCutoff:
#             if verbose:
#                 print "Skipping example from hidden donor", example["icgc_donor_id"]
#             return False
#         elif not self.includeTrainingSet and example["hidden"] >= self.hiddenCutoff:
#             if verbose:
#                 print "Skipping example " + str(example) + " from non-hidden donor", example["icgc_donor_id"]
#             return False
#         else:
#             return True
    
    def getClassId(self, value):
        if self.classIds != None:
            value = str(value)
            if value not in self.classIds:
                self.classIds[value] = len(self.classIds)
            return self.classIds[value]
        else:
            return value
    
#     def getFeatureId(self, featureName):
#         if featureName not in self.featureIds:
#             self.featureIds[featureName] = len(self.featureIds)
#             self.meta.insert("feature", {"name":featureName, "id":self.featureIds[featureName]})
#         return self.featureIds[featureName]
        
    def _buildFeatures(self, example):
        features = {}
        connection = self.getConnection()
        for featureGroup in self.featureGroups:
            if not featureGroup.processExample(connection, example, features, self.featureIds, self.meta):
                print "Example has no features for required group", featureGroup.name
                return {}
#         for groupIndex in range(len(self.featureGroups)):
#             featureGroup = self.featureGroups[groupIndex]
#             for row in self._queryFeatures(featureGroup, example): #featureGroup(con=self.getConnection(), example=example):
#                 for key, value in itertools.izip(*[iter(row)] * 2): # iterate over each consecutive key,value columns pair
#                     if not isinstance(key, basestring):
#                         raise Exception("Non-string feature key '" + str(key) + "' in feature group " + str(groupIndex))
#                     if not isinstance(value, Number):
#                         raise Exception("Non-number feature value '" + str(value) + "' in feature group " + str(groupIndex))
#                     features[self.getFeatureId(key)] = value
        #if len(features) == 0:
        #    print "WARNING: example has no features"
        return features
    
#     def _queryFeatures(self, featureGroup, example):
#         return self.getConnection().execute(featureGroup, (example['icgc_specimen_id'], ) )
    
#     def _filterExample(self, example):
#         if self.filter != None:
#             return len([x for x in self.getConnection().execute(self.filter, (example['icgc_specimen_id'], ) )]) == 0
#         return False

    def filter(self, example, features):
        if len(features) == 0:
            print "Filtered example with 0 features"
            return True
        return False
    
#     def getExampleMeta(self, example, classId, features):
#         return dict(example, label=str(classId), features=len(features))
    
#     def _balanceClasses(self, examples, groupBy):
#         examples = [x for x in examples if x["set"] == "train"]
#         counts = defaultdict(lambda: defaultdict(int))
#         for example in examples:
#             counts[example[groupBy]][example["label"]] += 1
#         print counts
#         limits = defaultdict(lambda: defaultdict(int))
#         for groupKey in counts:
#             minorityClassSize = counts[groupKey][min(counts[groupKey], key=counts[groupKey].get)]
#             for classId in counts[groupKey]:
#                 limits[groupKey][classId] = minorityClassSize
#         print limits
#         sys.exit()
#         counts = defaultdict(lambda: defaultdict(int))
#         for example in examples:
#             groupKey = example[groupBy]
#             classId = example["label"]
#             counts[groupKey][classId] += 1
#             example["balanced"] = counts[groupKey][classId] < limits[groupKey][classId]
    
    def _defineSets(self, examples):
        hiddenSet = HiddenSet()
        for example in examples:
            example["hidden"] = hiddenSet.getDonorThreshold(example["icgc_donor_id"])
            example["set"] = "hidden" if example["hidden"] < self.hiddenCutoff else "train"

    def _defineLabels(self, examples):
        for example in examples:
            assert "label" not in example
            example["label"] = self.getClassId(self.getLabel(example))
    
    def _getChildVars(self):
        members = vars(self)
        names = sorted(members.keys())
        childVars = OrderedDict()
        for name in names:
            if name not in self.baseClassVars:
                childVars[name] = members[name]
        return childVars
    
    def buildExamples(self, metaDataFileName=None, exampleWriter=None):
        print "Experiment:", self.__class__.__name__
        self.meta = Meta(metaDataFileName, clear=True)
        childVars = self._getChildVars()
        self.meta.insert("experiment", {"name":self.__class__.__name__, 
                                        "query":self.query,
                                        "vars":";".join([x+"="+str(childVars[x]) for x in childVars]),
                                        "time":time.strftime("%c"), 
                                        "dbFile":self.databasePath, 
                                        "dbModified":time.strftime("%c", time.localtime(os.path.getmtime(self.databasePath)))})
        self.meta.flush()
        self.meta.initCache("feature", 100000)
        # Initialize examples
        examples = self._queryExamples()
        self._defineLabels(examples)
        #numHidden = hidden.setHiddenValuesByFraction(self.examples, self.hiddenCutoff)
        self._defineSets(examples)
#         self.balanceBy = "project_code"
#         if self.balanceBy:
#             self._balanceClasses(examples, self.balanceBy)
        numExamples = len(examples)
        print "Examples " +  str(numExamples)
        # Build examples and features
        setCounts = defaultdict(int)
        count = 0
        numBuilt = 0
        for example in examples:
            count += 1
            if example["set"] not in self.includeSets:
                print "Skipping", example["icgc_donor_id"], "from set", example["set"]
                continue
#             if "balanced" in example and not example["balanced"]:
#                 print "Unbalanced", example["icgc_donor_id"], "from set", example["set"], "skipped"

            print "Processing example", example
            #classId = self.getClassId(self.getLabel(example))
            #if self._filterExample(example):
            #    print "NOTE: Filtered example"
            #    continue
#             if self.unique:
#                 assert example[self.unique] not in uniqueValues
#                 uniqueValues.add(example[self.unique])
            
            features = self._buildFeatures(example)
            print example["label"], str(len(features)), str(count) + "/" + str(numExamples)
            if self.filter(example, features):
                continue
            #self.exampleMeta.append(self.getExampleMeta(example, classId, features))
            #self.meta.insert("example", self.getExampleMeta(example, classId, features))
            self.meta.insert("example", dict(example, id=numBuilt, features=len(features)))
            exampleWriter.writeExample(example["label"], features)
            setCounts[example["set"]] += 1
            numBuilt += 1
        
        for classId in self.classIds:
            self.meta.insert("class", {"label":classId, "id":self.classIds[classId]})
        self.meta.flush()
        print "Built", numBuilt, "examples (" + str(dict(setCounts)) + ") with", len(self.featureIds), "unique features"
        #self.saveMetaData(metaDataFileName)
    
#     def _writeExamples(self, classIds, featureVectors, exampleWriter):
#         if exampleWriter != None:
#             for classId, features in zip(classIds, featureVectors):
#                 exampleWriter.writeExample(classId, features)
    
#     def getFingerprint(self):
#         return inspect.getsource(self.__class__)
    
#     def saveMetaData(self, metaDataFileName):
#         if metaDataFileName != None:
#             print "Writing metadata to", metaDataFileName
#             if not os.path.exists(os.path.dirname(metaDataFileName)):
#                 os.makedirs(os.path.dirname(metaDataFileName))
#             f = open(metaDataFileName, "wt")
#             output = OrderedDict((("experiment", self.meta), ("source", inspect.getsource(self.__class__)), ("classes", self.classIds), ("features", self.featureIds)))
#             if len(self.exampleMeta) > 0:
#                 output["examples"] = self.exampleMeta
#             json.dump(output, f, indent=4)#, separators=(',\n', ':'))
#             f.close()
#         else:
#             print "Experiment metadata not saved"
    
    def writeExamples(self, outDir, fileStem=None, exampleIO=None):
        if fileStem == None:
            fileStem = "examples"
        if exampleIO == None:
            exampleIO = SVMLightExampleIO(os.path.join(outDir, fileStem))
        
        exampleIO.newFiles()
        self.buildExamples(os.path.join(outDir, fileStem + ".meta.sqlite"), exampleIO)
        exampleIO.closeFiles()  