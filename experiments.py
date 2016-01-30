from src.Experiment import Experiment
from src.FeatureGroup import FeatureGroup
from src.taggers.WordNetTagger import WordNetTagger
from src.taggers.OutOfVocabularyTagger import OutOfVocabularyTagger

###############################################################################
# Features
###############################################################################

class TestFeatureGroup(FeatureGroup):
    def __init__(self):
        super(TestFeatureGroup, self).__init__("TEST")
    def buildFeatures(self, tokens, supersense, sentence, supersenses):
        lemmas = [x["lemma"] for x in tokens]
        features = [x["lemma"] for x in tokens]
        features.append("EXACT:" + "_".join(lemmas))
        features.append(supersense)
        return features, None

###############################################################################
# Experiments
###############################################################################


class SuperSenseTest(Experiment):
    def __init__(self):
        super(SuperSenseTest, self).__init__()
        self.featureGroups = [TestFeatureGroup]
        self.taggers = [WordNetTagger, OutOfVocabularyTagger]