import os
from Analysis import Analysis
from collections import OrderedDict
from _collections import defaultdict
from src.utils.evaluation import evaluateScript
import codecs
import zipfile
from src.Resources import Resources

class ResultAnalysis(Analysis):
    def __init__(self, dataPath=None):
        super(ResultAnalysis, self).__init__(dataPath=dataPath)
        self.columns = ["index", "word", "lemma", "POS", "MWE", "parent", "strength", "supersense", "sentence"]
    
    def processSentence(self, sentence, counts):
        for token in sentence:
            if token["MWE"] == "I": # Skip already matched
                continue
            
            sentenceId = token["sentence"]
            index = token["index"]
            if sentenceId not in self.exampleMap:
                continue
            counts["sentences-with-examples"] += 1
            if index not in self.exampleMap[sentenceId]:
                continue
            counts["tokens-with-examples"] += 1
            # Get example with the highest predicted value
            examples = self.exampleMap[sentenceId][index]
            maxExample = None
            maxPrediction = None
            for example in examples:
                if example["id"] in self.predictions:
                    prediction = self.predictions[example["id"]]
                    if maxPrediction == None or prediction > maxPrediction:
                        maxExample = example
                        maxPrediction = prediction
            # Generate the expression for the example
            if maxExample != None and maxPrediction > 0.0:
                assert token["MWE"] == "O", (token, maxExample, maxPrediction)
                assert token["parent"] == 0, (token, maxExample, maxPrediction)
                assert token["supersense"] == None, (token, maxExample, maxPrediction)
                token["supersense"] = maxExample["supersense"]
                span = sorted([int(x) for x in str(maxExample["tokens"]).split(",")])
                assert span[0] == index, (index, span, token, maxExample, maxPrediction)
                assert min(span) == index, (index, span, token, maxExample, maxPrediction)
                if len(span) == 1:
                    counts["pred-O"] += 1
                else:
                    prevIndex = None
                    for spanIndex in span:
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
    
    def writeSentence(self, sentence, predFile, counts):
        self.processSentence(sentence, counts)
        for sentenceToken in sentence:
            sentenceToken = sentenceToken.copy()
            sentenceToken["index"] = sentenceToken["index"] + 1
            for column in self.columns:
                if sentenceToken[column] == None:
                    sentenceToken[column] = ""
                elif not isinstance(sentenceToken[column], basestring):
                    sentenceToken[column] = str(sentenceToken[column])
            predFile.write("\t".join([sentenceToken[column] for column in self.columns]) + "\n")
        predFile.write("\n")
    
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
        predFilePath = os.path.join(self.inDir, "dimsum16." + setName + ".pred")
        predFile = codecs.open(predFilePath, "wt", "utf-8")
        #debugFile = open(os.path.join(self.inDir, "debug." + setName + ".pred"), "wt")
        prevSentence = None
        for token in tokens:
            if prevSentence != None and prevSentence != token["sentence"]:
                if (sentenceCount + 1) % 1000 == 0:
                    print "Processing sentence", str(sentenceCount + 1) + "/" + str(counts["sentences"])
                self.writeSentence(sentence, predFile, counts)
                sentenceCount += 1
                sentence = []
            prevSentence = token["sentence"]
            outToken = token.copy()
            # Clear the columns to be predicted
            outToken["supersense"] = None
            outToken["parent"] = 0
            outToken["MWE"] = "O"
            assert outToken not in sentence
            sentence.append(outToken)
        if len(sentence) > 0: # Write final sentence
            self.writeSentence(sentence, predFile, counts)
            
        predFile.close()
        print "Evaluating", predFilePath
        goldFile = "dimsum16.train" if setName == "train" else "dimsum16.test.blind"
        goldFile = "dimsum-data-1.5/" + goldFile
        evaluateScript(os.path.join(self.dataPath, "dimsum-data-1.5/scripts/dimsumeval.py"),
                       os.path.join(self.dataPath, goldFile),
                       predFilePath)
        print "Finished processing dataset '" + setName + "'", counts
        if setName == "test":
            print "Making the zip file"
            self.writeZip(predFilePath)
            #self.writeZip(os.path.join(self.inDir, "result.zip"), predFilePath)
    
    def writeZip(self, predFilePath):
        # Write the report
        experiment = [x for x in self.db.db["experiment"].all()]
        assert len(experiment) == 1
        experiment = experiment[0]
        report = Resources().buildReport(experiment["resources"].split(","))
        reportPath = os.path.join(self.inDir, "submission.csv")
        f = open(reportPath, "wt")
        f.write(report)
        f.close()
        # Save the zipfile
        zipPath = os.path.join(self.inDir, experiment["name"] + ".zip")
        zf = zipfile.ZipFile(zipPath, "w")
        for filePath in (predFilePath,reportPath):
            zf.write(filePath, os.path.basename(filePath))
        zf.close()
        
    def analyse(self, inDir, fileStem=None, hidden=False, clear=True):
        self.inDir = inDir
        self.db = self._getDatabase(inDir, fileStem)
        for filename in os.listdir(inDir):
            if filename.endswith(".pred") or filename.endswith(".zip") or filename.endswith(".csv"):
                os.remove(os.path.join(inDir, filename))
        #if clear:
        #    meta.drop("project_analysis")
        print "Reading examples"
        self.examples = [x for x in self.db.db.query("SELECT id,supersense,sentence,root_token,tokens FROM example WHERE skipped IS NULL;")] # [x for x in self.meta.db["example"].all() if x["label"] is not None]
        for example in self.examples:
            example["root_token"] = int(example["root_token"])
        print "Reading predictions"
        self.predictions = {x["example"]:float(x["predicted"]) for x in self.db.db.query("SELECT * FROM prediction WHERE predicted > 0;")} #{x["example"]:x["predicted"] for x in self.meta.db["prediction"].all()}
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
        self.tokens = [x for x in self.db.db["token"].all()]
        for token in self.tokens:
            token["index"] = int(token["index"])
        print "Processing datasets"
        self.writeTokens(self.tokens, "train")
        if hidden:
            self.writeTokens(self.tokens, "test")
