from Tagger import Tagger
from src.Meta import Meta
import os

class YelpTagger(Tagger):
    def __init__(self):
        super(YelpTagger, self).__init__("Yelp", ["Yelp"])
        self.categoryMap = {"business":["n.group", "n.artifact", "n.communication"],
                            "neighborhood":["n.location"],
                            "school":["n.location"]}
    
    def initialize(self, dataPath):
        super(YelpTagger, self).initialize(dataPath)
        dbPath = os.path.join(dataPath, "yelp", "yelp.sqlite")
        if not os.path.exists(dbPath):
            raise Exception("No Yelp database at " + dbPath)
        self.meta = Meta(dbPath)
        
        self.parts = {"middle":{}, "first":{}, "last":{}, "single":{}}
        for row in self.meta.db.query("select * from part where total > 10;"):
            pos = row["position"]
            text = row["token"]
            if text not in self.parts[pos]:
                self.parts[pos][text] = []
            self.parts[pos][text].append(row["category"])
        
        self.locations = {}
        for row in self.meta.db["location"].all():
            name = row["lower"]
            if row["lower"] not in self.locations:
                self.locations[name] = []
            self.locations[name].append(row)
    
    def tag(self, tokens, sentence, taggingState):
#         for token in tokens:
#             if token["word"][0].islower():
#                 return []
#         left, right = self.getFlankingTokens(tokens, sentence)
#         if left and left["word"][0].isupper():
#             return []
#         if right and right["word"][0].isupper():
#             return []

#         if len(tokens) == 1 and len(taggingState["supersenses"]) > 0:
#             return
        
        text = " ".join([x["word"].lower() for x in tokens])
        if text in self.locations:
            yelpTypes = [row["type"] for row in self.locations[text]]
            categories = []
            for yelpType in yelpTypes:
                categories.extend(self.categoryMap[yelpType])
            return categories
            #return ["yelp." + row["type"] for row in self.locations[text]]
        else:
            return []
    
    def tagPartial(self, tokens, sentence):
        for token in tokens:
            if token["word"][0].islower():
                return None
        categories = []
        if len(tokens) == 1:
            text = tokens[0]["word"].lower()
            if text in self.parts["single"]:
                categories.extend(self.parts["single"][text])
        else:
            last = self.parts["last"].get(tokens[-1]["word"].lower(), [])
            if last:
                categories += last
                categories += self.parts["first"].get(tokens[0]["word"].lower(), [])
                for i in range(1, len(tokens) - 1):
                    categories += self.parts["middle"].get(tokens[i]["word"].lower(), [])
        if len(categories) > 0:
            return sorted(set(categories))
        return None
        