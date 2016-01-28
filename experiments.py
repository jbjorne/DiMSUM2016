from src.Experiment import Experiment
from src.FeatureGroup import FeatureGroup

###############################################################################
# Features
###############################################################################

class TestFeatureGroup(FeatureGroup):
    def __init__(self):
        super(TestFeatureGroup, self).__init__("TEST")
    def buildFeatures(self, tokens, supersense, sentence, supersenses):
        return [x["lemma"] for x in tokens], None

###############################################################################
# Experiments
###############################################################################

class MWETest(Experiment):
    def __init__(self):
        super(MWETest, self).__init__()
        self.featureGroups = [TestFeatureGroup]
    
    def getLabel(self, example):
        return example["MWE"]

class SuperSenseTest(Experiment):
    def __init__(self):
        super(SuperSenseTest, self).__init__()
        self.featureGroups = [TestFeatureGroup]
    
#     def getLabel(self, example):
#         return example["supersense"]