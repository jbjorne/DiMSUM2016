import sys, os
from collections import OrderedDict
from Meta import Meta
from ExampleIO import SVMLightExampleIO
import time
import csv
from _collections import defaultdict
from nltk.corpus import wordnet
import traceback

class Experiment(object):
    def readExamples(self, filePath):
        MWETags = set(["O", "o", "B", "b", "I", "i"])
        with open(filePath) as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=self.corpusColumns,  delimiter="\t", quoting=csv.QUOTE_NONE)
            examples = [row for row in reader]
            for example in examples:
                example["index"] = int(example["index"]) - 1
                assert example["index"] >= 0
                example["parent"] = int(example["parent"]) if example["parent"] != "" else None
                example["supersense"] = example["supersense"] if example["supersense"] != "" else None
                assert example["MWE"] in MWETags, example
            return examples
    
    def printSentence(self, sentence):
        for token in sentence:
            print "\t".join(str(token[x]) for x in self.corpusColumns) 
    
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
        self.corpusColumns = ["index", "word", "lemma", "POS", "MWE", "parent", "strength", "supersense", "sentence"]
        # Id sets
        self.featureIds = {}
        self.classIds = {'True':1, 'False':-1}
        self.classNames = {}
        self.maxExampleTokens = 6
        
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
        self.missedExampleCount = 0
        self.classCounts = defaultdict(int)
        self.numSentences = sum([len(self.corpus.get(setName, [])) for setName in setNames])
        for setName in setNames:
            self.processSentences(self.corpus[setName], setName)
        self.endExperiment()
        
    def endExperiment(self):
        for classId in self.classIds:
            self.meta.insert("class", {"label":classId, "id":self.classIds[classId], "instances":self.classCounts[classId]})
        self.meta.flush()
        print "Built", self.exampleCount, "examples with", len(self.featureIds), "unique features"
        print "Missed", self.missedExampleCount, "positive examples with window size", self.maxExampleTokens
        print "Counts:", dict(self.classCounts)
    
    def processSentences(self, sentences, setName):
        try:
            for sentence in sentences:
                if (self.sentenceCount + 1) % 100 == 0:
                    print "Processing sentence", str(self.sentenceCount + 1) + "/" + str(self.numSentences)
                self.processSentence(sentence, setName)
                self.sentenceCount += 1
        except Exception, err:
            self.printSentence(sentence)
            traceback.print_exc()
            sys.exit()
 
    def processSentence(self, sentence, setName):
        numTokens = len(sentence)
        mappedTokens = [False] * len(sentence)
        for i in range(numTokens):
            numPos = 0
            numTotal = 0
            goldTokens = self.getGoldExample(i, sentence)
            skipNested = mappedTokens[i]
            if not skipNested:
                for j in range(i + self.maxExampleTokens, i, -1):
                    tokens = sentence[i:j]
                    supersenses = self.getSuperSenses("_".join([x["lemma"] for x in tokens]))
                    goldSupersense = None
                    if tokens == goldTokens:
                        goldSupersense = goldTokens[0]["supersense"]
                    for supersense in supersenses:
                        if self.buildExample(tokens, sentence, supersense, supersenses, goldSupersense, setName):
                            numPos += 1
                        numTotal += 1
                        self.exampleCount += 1
                    if numTotal > 0:
                        for mappedIndex in range(i, j):
                            mappedTokens[mappedIndex] = True
                        skipNested = True
                        break
            if goldTokens != None and numPos == 0:
                self.insertExampleMeta(None, None, goldSupersense, tokens, {}, setName, numTotal > 0, skipNested)
                self.missedExampleCount += 1
            self.meta.insert("token", dict(sentence[i], token_id=self._getTokenId(sentence[i]), num_examples=len(supersenses), num_pos=numPos))
            #print (token["lemma"], token["supersense"], token["POS"]), self.getSuperSenses(token["lemma"])                        
    
    def getGoldExample(self, beginIndex, sentence):
        """
        For each token in a sentence there can be only one expression,
        which can have one or more words. A new expression begins with
        one of the MWE tags 'O', 'B' or 'b'.
        """
        if sentence[beginIndex]["supersense"] == None:
            return None
        tokens = [sentence[beginIndex]]
        mweType = tokens[0]["MWE"]
        assert mweType in ("O", "B", "b")
        if mweType == "O":
            return tokens
        for i in range(beginIndex + 1, len(sentence)):
            mwe = sentence[i]["MWE"]
            if mwe == "O":
                break
            elif mweType == "B" and mwe == "I":
                tokens.append(sentence[i])
            elif mweType == "b" and mwe == "i":
                tokens.append(sentence[i])
            else:
                assert mwe == "o"
        return tokens   
    
#     def isExact(self, tokens, sentence):
#         if tokens[0]["MWE"] in ("O", "o"): # This is a single-word expression
#             return len(tokens) == 1
#         elif tokens[0]["MWE"] == "B": # The first token begins a multi-word expression
#             if len(tokens) == 1: # A MWE must have more than one token
#                 return False
#             for token in tokens[1:]: # Check tokens after the beginning one
#                 if token["MWE"] != "I": # Tokens must extend the MWE
#                     return False
#             if tokens[-1] != sentence[-1]: # Check the token after the last one
#                 if sentence[tokens[-1]["index"] + 1]["MWE"] in ("I", "i", "o", "b"): # The token after the last one must close the MWE
#                     return False
#             return True # MWE is a B + n * I series
#         return False # MWE begins with a token other than B
#     
#     def getAnnotatedSense(self, tokens, sentence):
#         if self.isExact(tokens, sentence):
#             return tokens[0]["supersense"]
#         else:
#             return None
    
    def insertExampleMeta(self, label, supersense, goldSupersense, tokens, features, setName, textDetected, isNested):
        exampleId = self._getExampleId(tokens)
        self.meta.insert("example", {"label":label, 
                                     "supersense":supersense, 
                                     "gold_sense":goldSupersense, 
                                     "text":" ".join([x["word"] for x in tokens]), 
                                     "set_name":setName, 
                                     "example_id":exampleId, 
                                     "num_features":len(features),
                                     "num_tokens":len(tokens),
                                     "mwe_type":"".join([x["MWE"] for x in tokens]),
                                     "text_detected":textDetected,
                                     "nested":isNested})
    
    def buildExample(self, tokens, sentence, supersense, supersenses, goldSupersense, setName):
        #realSense = self.getAnnotatedSense(tokens, sentence)
        #label = True if supersense == realSense else False
        label = True if supersense == goldSupersense else False
        classId = self.getClassId(label)
        features = {}
        for featureGroup in self.featureGroups:
            features.update(featureGroup.processExample(tokens, supersense, sentence, supersenses, self.featureIds, self.meta))
        self.insertExampleMeta(label, supersense, goldSupersense, tokens, features, setName, True)
        self._getExampleIO().writeExample(classId, features)
        self.classCounts[label] += 1
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