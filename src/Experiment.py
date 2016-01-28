import sys, os
from collections import OrderedDict
from Meta import Meta
from ExampleIO import SVMLightExampleIO
import time
import csv
from _collections import defaultdict
from nltk.corpus import wordnet

class Experiment(object):
    def readExamples(self, filePath):
        columns = ["index", "word", "lemma", "POS", "MWE", "parent", "strength", "supersense", "sentence"]
        MWETags = set(["O", "o", "B", "b", "I", "i"])
        with open(filePath) as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=columns,  delimiter="\t", quoting=csv.QUOTE_NONE)
            examples = [row for row in reader]
            for example in examples:
                example["index"] = int(example["index"])
                example["parent"] = int(example["parent"]) if example["parent"] != "" else None
                assert example["MWE"] in MWETags, example
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
        self.classIds = {} #{'True':1, 'False':-1}
        self.classNames = {}
        
        self.featureGroups = None
        self.includeSets = ("train",)
        self.meta = None
        self.baseClassVars = None
        self.baseClassVars = set(vars(self).keys())
    
    def getClassId(self, value):
        value = str(value)
        if value not in self.classIds:
            self.classIds[value] = len(self.classIds)
            self.classNames[self.classIds[value]] = value
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
        if exampleId not in exampleFeatures:
            exampleFeatures[exampleId] = {}
        groups = exampleFeatures[exampleId]
        if unique or groupName not in groups:
            assert groupName not in groups
            groups[groupName] = featureSet
        else:
            combined = {}
            combined.update(groups[groupName])
            combined.update(featureSet)
            groups[groupName] = combined            
    
    def analysePOS(self):
        d = {}
        for sentence in self.corpus["train"]:
            for example in sentence:
                if example["POS"] not in d:
                    d[example["POS"]] = set()
                d[example["POS"]].add(example["supersense"])
        for key in sorted(d.keys()):
            self.meta.insert("pos_group", {"pos":key, "senses":",".join(sorted(d[key]))})
        self.meta.flush()

    def processSentences(self, metaDataFileName=None, exampleWriter=None, setNames=None):
        self.beginExperiment(metaDataFileName)
        if setNames == None:
            setNames = self.includeSets
        self.readCorpus(setNames)
        #self.analysePOS()
        sentenceCount = 0
        exampleCount = 0
        classCounts = defaultdict(int)
        #numSentences = sum([len(:self.corpus.get(setName, [])) for setName in setNames])
        for setName in setNames:
            for sentence in self.corpus[setName]:
                for token in sentence:
                    print wordnet.synsets(token["lemma"],  )
                sentenceCount += 1
                sys.exit()

        for classId in self.classIds:
            self.meta.insert("class", {"label":classId, "id":self.classIds[classId], "instances":classCounts[classId]})
        self.meta.flush()
        print "Built", exampleCount, "examples with", len(self.featureIds), "unique features"
        #print "Counts:", dict(classCounts)
        
    def processSentencesOld(self, metaDataFileName=None, exampleWriter=None, setNames=None):
        self.beginExperiment(metaDataFileName)
        if setNames == None:
            setNames = self.includeSets
        self.readCorpus(setNames)
        #self.analysePOS()
        sentenceCount = 0
        exampleCount = 0
        classCounts = defaultdict(int)
        numSentences = sum([len(self.corpus.get(setName, [])) for setName in setNames])
        for setName in setNames:
            for sentence in self.corpus[setName]:
                exampleIds = []
                exampleFeatures = {}
                exampleLabels = {}
                for example in sentence:
                    #print example
                    exampleId = self._getExampleId(example)
                    exampleLabels[exampleId] = self.getClassId(self.getLabel(example))
                if sentenceCount % 100 == 0:
                    print "Processing sentence", str(sentenceCount + 1) + "/" + str(numSentences)
                #groupCounts = defaultdict(int)
                for featureGroup in self.featureGroups:
                    for example in sentence:
                        exampleId = self._getExampleId(example)
                        exampleIds.append(exampleId)
                        featureSet = featureGroup.processExample(example, sentence, self.featureIds, self.meta)
                        #groupCounts[featureGroup.name] += len(featureSet)
                        self._addToSentence(exampleId, featureGroup.name, featureSet, exampleFeatures)
                        self._addToSentence(exampleId, "ALL_FEATURES", featureSet, exampleFeatures, False)
                #print dict(groupCounts)
                for exampleId in exampleIds:
                    if exampleId not in exampleFeatures:
                        print "No features for example", exampleId
                    self.meta.insert("example", dict(example, set_name=setName, example_id=exampleId, num_features=len(exampleFeatures[exampleId])))
                    exampleWriter.writeExample(exampleLabels[exampleId], exampleFeatures[exampleId]["ALL_FEATURES"])
                    classCounts[exampleLabels[exampleId]] += 1
                    exampleCount += 1
                sentenceCount += 1

        for classId in self.classIds:
            self.meta.insert("class", {"label":classId, "id":self.classIds[classId], "instances":classCounts[classId]})
        self.meta.flush()
        print "Built", exampleCount, "examples with", len(self.featureIds), "unique features"
        #print "Counts:", dict(classCounts)
    
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