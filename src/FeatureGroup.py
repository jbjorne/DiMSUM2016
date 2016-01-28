from collections import OrderedDict
class FeatureGroup(object):
    def __init__(self, name):
        self.name = name
    
    def initialize(self, dataPath):
        self.dataPath = dataPath
    
    def processExample(self, example, sentence, featureIds, meta):
        features, values = self.buildFeatures(example, sentence)
        return self._buildVector(features, values, featureIds, meta)
    
    def buildFeatures(self, example, sentence):
        raise NotImplementedError
    
    def _getFeatureNameAsString(self, featureNameParts):
        return self.name + ":" + ":".join([str(x) for x in featureNameParts])        
    
    def _getFeatureId(self, featureName, featureIds, meta):
        if featureName not in featureIds:
            featureIds[featureName] = len(featureIds)
            meta.insert("feature", {"name":featureName, "id":featureIds[featureName]})
        return featureIds[featureName]
    
    def _buildVector(self, features, values, exampleFeatures, featureIds, meta):
        if values == None:
            values = [1] * len(features) # Use default weight for all features
        assert len(features) == len(values)
        featureSet = OrderedDict
        for feature, value in zip(features, values):
            if not isinstance(feature, basestring):
                feature = self._getFeatureNameAsString(feature)
            featureSet[self._getFeatureId(feature, featureIds, meta)] = value
        return featureSet
