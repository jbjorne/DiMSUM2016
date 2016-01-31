from FeatureBuilder import FeatureBuilder

class BasicFeatureBuilder(FeatureBuilder):
    def buildSpanFeatures(self):
        lemmas = [x["lemma"] for x in self.tokens]
        features = ["LEMMA:" + x for x in lemmas]
        features.append("SPAN_LEMMA:" + "_".join(self.lemmas))
        features.append("SPAN_LEX:" + self.supersense)
        return features