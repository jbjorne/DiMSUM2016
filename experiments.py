from src.Experiment import Experiment
from src.FeatureGroup import FeatureGroup

###############################################################################
# Features
###############################################################################

class TestFeatureGroup(FeatureGroup):
    def __init__(self):
        super(TestFeatureGroup, self).__init__("TEST")
    def buildFeatures(self, tokens, supersense, sentence, supersenses):
        features = [x["lemma"] for x in tokens]
        features.append(supersense)
        return features, None

###############################################################################
# Experiments
###############################################################################


class SuperSenseTest(Experiment):
    def __init__(self):
        super(SuperSenseTest, self).__init__()
        self.featureGroups = [TestFeatureGroup]