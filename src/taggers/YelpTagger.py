from Tagger import Tagger
from src.Database import Database
import os
from src.yelp.YelpDataset import getYelpDataset

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
        self.dataset = getYelpDataset(dataPath)
        
    def tag(self, tokens, sentence, taggingState): 
        allUpper, leftUpper, rightUpper = self.getCapitalization(tokens, sentence)

        # Tag exact matches
        types = self.tagExact(tokens)
        
        # Tag personal names
        if len(types) == 0 and len(tokens) <= 2 and allUpper:
            firstName = tokens[0]["word"].lower()
            if len(firstName) >= 3 and firstName in self.dataset.names:
                types += ["person"]
        
        # Tag partial matches
        if len(types) == 0 and len(tokens) > 1 and allUpper and not leftUpper and not rightUpper:
            types += self.tagPartial(tokens, sentence)
        
        # Convert Yelp types to categories
        categories = []
        for yelpType in types:
            if yelpType in self.categoryMap:
                categories.extend(self.categoryMap[yelpType])
        #if tokens[0]["word"] == "Pacific":
        #    print [x["word"] for x in tokens], categories
        return list(set(categories))
        
    def tagExact(self, tokens):        
        text = " ".join([x["word"].lower() for x in tokens])
        if text in self.dataset.locations:
            return [row["type"] for row in self.dataset.locations[text]]
        return []
    
    def tagPartial(self, tokens, sentence):
        #if tokens[0]["word"] == "Pacific":
        #    print [x["word"] for x in tokens]
        for token in tokens:
            if token["POS"] not in ("NOUN", "PROPN",):
                return []
        types = []
        if len(tokens) == 1:
            text = tokens[0]["word"].lower()
            if text in self.dataset.parts["single"]:
                types.extend(self.dataset.parts["single"][text])
        else:
            last = self.dataset.parts["last"].get(tokens[-1]["word"].lower(), [])
            if last:
                types += last
                types += self.dataset.parts["first"].get(tokens[0]["word"].lower(), [])
                for i in range(1, len(tokens) - 1):
                    types += self.dataset.parts["middle"].get(tokens[i]["word"].lower(), [])
        if len(types) > 0:
            types += ["business"]
            #print "Match", [x["word"] for x in tokens], types
        #if tokens[0]["word"] == "Pacific":
        #    print [x["word"] for x in tokens], types
        return types
        