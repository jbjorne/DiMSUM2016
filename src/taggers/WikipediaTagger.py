from Tagger import Tagger
import os
import codecs

class WikipediaTagger(Tagger):
    def __init__(self):
        super(WikipediaTagger, self).__init__("Wikipedia", ["Wikipedia"])

    def initialize(self, dataPath):
        super(WikipediaTagger, self).initialize(dataPath)
        filePath = os.path.join(dataPath, "wikipedia", "enwiki-latest-all-titles-in-ns0")
        if not os.path.exists(filePath):
            raise Exception("Wikipedia titles file does not exist")
        print "Loading Wikipedia titles...",
        f = codecs.open(filePath, "rt", "utf-8")
        self.titles = set([x.strip().lower() for x in f.readlines()])
        f.close()
        print "done"
    
    def tag(self, tokens, sentence, taggingState):
        if len(taggingState["supersenses"]) > 0:
            return []
        includesProperNoun = False
        for token in tokens:
            if token["POS"] == "PROPN":
                includesProperNoun = True
        if not includesProperNoun:
            return []
        for key in ("lemma", "word"):
            text = "_".join([x[key] for x in tokens])
            text = text.lower()
            if text in self.titles:
                supersenses = ["Wikipedia"]
                if len(supersenses) > 0:
                    return supersenses
        return []