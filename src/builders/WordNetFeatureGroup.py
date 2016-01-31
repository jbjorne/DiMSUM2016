from src.FeatureGroup import FeatureGroup

class WordNetFeatureBuilder(FeatureGroup):
    def __init__(self):
        super(WordNetFeatureBuilder, self).__init__("WN")
    
    def buildFeatures(self, tokens, supersense, sentence, supersenses):
        lemmas = [x["lemma"] for x in tokens]
        features = [x["lemma"] for x in tokens]
        features.append("EXACT:" + "_".join(lemmas))
        features.append(supersense)
        return features, None