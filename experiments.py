from src.Experiment import Experiment
from src.FeatureGroup import FeatureGroup

###############################################################################
# Features
###############################################################################

class TestFeatureGroup(FeatureGroup):
    def __init__(self):
        super(TestFeatureGroup, self).__init__("TEST")
    def buildFeatures(self, example, sentence):
        return [example["word"]], None

###############################################################################
# Experiments
###############################################################################

class MWETest(Experiment):
    def __init__(self):
        super(MWETest, self).__init__()
        self.featureGroups = [TestFeatureGroup]
    
    def getLabel(self, example):
        return example["MWE"]
