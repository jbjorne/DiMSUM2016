from src.Experiment import Experiment
from src.FeatureGroup import FeatureGroup
from src.taggers.WordNetTagger import WordNetTagger
from src.taggers.OutOfVocabularyTagger import OutOfVocabularyTagger
from src.builders.BasicFeatureBuilder import BasicFeatureBuilder
from src.builders.BasicFeatureBuilder2 import BasicFeatureBuilder2
from src.taggers.YelpTagger import YelpTagger
from src.taggers.WikipediaTagger import WikipediaTagger
from src.builders.YelpFeatureBuilder import YelpFeatureBuilder
from src.builders.ContextFeatureBuilder import ContextFeatureBuilder

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

class TestYelpTagger(Experiment):
    def __init__(self):
        super(TestYelpTagger, self).__init__()
        self.featureGroups = [TestFeatureGroup]
        self.taggers = [YelpTagger]

class SuperSenseTest(Experiment):
    def __init__(self):
        super(SuperSenseTest, self).__init__()
        self.featureGroups = [TestFeatureGroup]
        self.taggers = [WordNetTagger, OutOfVocabularyTagger]
        
class TestTask2Basic2(Experiment):
    def __init__(self):
        super(TestTask2Basic2, self).__init__()
        self.featureGroups = [BasicFeatureBuilder2] # [BasicFeatureBuilder, ContextFeatureBuilder, YelpFeatureBuilder]
        #self.taggers = [WordNetTagger, YelpTagger, WordNetTagger(exact=False), OutOfVocabularyTagger]
        self.taggers = [WordNetTagger, YelpTagger, OutOfVocabularyTagger]

class Task1(Experiment):
    def __init__(self):
        super(Task1, self).__init__()
        self.featureGroups = [BasicFeatureBuilder] # [BasicFeatureBuilder, ContextFeatureBuilder]
        self.taggers = [WordNetTagger, OutOfVocabularyTagger]

class Task2(Experiment):
    def __init__(self):
        super(Task2, self).__init__()
        self.featureGroups = [BasicFeatureBuilder] # [BasicFeatureBuilder, ContextFeatureBuilder, YelpFeatureBuilder]
        #self.taggers = [WordNetTagger, YelpTagger, WordNetTagger(exact=False), OutOfVocabularyTagger]
        self.taggers = [WordNetTagger, YelpTagger, OutOfVocabularyTagger]

class Task3(Experiment):
    def __init__(self):
        super(Task3, self).__init__()
        self.featureGroups = [BasicFeatureBuilder] # [BasicFeatureBuilder, ContextFeatureBuilder, YelpFeatureBuilder]
        self.taggers = [WordNetTagger, WikipediaTagger, YelpTagger, OutOfVocabularyTagger]