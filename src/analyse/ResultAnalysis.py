import os
from Analysis import Analysis
from collections import OrderedDict

class ResultAnalysis(Analysis):
    def __init__(self, dataPath=None):
        super(ResultAnalysis, self).__init__(dataPath=dataPath)
        self.columns = ["index", "word", "lemma", "POS", "MWE", "parent", "strength", "supersense", "sentence"]
    
    def writeTokens(self, tokens, setName):
        tokens = [x for x in tokens if x["set_name"] == setName]
        if len(tokens) == 0:
            print "Zero tokens for set", setName
            return
        outFile = open(os.path.join(self.inDir, self.fileStem + setName))
        prevSentence = None
        for token in tokens:
            if prevSentence != None and prevSentence != token["sentence"]:
                outFile.write("\n")
            outToken = token.copy()
            outFile.write("\t".join([outToken[column] for column in self.columns]) + "\n")
        outFile.close()
        
    def analyse(self, inDir, fileStem=None, hidden=False, clear=True):
        self.inDir = inDir
        if fileStem == None:
            fileStem = "examples"
        self.fileStem = fileStem
        meta = self._getMeta(inDir, fileStem)
        #if clear:
        #    meta.drop("project_analysis")
        self.predictions = None
        if "prediction" in meta.db:
            self.predictions = {x["example"]:x["predicted"] for x in meta.db["prediction"].all()}
        self.examples = [x for x in self.meta.db["example"].all() if x["label"] is not None]
        
        self.exampleMap = OrderedDict()
        for example in self.examples:
            if example["sentence"] not in self.exampleMap:
                self.exampleMap[example["sentence"]] = OrderedDict()
            sentenceExamples = self.exampleMap[example["sentence"]]
            if example["root_token"] not in sentenceExamples:
                sentenceExamples[example["root_token"]] = []
            sentenceExamples[example["root_token"]].append(example)
        
        self.tokens = [x for x in self.meta.db["token"].all()]
        
