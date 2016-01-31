from Tagger import Tagger
from src.Meta import Meta
import os

class YelpTagger(Tagger):
    def __init__(self):
        super(YelpTagger, self).__init__("Yelp", ["Yelp"])
        self.categoryMap = {"business":["n.group"],#["n.group", "n.artifact", "n.communication"],
                            "neighborhood":["n.location"],
                            "school":["n.location"],
                            "person":["n.person"],
                            "Restaurants":["n.group", "n.food"]}
    
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
        allUpper, leftUpper, rightUpper = self.getCapitalization(tokens, sentence)

        # Tag exact matches
        types = self.tagExact(tokens)
        
        # Tag personal names
        if len(types) == 0 and len(tokens) <= 2 and allUpper:
            firstName = tokens[0]["word"].lower()
            if len(firstName) >= 3 and firstName in self.names:
                types += ["person"]
        
        # Tag partial matches
        if len(types) == 0 and len(tokens) > 1 and allUpper and not leftUpper and not rightUpper:
            types += self.tagPartial(tokens, sentence)
        
        # Convert Yelp types to categories
        categories = []
        for yelpType in types:
            if yelpType in self.categoryMap:
                categories.extend(self.categoryMap[yelpType])
        return list(set(categories))
        
    def tagExact(self, tokens):        
        text = " ".join([x["word"].lower() for x in tokens])
        if text in self.locations:
            return [row["type"] for row in self.locations[text]]
        return []
    
    def tagPartial(self, tokens, sentence):
        for token in tokens:
            if token["POS"] not in ("NOUN", "PROPN",):
                return []
        types = []
        if len(tokens) == 1:
            text = tokens[0]["word"].lower()
            if text in self.parts["single"]:
                types.extend(self.parts["single"][text])
        else:
            last = self.parts["last"].get(tokens[-1]["word"].lower(), [])
            if last:
                types += last
                types += self.parts["first"].get(tokens[0]["word"].lower(), [])
                for i in range(1, len(tokens) - 1):
                    types += self.parts["middle"].get(tokens[i]["word"].lower(), [])
        if len(types) > 0:
            types += ["business"]
            #print "Match", [x["word"] for x in tokens], types
        return types
        