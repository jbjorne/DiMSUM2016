from src.FeatureGroup import FeatureGroup

class FeatureBuilder(FeatureGroup):
    def __init__(self, name, resources=None):
        super(FeatureBuilder, self).__init__(name, resources)
    
    def buildFeatures(self, tokens, supersense, sentence, supersenses):
        self.supersense = supersense
        self.supersenses = supersenses
        self.sentence = sentence
        self.tokens = tokens
        
        self._features = []
        self._values = []
        
        self.buildSpanFeatures()
        for token in self.tokens:
            self.buildTokenFeatures(token)
        
        return self._features, self._values
    
    def buildSpanFeatures(self):
        return
    
    def buildTokenFeatures(self, token):
        return
    
    def build(self, name, value=1):
        self._features.append(name)
        self._values.append(value)
    
    def buildMany(self, names, values=None):
        if values == None:
            values = [1] * len(names)
        self._features.extend(names)
        self._values.extend(values)
        