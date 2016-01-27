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
    def readExamples(self, filePath):
        columns = ["index", "word", "lemma", "POS", "MWE", "parent", "strength", "supersense", "sentence"]
        with open(filePath) as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=columns,  delimiter="\t")
            examples = [row for row in reader]
            return examples
    
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

    
    def getClassId(self, value):
        if self.classIds != None:
            value = str(value)
            if value not in self.classIds:
                self.classIds[value] = len(self.classIds)
            return self.classIds[value]
        else:
            return value
        
    def _buildFeatures(self, example):
        features = {}
        connection = self.getConnection()
        for featureGroup in self.featureGroups:
            featureGroup.processExample(connection, example, features, self.featureIds, self.meta)
        return features

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

            print "Processing example", example
            
            features = self._buildFeatures(example)
            print example["label"], str(len(features)), str(count) + "/" + str(numExamples)
            if self.filter(example, features):
                continue
            self.meta.insert("example", dict(example, id=numBuilt, features=len(features)))
            exampleWriter.writeExample(example["label"], features)
            setCounts[example["set"]] += 1
            numBuilt += 1
        
        for classId in self.classIds:
            self.meta.insert("class", {"label":classId, "id":self.classIds[classId]})
        self.meta.flush()
        print "Built", numBuilt, "examples (" + str(dict(setCounts)) + ") with", len(self.featureIds), "unique features"
    
    def writeExamples(self, outDir, fileStem=None, exampleIO=None):
        if fileStem == None:
            fileStem = "examples"
        if exampleIO == None:
            exampleIO = SVMLightExampleIO(os.path.join(outDir, fileStem))
        
        exampleIO.newFiles()
        self.buildExamples(os.path.join(outDir, fileStem + ".meta.sqlite"), exampleIO)
        exampleIO.closeFiles()  