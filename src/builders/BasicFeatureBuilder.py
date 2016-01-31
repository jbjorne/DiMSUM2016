from FeatureBuilder import FeatureBuilder

class BasicFeatureBuilder(FeatureBuilder):
    
    def __init__(self):
        super(FeatureBuilder, self).__init__("BASIC", ["WordNet"])
    
    def buildTokenFeatures(self, token):
        numTokens = len(self.tokens)
        for key in ("lemma", "POS", "word"):
            values = [x[key].lower() for x in self.tokens]
            self.buildMany(["TOKEN_" + key + ":" + x for x in values])
            if numTokens == 1:
                self.buildMany(["SINGLE_TOKEN_" + key + ":" + x for x in values])
            elif token == self.tokens[0]:
                self.buildMany(["FIRST_TOKEN_" + key + ":" + x for x in values])
            elif token == self.tokens[-1]:
                self.buildMany(["LAST_TOKEN_" + key + ":" + x for x in values])
    
    def buildSpanFeatures(self):
        supersensePOS = self.supersense.split(".")[0]
        
        self.build("SPAN_LEX:" + self.supersense)
        self.build("SPAN_LEX:" + supersensePOS)
        for sense in self.supersenses:
            if sense != self.supersense:
                self.build("SPAN_OTHER_LEX:" + self.supersense)
                self.build("SPAN_OTHER_LEX:" + supersensePOS)
        
        self.build("SPAN_LEX_NUM_" + str(len(self.supersenses)))
        self.build("SPAN_LEX_NUM_VALUE", len(self.supersenses))
        
        for key in ("lemma", "POS", "word"):
            values = "_".join([x[key].lower() for x in self.tokens])
            self.build("SPAN_" + key + ":" + values)
            self.build("SPAN_" + key + ":" + values + ":" + self.supersense)
            self.build("SPAN_" + key + ":" + values + ":" + supersensePOS)