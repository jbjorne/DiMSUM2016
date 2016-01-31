from FeatureBuilder import FeatureBuilder
from src.yelp.YelpDataset import getYelpDataset

class YelpFeatureBuilder(FeatureBuilder):
    
    def __init__(self):
        super(YelpFeatureBuilder, self).__init__("Yelp", ["Yelp"])
    
    def initialize(self, dataPath):
        FeatureBuilder.initialize(self, dataPath)
        self.dataset = getYelpDataset(dataPath)
    
    def buildSpanFeatures(self):
        text = " ".join([x["word"].lower() for x in self.tokens])
        if text in self.dataset.locations:
            for row in self.dataset.locations[text]:
                self.build("YELP_TYPE:" + row["type"])
                self.build("YELP_CATEGORY:" + row["category"])
        
        for token in self.tokens:
            text = token["word"].lower()
            if len(text) >= 3 and text in self.dataset.names:
                self.build("YELP_FIRST_NAME")
        
        if len(self.tokens) == 1:
            text = self.tokens[0]["word"].lower()
            if text in self.dataset.parts["single"]:
                for category in self.dataset.parts["single"][text]:
                    self.build("YELP_SINGLE:" + category)
                    self.build("YELP_PART:" + category)
        else:
            for category in self.dataset.parts["first"].get(self.tokens[0]["word"].lower(), []):
                self.build("YELP_FIRST:" + category)
                self.build("YELP_PART:" + category)
            for category in self.dataset.parts["last"].get(self.tokens[-1]["word"].lower(), []):
                self.build("YELP_LAST:" + category)
                self.build("YELP_PART:" + category)
            for i in range(1, len(self.tokens) - 1):
                for category in self.dataset.parts["middle"].get(self.tokens[i]["word"].lower(), []):
                    self.build("YELP_MIDDLE:" + category)
                    self.build("YELP_PART:" + category)

            self.build("YELP_BUSINESS")