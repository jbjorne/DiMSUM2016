import sys, os
from collections import OrderedDict
from Meta import Meta
from ExampleIO import SVMLightExampleIO
import time
import csv

class Experiment(object):
    def readExamples(self, filePath):
        columns = ["index", "word", "lemma", "POS", "MWE", "parent", "strength", "supersense", "sentence"]
        with open(filePath) as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=columns,  delimiter="\t")
            examples = [row for row in reader]
            for example in examples:
                example["index"] = int(example["index"])
                example["parent"] = int(example["parent"]) if example["parent"] != "" else None
            return examples
    
    def readSentences(self, filePath):
        examples = self.readExamples(filePath)
        sentenceDict = OrderedDict()
        for example in examples:
            if example["sentence"] not in sentenceDict:
                sentenceDict[example["sentence"]] = []
            sentenceDict[example["sentence"]].append(example)
        return [sentenceDict[x] for x in sentenceDict]
    
    def readCorpus(self, setNames):
        self.corpus = {}
        for setName in setNames:
            filePath = os.path.join(self.dataPath, self.corpusFiles[setName])
            print "Reading set", setName, "from", filePath
            self.corpus[setName] = self.readSentences(filePath) 
    
    def getLabel(self, example):
        raise NotImplementedError
    
    def __init__(self):
        self.dataPath = None
        self.corpusFiles = {"train":"dimsum-data-1.5/dimsum16.train", "test":"dimsum-data-1.5/dimsum16.test.blind"}
        # Id sets
        self.featureIds = {}
        self.classIds = {'True':1, 'False':-1}
        
        self.featureGroups = None
        self.includeSets = ("train",)
        self.meta = None
        self.baseClassVars = None
        self.baseClassVars = set(vars(self).keys())
    
    def getClassId(self, value):
        value = str(value)
        if value not in self.classIds:
            self.classIds[value] = len(self.classIds)
        return self.classIds[value]
    
    def _getChildVars(self):
        members = vars(self)
        names = sorted(members.keys())
        childVars = OrderedDict()
        for name in names:
            if name not in self.baseClassVars:
                childVars[name] = members[name]
        return childVars
    
    def _getExampleId(self, example):
        return example["sentence"] + ":" + str(example["index"])
    
    def _addToSentence(self, exampleId, groupName, featureSet, exampleFeatures, unique=True):
        if groupName not in exampleFeatures:
            exampleFeatures[groupName] = {}
        if unique or exampleId not in exampleFeatures[groupName]:
            assert exampleId not in exampleFeatures[groupName]
            exampleFeatures[groupName][exampleId] = featureSet
        elif exampleId in exampleFeatures[groupName]:
            combined = {}
            combined.update(exampleFeatures[groupName][exampleId])
            combined.update(featureSet)
            exampleFeatures[groupName] = combined            
    
    def processSentences(self, metaDataFileName=None, exampleWriter=None, setNames=None):
        self.beginExperiment(metaDataFileName)
        if setNames == None:
            setNames = self.includeSets
        self.readCorpus(setNames)
        sentenceCount = 0
        exampleCount = 0
        numSentences = sum([len(self.corpus.get(setName, [])) for setName in setNames])
        for setName in setNames:
            for sentence in self.corpus[setName]:
                exampleIds = []
                exampleFeatures = {}
                exampleLabels = {}
                for example in sentence:
                    print example
                    exampleId = self._getExampleId(example)
                    exampleLabels[exampleId] = self.getClassId(self.getLabel(example))
                print "Processing sentence", str(sentenceCount + 1) + "/" + str(numSentences)
                for featureGroup in self.featureGroups:
                    for example in sentence:
                        exampleId = self._getExampleId(example)
                        exampleIds.append(exampleId)
                        featureSet = featureGroup.processExample(example, sentence, self.featureIds, self.meta)
                        self._addToSentence(exampleId, featureGroup.name, featureSet, exampleFeatures)
                        self._addToSentence(exampleId, "ALL_FEATURES", featureSet, exampleFeatures, False)
                for exampleId in exampleIds:
                    self.meta.insert("example", dict(example, example_id=exampleId, num_features=len(exampleFeatures.get(exampleId, []))))
                    exampleWriter.writeExample(exampleLabels[exampleId], exampleFeatures.get(exampleId, {}))
                    #setCounts[example["set"]] += 1
                    exampleCount += 1
                sentenceCount += 1

        for classId in self.classIds:
            self.meta.insert("class", {"label":classId, "id":self.classIds[classId]})
        self.meta.flush()
        print "Built", exampleCount, "examples with", len(self.featureIds), "unique features"
    
    def beginExperiment(self, metaDataFileName=None):
        print "Experiment:", self.__class__.__name__
        self.meta = Meta(metaDataFileName, clear=True)
        childVars = self._getChildVars()
        self.meta.insert("experiment", {"name":self.__class__.__name__,
                                        "vars":";".join([x+"="+str(childVars[x]) for x in childVars]),
                                        "time":time.strftime("%c")})
        self.meta.flush()
        self.meta.initCache("feature", 100000)        
    
    def writeExamples(self, outDir, fileStem=None, exampleIO=None):
        if fileStem == None:
            fileStem = "examples"
        if exampleIO == None:
            exampleIO = SVMLightExampleIO(os.path.join(outDir, fileStem))
        
        exampleIO.newFiles()
        self.processSentences(os.path.join(outDir, fileStem + ".meta.sqlite"), exampleIO)
        exampleIO.closeFiles()  