import os
from Analysis import Analysis
from collections import OrderedDict

class ResultAnalysis(Analysis):
    def __init__(self, dataPath=None):
        super(ResultAnalysis, self).__init__(dataPath=dataPath)
        self.columns = ["index", "word", "lemma", "POS", "MWE", "parent", "strength", "supersense", "sentence"]
    
    def processSentence(self, sentence):
        for token in sentence:
            sentenceId = token["sentence"]
            index = token["index"]
            if sentenceId in self.exampleMap and index in self.exampleMap[sentenceId]:
                examples = self.exampleMap[sentenceId][index]
                maxExample = None
                maxPrediction = None
                for example in examples:
                    prediction = self.predictions[example["id"]]
                    if maxPrediction == None or float(prediction["predicted"]) > maxPrediction:
                        maxExample = example
                if float(maxPrediction["predicted"]) > 0.0:
                    token["supersense"] = maxExample["supersense"]
                    span = sorted([int(x) for x in str(maxExample["tokens"]).split(",")])
                    assert span[0] == index
                    if len(span) == 0:
                        token["MWE"] = "O"
                    else:
                        token["MWE"] = "O"
                        prevIndex = None
                        for spanIndex in sorted(span):
                            if prevIndex != None:
                                assert spanIndex - prevIndex == 1
                            assert spanIndex >= index
                            if spanIndex > index:
                                sentence[spanIndex] = "I"
                            else:
                                token["MWE"] = "B"
                            prevIndex = spanIndex
    
    def writeTokens(self, tokens, setName):
        print "Processing tokens for dataset '" + setName + "'"
        tokens = [x for x in tokens if x["set_name"] == setName]
        if len(tokens) == 0:
            print "Zero tokens for set", setName
            return
        print "Counting sentences"
        sentenceIds = set()
        for token in tokens:
            sentenceIds.add(token["sentence"])
        numSentences = len(sentenceIds)
        print "Processing sentences"
        sentence = []
        sentenceCount = 0
        outFile = open(os.path.join(self.inDir, "dimsum16." + setName + ".pred"), "wt")
        prevSentence = None
        for token in tokens:
            if prevSentence != None and prevSentence != token["sentence"]:
                if (sentenceCount + 1) % 100 == 0:
                    print "Processing sentence", str(sentenceCount + 1) + "/" + str(numSentences)
                self.processSentence(sentence)
                for sentenceToken in sentence:
                    outFile.write("\t".join([sentenceToken[column] for column in self.columns]) + "\n")
                outFile.write("\n")
                sentenceCount += 1
            prevSentence = token["sentence"]
            outToken = token.copy()
            # Clear the columns to be predicted
            outToken["supersense"] = None
            outToken["MWE"] = "O"
            sentence.append(outToken)
            
        outFile.close()
        
    def analyse(self, inDir, fileStem=None, hidden=False, clear=True):
        self.inDir = inDir
        self.meta = self._getMeta(inDir, fileStem)
        for filename in os.listdir(inDir):
            if filename.startswith("dimsum16.") and filename.endswith(".pred"):
                os.remove(os.path.join(inDir, filename))
        #if clear:
        #    meta.drop("project_analysis")
        print "Reading examples"
        self.examples = [x for x in self.meta.db["example"].all() if x["label"] is not None]
        print "Reading predictions"
        self.predictions = {x["example"]:x["predicted"] for x in self.meta.db["prediction"].all()}
        print "Checking predictions"
        for example in self.examples:
            assert example["id"] in self.predictions
            
        print "Mapping examples"
        self.exampleMap = OrderedDict()
        for example in self.examples:
            if example["sentence"] not in self.exampleMap:
                self.exampleMap[example["sentence"]] = OrderedDict()
            sentenceExamples = self.exampleMap[example["sentence"]]
            if example["root_token"] not in sentenceExamples:
                sentenceExamples[example["root_token"]] = []
            sentenceExamples[example["root_token"]].append(example)
        
        print "Processing datasets"
        self.tokens = [x for x in self.meta.db["token"].all()]
        self.writeTokens(self.tokens, "train")
        if hidden:
            self.writeTokens(self.tokens, "test")
