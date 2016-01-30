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
            else:
                token["MWE"] = "O"
    
    def writeTokens(self, tokens, setName):
        tokens = [x for x in tokens if x["set_name"] == setName]
        if len(tokens) == 0:
            print "Zero tokens for set", setName
            return
        outFile = open(os.path.join(self.inDir, "dimsum16." + setName + ".pred"))
        prevSentence = None
        sentence = []
        for token in tokens:
            if prevSentence != None and prevSentence != token["sentence"]:
                self.processSentence(sentence)
                for sentenceToken in sentence:
                    outFile.write("\t".join([sentenceToken[column] for column in self.columns]) + "\n")
                outFile.write("\n")
            prevSentence = token["sentence"]
            outToken = token.copy()
            # Clear the columns to be predicted
            outToken["supersense"] = None
            outToken["MWE"] = None
            sentence.append(outToken)
            
        outFile.close()
        
    def analyse(self, inDir, fileStem=None, hidden=False, clear=True):
        self.inDir = inDir
        self.fileStem = fileStem
        meta = self._getMeta(inDir, fileStem)
        #if clear:
        #    meta.drop("project_analysis")
        self.examples = [x for x in self.meta.db["example"].all() if x["label"] is not None]
        self.predictions = {x["example"]:x["predicted"] for x in meta.db["prediction"].all()}
        for example in self.examples:
            assert example["id"] in self.predictions
            
        
        self.exampleMap = OrderedDict()
        for example in self.examples:
            if example["sentence"] not in self.exampleMap:
                self.exampleMap[example["sentence"]] = OrderedDict()
            sentenceExamples = self.exampleMap[example["sentence"]]
            if example["root_token"] not in sentenceExamples:
                sentenceExamples[example["root_token"]] = []
            sentenceExamples[example["root_token"]].append(example)
        
        self.tokens = [x for x in self.meta.db["token"].all()]
        
