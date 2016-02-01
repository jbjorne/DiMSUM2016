from Tagger import Tagger
import os
import codecs
import json

class WikipediaTagger(Tagger):
    def __init__(self):
        super(WikipediaTagger, self).__init__("Wikipedia", ["Wikipedia"])

    def initialize(self, dataPath):
        super(WikipediaTagger, self).initialize(dataPath)
#         filePath = os.path.join(dataPath, "wikipedia", "enwiki-latest-all-titles-in-ns0")
#         if not os.path.exists(filePath):
#             raise Exception("Wikipedia titles file does not exist")
#         print "Loading Wikipedia titles...",
#         f = codecs.open(filePath, "rt", "utf-8")
#         self.titles = {}
#         for title in f.readlines():
#             title = title.strip()
#             origTitle = title
#             self.titles[title.strip().lower()] = origTitle
#             disambiguation = None
#             if title.endswith(")") and "(" in title:
#                 title, disambiguation =title.rsplit("(", 1)
#                 title = title.strip()
#                 disambiguation = disambiguation.rstrip(" )")
#                 self.titles[title.strip().lower()] = origTitle
#         f.close()
        print "Loading senses"
        filePath = os.path.join(dataPath, "wikipedia", "page-senses.json")
        f = codecs.open(filePath, "rt", "utf-8")
        items = json.loads(f.read(), "utf-8")
        self.titles = {x["t"].strip().lower():x["s"] for x in items}
        f.close()
    
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
                supersenses = self.titles[text] #[self.titles[text]]
                if len(supersenses) > 0:
                    return supersenses
        return []