import os
from Analysis import Analysis
from collections import OrderedDict
from _collections import defaultdict

class ResultAnalysis(Analysis):
    def __init__(self, dataPath=None):
        super(ResultAnalysis, self).__init__(dataPath=dataPath)
        self.columns = ["index", "word", "lemma", "POS", "MWE", "parent", "strength", "supersense", "sentence"]
    
    def processSentence(self, sentence, counts):
        for token in sentence:
            sentenceId = token["sentence"]
            index = token["index"]
            if sentenceId not in self.exampleMap:
                continue
            counts["sentences-with-examples"] += 1
            if index not in self.exampleMap[sentenceId]:
                continue
            counts["tokens-with-examples"] += 1
            examples = self.exampleMap[sentenceId][index]
            maxExample = None
            maxPrediction = None
            for example in examples:
                if example["id"] in self.predictions:
                    prediction = self.predictions[example["id"]]
                    if maxPrediction == None or prediction > maxPrediction:
                        maxExample = example
                        maxPrediction = prediction
            if maxExample != None and maxPrediction > 0.0:
                token["supersense"] = maxExample["supersense"]
                span = sorted([int(x) for x in str(maxExample["tokens"]).split(",")])
                assert span[0] == index
                if len(span) == 1:
                    token["MWE"] = "O"
                    counts["pred-O"] += 1
                else:
                    prevIndex = None
                    for spanIndex in sorted(span):
                        if prevIndex != None:
                            assert spanIndex - prevIndex == 1
                        assert spanIndex >= index
                        if spanIndex > index:
                            sentence[spanIndex]["MWE"] = "I"
                            sentence[spanIndex]["parent"] = spanIndex - 1 + 1
                            counts["pred-I"] += 1
                        else:
                            token["MWE"] = "B"
                            counts["pred-B"] += 1
                        prevIndex = spanIndex
    
    def writeTokens(self, tokens, setName):
        print "Processing tokens for dataset '" + setName + "'"
        tokens = [x for x in tokens if x["set_name"] == setName]
        if len(tokens) == 0:
            print "Zero tokens for set", setName
            return
        counts = defaultdict(int)
        print "Counting sentences"
        sentenceIds = set()
        for token in tokens:
            sentenceIds.add(token["sentence"])
        counts["sentences"] = len(sentenceIds)
        print "Processing sentences"
        sentence = []
        sentenceCount = 0
        outFile = open(os.path.join(self.inDir, "dimsum16." + setName + ".pred"), "wt")
        prevSentence = None
        for token in tokens:
            if prevSentence != None and prevSentence != token["sentence"]:
                if (sentenceCount + 1) % 100 == 0:
                    print "Processing sentence", str(sentenceCount + 1) + "/" + str(counts["sentences"])
                self.processSentence(sentence, counts)
                for sentenceToken in sentence:
                    sentenceToken = sentenceToken.copy()
                    sentenceToken["index"] = sentenceToken["index"] + 1
                    outFile.write("\t".join([(str(sentenceToken[column]) if sentenceToken[column] != None else "") for column in self.columns]) + "\n")
                outFile.write("\n")
                sentenceCount += 1
                sentence = []
            prevSentence = token["sentence"]
            outToken = token.copy()
            # Clear the columns to be predicted
            outToken["supersense"] = None
            outToken["parent"] = 0
            outToken["MWE"] = "O"
            sentence.append(outToken)
            
        outFile.close()
        print "Finished processing dataset '" + setName + "'", counts
        
    def analyse(self, inDir, fileStem=None, hidden=False, clear=True):
        self.inDir = inDir
        self.meta = self._getMeta(inDir, fileStem)
        for filename in os.listdir(inDir):
            if filename.startswith("dimsum16.") and filename.endswith(".pred"):
                os.remove(os.path.join(inDir, filename))
        #if clear:
        #    meta.drop("project_analysis")
        print "Reading examples"
        self.examples = [x for x in self.meta.db.query("SELECT id,supersense,sentence,root_token,tokens FROM example WHERE skipped IS NULL;")] # [x for x in self.meta.db["example"].all() if x["label"] is not None]
        for example in self.examples:
            example["root_token"] = int(example["root_token"])
        print "Reading predictions"
        self.predictions = {x["example"]:float(x["predicted"]) for x in self.meta.db.query("SELECT * FROM prediction WHERE predicted > 0;")} #{x["example"]:x["predicted"] for x in self.meta.db["prediction"].all()}
        #print "Checking predictions"
        #for example in self.examples:
        #    assert example["id"] in self.predictions
            
        print "Mapping examples"
        self.exampleMap = OrderedDict()
        for example in self.examples:
            if example["sentence"] not in self.exampleMap:
                self.exampleMap[example["sentence"]] = OrderedDict()
            sentenceExamples = self.exampleMap[example["sentence"]]
            if example["root_token"] not in sentenceExamples:
                sentenceExamples[example["root_token"]] = []
            sentenceExamples[example["root_token"]].append(example)
        
        print "Reading tokens"
        self.tokens = [x for x in self.meta.db["token"].all()]
        for token in self.tokens:
            token["index"] = int(token["index"])
        print "Processing datasets"
        self.writeTokens(self.tokens, "train")
        if hidden:
            self.writeTokens(self.tokens, "test")
