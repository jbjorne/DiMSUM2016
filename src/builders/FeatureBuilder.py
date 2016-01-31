from src.FeatureGroup import FeatureGroup

class FeatureBuilder(FeatureGroup):
    def __init__(self, name, resources=None):
        super(FeatureBuilder, self).__init__(name, resources)
    
    def buildFeatures(self, tokens, supersense, sentence, supersenses):
        self.supersense = supersense
        self.supersenses = supersenses
        self.sentence = sentence
        self.tokens = tokens
        
        features = self.buildSpanFeatures()
        for token in self.tokens:
            features += self.buildTokenFeatures(token)
        
        return features, None
    
    def buildSpanFeatures(self):
        return []
    
    def buildTokenFeatures(self, token):
        return []
        