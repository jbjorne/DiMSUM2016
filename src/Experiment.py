import sys, os
from collections import OrderedDict
from Meta import Meta
from ExampleIO import SVMLightExampleIO
import time
from _collections import defaultdict
from nltk.corpus import wordnet
import traceback
from src.Corpus import Corpus, getGoldExample, getExampleId, getTokenId, hasGaps
#from src.taggers.WordNetTagger import WordNetTagger

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
    
    def getFeatureId(self, featureName):
        if featureName not in self.featureIds:
            self.featureIds[featureName] = len(self.featureIds)
            self.meta.insert("feature", {"name":featureName, "id":self.featureIds[featureName]})
        return self.featureIds[featureName]

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
        resources = []
        if self.taggers:
            for tagger in self.taggers:
                resources += tagger.resources
        if self.featureGroups:
            for featureGroup in self.featureGroups:
                resources += featureGroup.resources
        resources = sorted(set(resources))
        self.meta.insert("experiment", {"name":self.__class__.__name__,
                                        "vars":";".join([x+"="+str(childVars[x]) for x in childVars]),
                                        "resources":",".join(resources),
                                        "time":time.strftime("%c")})
        self.meta.flush()
        self.meta.initCache("feature", 100000)        

    def endExperiment(self):
        for label in self.classIds:
            self.meta.insert("class", {"label":label, "id":self.classIds[label], "instances":self.exampleCounts.get(label, 0)})
        self.meta.flush()
        print "Built", sum(self.exampleCounts.values()), "examples with", len(self.featureIds), "unique features"
        missedPositives = sum(self.missedExampleCounts.values())
        totalPositives = self.exampleCounts.get(True, 0) + missedPositives
        missedPercent = 0
        if totalPositives > 0:
            missedPercent = 100.0 * missedPositives / float(totalPositives)
        print "Missed", sum(self.missedExampleCounts.values()), "positive examples (%.2f percent) with window size" % missedPercent, self.maxExampleTokens
        print "Positives (built and missed):", totalPositives
        print "Examples:", dict(self.exampleCounts)
        print "Missed:", dict(self.missedExampleCounts)
        print "Taggers:", self.taggerCounts

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
        self.exampleCounts = defaultdict(int)
        self.missedExampleCounts = defaultdict(int)
        self.taggerCounts = {}
        for tagger in self.taggers:
            self.taggerCounts[tagger.name] = {"pos":0, "neg":0}
        self.numSentences = sum([len(self.corpus.getSentences(setName)) for setName in setNames])
        for setName in setNames:
            self.processSentences(self.corpus.getSentences(setName), setName)
        self.endExperiment()
    
    def processSentences(self, sentences, setName):
        #self.preprocessSentences(sentences)
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
    
#     def preprocessSentences(self, sentences):
#         print "Preprocessing sentences...",
#         tagger = WordNetTagger()
#         for sentence in sentences:
#             for token in sentence:
#                 token["lexnames"] = tagger.tag([token], sentence, {})
#         print "done"

#     def processSentence(self, sentence, setName):
#         numTokens = len(sentence)
#         for i in range(numTokens): # There can be max one example per each token
#             exampleCounts = {"pos":0, "neg":0}
#             goldTokens = getGoldExample(i, sentence)
#             matchedTokens = None
#             for j in range(i + self.maxExampleTokens, i, -1):
#                 tokens = sentence[i:j]
#                 spanCounts, supersenseDict = self.buildExamples(tokens, goldTokens, sentence, setName)
#                 if sum(spanCounts.values()) > 0: # At least one example was generated
#                     if tokens == goldTokens:
#                         matchedTokens = supersenseDict
#                     for key in spanCounts:
#                         exampleCounts[key] += spanCounts[key]
#             # If no positive example is generated record the reason
#             if goldTokens != None and exampleCounts["pos"] == 0:
#                 if hasGaps(goldTokens):
#                     skipReason = "gaps"
#                 elif len(goldTokens) > self.maxExampleTokens:
#                     skipReason = "too long"
#                 elif matchedTokens != None and goldTokens[0]["supersense"] not in matchedTokens:
#                     skipReason = "type"
#                     for key in sorted(matchedTokens.keys()):
#                         self.insertExampleMeta(None, key, goldTokens[0]["supersense"], goldTokens, {}, setName, skipReason, tableName="type_error", addToCounts=False)
#                 else:
#                     skipReason = "no match"
#                 self.insertExampleMeta(None, None, goldTokens[0]["supersense"], goldTokens, {}, setName, skipReason)
#             # Save the token
#             self.meta.insert("token", dict(sentence[i], set_name=setName, token_id=getTokenId(sentence[i]), num_neg=exampleCounts["neg"], num_pos=exampleCounts["pos"]))
     
    def processSentence(self, sentence, setName):
        numTokens = len(sentence)
        matchedUntil = 0
        for i in range(numTokens): # There can be max one example per each token
            exampleCounts = {"pos":0, "neg":0}
            goldTokens = getGoldExample(i, sentence)
            matchLength = -1
            indexIsConsumed = i < matchedUntil
            if not indexIsConsumed:
                for j in range(i + self.maxExampleTokens, i, -1):
                    tokens = sentence[i:j]
                    exampleCounts, superSenseDict = self.buildExamples(tokens, goldTokens, sentence, setName)
                    if sum(exampleCounts.values()) > 0: # At least one example was generated
                        matchLength = len(tokens)
                        matchedUntil = j
                        break # Ignore nested matches
            # If no positive example is generated record the reason
            if goldTokens != None and exampleCounts["pos"] == 0:
                if hasGaps(goldTokens):
                    skipReason = "gaps"
                elif len(goldTokens) > self.maxExampleTokens:
                    skipReason = "too long"
                elif indexIsConsumed or len(goldTokens) < matchLength:
                    skipReason = "nested"
                elif len(goldTokens) == matchLength:
                    skipReason = "type"
                elif len(goldTokens) > matchLength:
                    skipReason = "no match"
                else:
                    skipReason = "unknown"
                self.insertExampleMeta(None, None, goldTokens[0]["supersense"], goldTokens, {}, setName, skipReason)
            # Save the token
            self.meta.insert("token", dict(sentence[i], set_name=setName, token_id=getTokenId(sentence[i]), num_neg=exampleCounts["neg"], num_pos=exampleCounts["pos"]))

    def buildExamples(self, tokens, goldTokens, sentence, setName):
        # Get the gold supersense for the examples built for this span
        exampleGoldSupersense = None
        if tokens == goldTokens: # Make a positive example only for the exact match
            exampleGoldSupersense = goldTokens[0]["supersense"]
        # Build the examples
        counts = {"pos":0, "neg":0}
        supersenseDict = {}
        taggingState = {"supersenses":supersenseDict} #{"nested":nested} #, "supersenses":supersenses}
        for tagger in self.taggers:
            supersenses = tagger.tag(tokens, sentence, taggingState)
            for supersense in supersenses:
                if supersense not in supersenseDict:
                    supersenseDict[supersense] = []
                supersenseDict[supersense].append(tagger.name)
            #if len(supersenses) > 0: # Ignore subsequent taggers
            #    break
        if len(supersenseDict) > 0:
            supersenses = sorted(supersenseDict.keys())
            for supersense in supersenses:
                label = self.buildExample(tokens, sentence, supersense, supersenses, exampleGoldSupersense, setName, ",".join(supersenseDict[supersense]))
                category = "pos" if label else "neg"
                counts[category] += 1
                for taggerName in supersenseDict[supersense]:
                    self.taggerCounts[taggerName][category] += 1
            #break # Skip subsequent taggers
        return counts, supersenseDict

    ###########################################################################
    # Example Generation
    ###########################################################################
    
    def insertExampleMeta(self, label, supersense, goldSupersense, tokens, features, setName, skipReason=None, taggerName=None, tableName="example", addToCounts=True):
        exampleId = getExampleId(tokens) #self._getExampleId(tokens)
        self.meta.insert(tableName, {"label":label, 
                                     "supersense":supersense, 
                                     "gold_sense":goldSupersense, 
                                     "text":" ".join([x["word"] for x in tokens]),
                                     "lemma":" ".join([x["lemma"] for x in tokens]), 
                                     "set_name":setName, 
                                     #"example_id":exampleId,
                                     "root_token":str(tokens[0]["index"]),
                                     "tokens":",".join([str(x["index"]) for x in tokens]), 
                                     "sentence":tokens[0]["sentence"], 
                                     "num_features":len(features),
                                     "num_tokens":len(tokens),
                                     "mwe_type":"".join([x["MWE"] for x in tokens]),
                                     "POS":":".join([x["POS"] for x in tokens]),
                                     "tagger":taggerName,
                                     #"nested":nested,
                                     "skipped":skipReason})
        if addToCounts:
            if label == None:
                self.missedExampleCounts[skipReason] += 1
            else:
                self.exampleCounts[label] += 1
    
    def buildExample(self, tokens, sentence, supersense, supersenses, goldSupersense, setName, taggerName):
        #realSense = self.getAnnotatedSense(tokens, sentence)
        #label = True if supersense == realSense else False
        label = True if supersense == goldSupersense else False
        classId = self.getClassId(label)
        features = {}
        #features[self.getFeatureId("SPAN_NESTED:" + str(nested))] = 1
        for featureGroup in self.featureGroups:
            features.update(featureGroup.processExample(tokens, supersense, sentence, supersenses, self.featureIds, self.meta))
        self.insertExampleMeta(label, supersense, goldSupersense, tokens, features, setName, None, taggerName)
        self._getExampleIO().writeExample(classId, features)
        return label