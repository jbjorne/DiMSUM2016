from FeatureBuilder import FeatureBuilder

class BasicFeatureBuilder(FeatureBuilder):
    
    def __init__(self):
        super(FeatureBuilder, self).__init__("BASIC", ["WordNet"])
    
    def buildTokenFeatures(self, token):
        features = []
        numTokens = len(self.tokens)
        for key in ("lemma", "POS", "word"):
            values = [x[key].lower() for x in self.tokens]
            features += ["TOKEN_" + key + ":" + x for x in values]
            if numTokens == 1:
                features += ["SINGLE_TOKEN_" + key + ":" + x for x in values]
            elif token == self.tokens[0]:
                features += ["FIRST_TOKEN_" + key + ":" + x for x in values]
            elif token == self.tokens[-1]:
                features += ["LAST_TOKEN_" + key + ":" + x for x in values]
        return features
    
    def buildSpanFeatures(self):
        features = []
        
        supersensePOS = self.supersense.split(".")[0]
        
        features.append("SPAN_LEX:" + self.supersense)
        features.append("SPAN_LEX:" + supersensePOS)
        for sense in self.supersenses:
            if sense != self.supersense:
                features.append("SPAN_OTHER_LEX:" + self.supersense)
                features.append("SPAN_OTHER_LEX:" + supersensePOS)
        
        for key in ("lemma", "POS", "word"):
            values = "_".join([x[key].lower() for x in self.tokens])
            features.append("SPAN_" + key + ":" + values)
            features.append("SPAN_" + key + ":" + values + ":" + self.supersense)
            features.append("SPAN_" + key + ":" + values + ":" + supersensePOS)
        
        return features