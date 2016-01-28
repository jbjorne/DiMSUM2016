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
                example["supersense"] = example["supersense"] if example["supersense"] != "" else None
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
    
#     def getLabel(self, example):
#         raise NotImplementedError
    
    def __init__(self):
        self.dataPath = None
        self.corpusFiles = {"train":"dimsum-data-1.5/dimsum16.train", "test":"dimsum-data-1.5/dimsum16.test.blind"}
        # Id sets
        self.featureIds = {}
        self.classIds = {'True':1, 'False':-1}
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
    
    def _getTokenId(self, token):
        return token["sentence"] + ":" + str(token["index"])
    
    def _getExampleId(self, tokens):
        sentenceId = tokens[0]["sentence"]
        for token in tokens:
            assert token["sentence"] == sentenceId
        return sentenceId + ":" + ",".join([str(x) for x in sorted([token["index"] for token in tokens])])
    
#     def _addToSentence(self, exampleId, groupName, featureSet, exampleFeatures, unique=True):
#         if exampleId not in exampleFeatures:
#             exampleFeatures[exampleId] = {}
#         groups = exampleFeatures[exampleId]
#         if unique or groupName not in groups:
#             assert groupName not in groups
#             groups[groupName] = featureSet
#         else:
#             combined = {}
#             combined.update(groups[groupName])
#             combined.update(featureSet)
#             groups[groupName] = combined            
    
#     def analysePOS(self):
#         d = {}
#         for sentence in self.corpus["train"]:
#             for example in sentence:
#                 if example["POS"] not in d:
#                     d[example["POS"]] = set()
#                 d[example["POS"]].add(example["supersense"])
#         for key in sorted(d.keys()):
#             self.meta.insert("pos_group", {"pos":key, "senses":",".join(sorted(d[key]))})
#         self.meta.flush()
    
    def getSuperSenses(self, lemma):
        lexnames = sorted(set([x.lexname() for x in wordnet.synsets(lemma)]))
        return [x.replace("noun.", "n.").replace("verb.", "v.") for x in lexnames if x.startswith("noun.") or x.startswith("verb.")]
    
    def run(self, outDir, fileStem=None, exampleIO=None):
        self.outDir = outDir
        self.fileStem = fileStem if fileStem else "examples"
        self.exampleIO = exampleIO
        self.processCorpus()
        self._closeExampleIO()
    
    def processCorpus(self, metaDataFileName=None, setNames=None):
        if metaDataFileName == None:
            metaDataFileName = os.path.join(self.outDir, self.fileStem + ".meta.sqlite")
        self.beginExperiment(metaDataFileName)
        if setNames == None:
            setNames = self.includeSets
        self.readCorpus(setNames)
        #self.analysePOS()
        self.sentenceCount = 0
        self.exampleCount = 0
        self.classCounts = defaultdict(int)
        self.numSentences = sum([len(self.corpus.get(setName, [])) for setName in setNames])
        for setName in setNames:
            self.processSentences(self.corpus[setName])
        for classId in self.classIds:
            self.meta.insert("class", {"label":classId, "id":self.classIds[classId], "instances":self.classCounts[classId]})
        self.meta.flush()
        print "Built", self.exampleCount, "examples with", len(self.featureIds), "unique features"
        #print "Counts:", dict(classCounts)
    
    def processSentences(self, sentences, setName):
        for sentence in sentences:
            if self.sentenceCount % 100 == 0:
                print "Processing sentence", str(self.sentenceCount + 1) + "/" + str(self.numSentences)
            self.processSentence(sentence, setName)
            self.sentenceCount += 1
            
    def processSentence(self, sentence, setName):
        for token in sentence:
            supersenses = self.getSuperSenses(token["lemma"])
            numPos = 0
            for supersense in supersenses:
                if self.buildExample([token], supersense, sentence, supersenses, setName):
                    numPos += 1
                self.exampleCount += 1
            self.meta.insert("token", dict(token, token_id=self._getTokenId(token), num_examples=len(supersenses), num_pos=numPos))
            #print (token["lemma"], token["supersense"], token["POS"]), self.getSuperSenses(token["lemma"])                        
    
    def buildExample(self, tokens, supersense, sentence, supersenses, setName):
        exampleId = self._getExampleId(tokens)
        realSense = tokens[0]["supersense"]
        label = True if supersense == realSense else False
        classId = self.getClassId(label)
        features = {}
        for featureGroup in self.featureGroups:
            features.update(featureGroup.processExample(tokens, supersense, sentence, supersenses, self.featureIds, self.meta))
        self.meta.insert("example", dict(label=label, supersense=supersense, real_sense=realSense, text=" ".join([x["word"] for x in tokens]), set_name=setName, example_id=exampleId, num_features=len(features)))
        self._getExampleIO().writeExample(classId, features)
        return label
    
    def beginExperiment(self, metaDataFileName=None):
        print "Experiment:", self.__class__.__name__
        self.meta = Meta(metaDataFileName, clear=True)
        childVars = self._getChildVars()
        self.meta.insert("experiment", {"name":self.__class__.__name__,
                                        "vars":";".join([x+"="+str(childVars[x]) for x in childVars]),
                                        "time":time.strftime("%c")})
        self.meta.flush()
        self.meta.initCache("feature", 100000)        
    
    def _getExampleIO(self):
        if self.exampleIO:
            return self.exampleIO
        if self.exampleIO == None:
            self.exampleIO = SVMLightExampleIO(os.path.join(self.outDir, self.fileStem))
        self.exampleIO.newFiles()
        return self.exampleIO
    
    def _closeExampleIO(self):
        if self.exampleIO:
            self.exampleIO.closeFiles()