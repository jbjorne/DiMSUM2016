from Tagger import Tagger
from src.Meta import Meta
import os

class YelpTagger(Tagger):
    def __init__(self):
        super(YelpTagger, self).__init__("Yelp", ["Yelp"])
        self.categoryMap = {"business":["n.group"],#["n.group", "n.artifact", "n.communication"],
                            "neighborhood":["n.location"],
                            "school":["n.location"],
                            "n.person":["n.person"]}
    
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
        
        self.names = set([x["lower"] for x in self.meta.db.query("select * from first_name where total > 10;")])
        for name in ("the",):
            self.names.remove(name)
        
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
        types = self.tagExact(tokens)
        if len(types) == 0:
            types += self.tagNames(tokens)
        
        categories = []
        for yelpType in types:
            categories.extend(self.categoryMap[yelpType])
        return list(set(categories))
        
    def tagExact(self, tokens):        
        text = " ".join([x["word"].lower() for x in tokens])
        if text in self.locations:
            return [row["type"] for row in self.locations[text]]
        return []
    
    def tagNames(self, tokens):
        if len(tokens) <= 2:
            lemma = tokens[0]["lemma"]
            if len(lemma) >= 3 and lemma in self.names:
                return ["n.person"]
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
        