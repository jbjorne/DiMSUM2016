import os
import csv
from collections import OrderedDict

def getTokenId(token):
    return token["sentence"] + ":" + str(token["index"])

def getExampleId(tokens):
    sentenceId = tokens[0]["sentence"]
    for token in tokens:
        assert token["sentence"] == sentenceId
    return sentenceId + ":" + ",".join([str(x) for x in sorted([token["index"] for token in tokens])])

def getGoldExample(beginIndex, sentence, includeGaps=False):
    """
    For each token in a sentence there can be only one expression,
    which can have one or more words. A new expression begins with
    one of the MWE tags 'O', 'B' or 'b'.
    """
    if sentence[beginIndex]["supersense"] == None:
        return None
    tokens = [sentence[beginIndex]]
    mweType = tokens[0]["MWE"]
    assert mweType in ("O", "o", "B", "b"), tokens[0]
    if mweType in ("O", "o"):
        return tokens
    for i in range(beginIndex + 1, len(sentence)):
        mwe = sentence[i]["MWE"]
        if mwe in ("B", "O"):
            break
        elif mwe == "I":
            if mweType == "B":
                tokens.append(sentence[i])
            elif includeGaps: tokens.append(sentence[i])
        elif mwe == "i":
            if mweType == "b":
                tokens.append(sentence[i])
            elif includeGaps: tokens.append(sentence[i])
        elif mwe == "b":
            assert mweType == "B"
            if includeGaps: tokens.append(sentence[i])
        else:
            assert mwe == "o", sentence[i]
            if includeGaps: tokens.append(sentence[i])
    return tokens

def hasGaps(tokens):
    index = tokens[0]["index"]
    for token in tokens[1:]:
        assert token["index"] > index, tokens
        if token["index"] - index > 1:
            return True
    return False

class Corpus():
    def __init__(self, dataPath):
        self.dataPath = dataPath
        self.corpusFiles = {"train":"dimsum-data-1.5/dimsum16.train", "test":"dimsum-data-1.5/dimsum16.test.blind"}
        self.columns = ["index", "word", "lemma", "POS", "MWE", "parent", "strength", "supersense", "sentence"]
        self.MWETags = set(["O", "o", "B", "b", "I", "i"])
    
    def readExamples(self, filePath):
        with open(filePath) as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=self.columns,  delimiter="\t", quoting=csv.QUOTE_NONE)
            examples = [row for row in reader]
            for example in examples:
                example["index"] = int(example["index"]) - 1
                assert example["index"] >= 0
                example["parent"] = int(example["parent"]) if example["parent"] != "" else None
                example["supersense"] = example["supersense"] if example["supersense"] != "" else None
                assert example["MWE"] in self.MWETags, example
            return examples
    
    def printSentence(self, sentence):
        for token in sentence:
            print "\t".join(str(token[x]) for x in self.columns) 
    
    def readSentences(self, filePath):
        examples = self.readExamples(filePath)
        sentenceDict = OrderedDict()
        for example in examples:
            if example["sentence"] not in sentenceDict:
                sentenceDict[example["sentence"]] = []
            sentenceDict[example["sentence"]].append(example)
        return [sentenceDict[x] for x in sentenceDict]
    
    def readCorpus(self, setNames, filePaths = None):
        self.corpus = {}
        for setName in setNames:
            if filePaths:
                filePath = filePaths["setName"]
            else:
                filePath = os.path.join(self.dataPath, self.corpusFiles[setName])
            print "Reading set", setName, "from", filePath
            self.corpus[setName] = self.readSentences(filePath) 
    
    def getSentences(self, setName):
        if setName in self.corpus: 
            return self.corpus[setName]
        else:
            return []