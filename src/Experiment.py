import sys, os
from collections import OrderedDict
from Meta import Meta
from ExampleIO import SVMLightExampleIO
import time
from _collections import defaultdict
from nltk.corpus import wordnet
import traceback
from src.Corpus import Corpus, getGoldExample, getExampleId, getTokenId, hasGaps

class Experiment(object):    
    def __init__(self):
        self.dataPath = None
        self.corpus = None
        # Id sets
        self.featureIds = {}
        self.classIds = {'True':1, 'False':-1}
        self.classNames = {}
        self.maxExampleTokens = 6
        
        self.taggers = None
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

    ###########################################################################
    # Running the Experiment
    ###########################################################################
    
    def run(self, outDir, fileStem=None, exampleIO=None):
        self.outDir = outDir
        self.fileStem = fileStem if fileStem else "examples"
        self.exampleIO = exampleIO
        self.processCorpus()
        self._closeExampleIO()
    
    def beginExperiment(self, metaDataFileName=None):
        print "Experiment:", self.__class__.__name__
        self.meta = Meta(metaDataFileName, clear=True)
        childVars = self._getChildVars()
        self.meta.insert("experiment", {"name":self.__class__.__name__,
                                        "vars":";".join([x+"="+str(childVars[x]) for x in childVars]),
                                        "time":time.strftime("%c")})
        self.meta.flush()
        self.meta.initCache("feature", 100000)        

    def endExperiment(self):
        for classId in self.classIds:
            self.meta.insert("class", {"label":classId, "id":self.classIds[classId], "instances":self.classCounts[classId]})
        self.meta.flush()
        print "Built", self.exampleCount, "examples with", len(self.featureIds), "unique features"
        print "Missed", self.missedExampleCount, "positive examples with window size", self.maxExampleTokens
        print "Counts:", dict(self.classCounts)

    def _getChildVars(self):
        members = vars(self)
        names = sorted(members.keys())
        childVars = OrderedDict()
        for name in names:
            if name not in self.baseClassVars:
                childVars[name] = members[name]
        return childVars
    
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

    ###########################################################################
    # Sentence processing
    ###########################################################################
        
    def processCorpus(self, metaDataFileName=None, setNames=None):
        if metaDataFileName == None:
            metaDataFileName = os.path.join(self.outDir, self.fileStem + ".meta.sqlite")
        self.beginExperiment(metaDataFileName)
        if setNames == None:
            setNames = self.includeSets
        self.corpus = Corpus(self.dataPath)
        self.corpus.readCorpus(setNames) #self.readCorpus(setNames)
        #self.analysePOS()
        self.sentenceCount = 0
        self.exampleCount = 0
        self.missedExampleCount = 0
        self.classCounts = defaultdict(int)
        self.numSentences = sum([len(self.corpus.getSentences(setName)) for setName in setNames])
        for setName in setNames:
            self.processSentences(self.corpus.getSentences(setName), setName)
        self.endExperiment()
    
    def processSentences(self, sentences, setName):
        try:
            for sentence in sentences:
                if (self.sentenceCount + 1) % 100 == 0:
                    print "Processing sentence", str(self.sentenceCount + 1) + "/" + str(self.numSentences)
                self.processSentence(sentence, setName)
                self.sentenceCount += 1
        except Exception, err:
            self.corpus.printSentence(sentence)
            traceback.print_exc()
            sys.exit()
     
    def processSentence(self, sentence, setName):
        numTokens = len(sentence)
        matchedUntil = 0
        for i in range(numTokens): # There can be max one example per each token
            numExamples = 0
            numPos = 0
            goldTokens = getGoldExample(i, sentence)
            goldSupersense = goldTokens[0]["supersense"]
            if i >= matchedUntil:
                for j in range(i + self.maxExampleTokens, i, -1):
                    tokens = sentence[i:j]
                    exampleGoldSupersense = None
                    if tokens == goldTokens: # Make a positive example only for the exact match
                        exampleGoldSupersense = goldTokens[0]["supersense"]
                    matchLength = -1
                    for tagger in self.taggers:
                        supersenses = tagger.tag(tokens)
                        if supersenses:
                            for supersense in supersenses:
                                if self.buildExample(tokens, sentence, supersense, supersenses, exampleGoldSupersense, setName, tagger.name):
                                    numPos += 1
                                numExamples += 1
                            matchedUntil = j
                            matchLength = j - i
                            break # Skip subsequent taggers
                    if matchLength != -1: # Ignore nested matches
                        break
            if goldTokens != None and numPos == 0:
                if hasGaps(goldTokens):
                    skipReason = "gaps"
                elif len(goldTokens) > self.maxExampleTokens:
                    skipReason = "too long"
                elif i < matchedUntil:
                    skipReason = "nested"
                elif len(goldTokens) == matchLength:
                    skipReason = "type"
                else:
                    skipReason = "unknown"
                self.insertExampleMeta(None, None, goldSupersense, tokens, {}, setName, skipReason)
                self.missedExampleCount += 1
            self.meta.insert("token", dict(sentence[i], token_id=getTokenId(sentence[i]), num_examples=numExamples, num_pos=numPos))

    ###########################################################################
    # Example Generation
    ###########################################################################
    
    def insertExampleMeta(self, label, supersense, goldSupersense, tokens, features, setName, skipReason=None, taggerName=None, tableName="examples"):
        exampleId = getExampleId(tokens) #self._getExampleId(tokens)
        self.meta.insert(tableName, {"label":label, 
                                     "supersense":supersense, 
                                     "gold_sense":goldSupersense, 
                                     "text":" ".join([x["word"] for x in tokens]),
                                     "lemma":" ".join([x["lemma"] for x in tokens]), 
                                     "set_name":setName, 
                                     "example_id":exampleId, 
                                     "num_features":len(features),
                                     "num_tokens":len(tokens),
                                     "mwe_type":"".join([x["MWE"] for x in tokens]),
                                     "POS":":".join([x["POS"] for x in tokens]),
                                     "tagger":taggerName,
                                     "skipped":skipReason})
    
    def buildExample(self, tokens, sentence, supersense, supersenses, goldSupersense, setName, taggerName):
        #realSense = self.getAnnotatedSense(tokens, sentence)
        #label = True if supersense == realSense else False
        label = True if supersense == goldSupersense else False
        classId = self.getClassId(label)
        features = {}
        for featureGroup in self.featureGroups:
            features.update(featureGroup.processExample(tokens, supersense, sentence, supersenses, self.featureIds, self.meta))
        self.insertExampleMeta(label, supersense, goldSupersense, tokens, features, setName, None, taggerName)
        self._getExampleIO().writeExample(classId, features)
        self.classCounts[label] += 1
        self.exampleCount += 1
        return label