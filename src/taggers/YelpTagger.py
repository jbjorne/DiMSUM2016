from Tagger import Tagger
from src.Meta import Meta
import os

class YelpTagger(Tagger):
    def __init__(self):
        super(YelpTagger, self).__init__("Yelp", ["Yelp"])
    
    def initialize(self, dataPath):
        super(YelpTagger, self).initialize(dataPath)
        dbPath = os.path.join(dataPath, "yelp", "yelp.sqlite")
        if not os.path.exists(dbPath):
            raise Exception("No Yelp database at " + dbPath)
        self.meta = Meta(dbPath)
        self.locations = set([row["lower"] for row in self.meta.db["location"].all()])
    
    def tag(self, tokens, sentence, taggingState):
        for key, useLowerCase in [("lemma", False), ("word", True)]:
            text = " ".join([x[key] for x in tokens])
            if useLowerCase:
                text = text.lower()
            if text in self.locations:
                return ["yelp"]
            #rows = [x for x in self.meta.db["location"].find(lower=text)]
            #if len(rows) > 0:
            #    return ["yelp"]
        return None
        