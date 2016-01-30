import os
import csv
from collections import OrderedDict

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