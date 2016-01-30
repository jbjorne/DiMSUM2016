class Corpus():
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
    