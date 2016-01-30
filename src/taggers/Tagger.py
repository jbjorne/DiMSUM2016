from src.Resources import Resources

class Tagger(object):
    def __init__(self, name=None, resources=None):
        self.name = None
        self.dataPath = None
        self.resources = []
        if resources != None:
            validator = Resources()
            for key in resources:
                self.resources.append(validator.validate(key))
    
    def initialize(self, dataPath):
        self.dataPath = dataPath
    
    def tag(self, tokens):
        raise NotImplementedError