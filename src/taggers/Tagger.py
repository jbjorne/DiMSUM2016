from src.Resources import Resources
from POSFilter import POSFilter

class Tagger(object):
    def __init__(self, name=None, resources=None):
        self.name = name
        self.dataPath = None
        self.resources = []
        if resources != None:
            validator = Resources()
            for key in resources:
                self.resources.append(validator.validate(key))
        self.posFilter = POSFilter()
        self.POS_FILTER_KEEP = "POS_FILTER"
    
    def initialize(self, dataPath):
        self.dataPath = dataPath
    
    def tag(self, tokens, taggingState):
        raise NotImplementedError
    
    def filterByPOS(self, tokens, supersenses, taggingState):
        if len(supersenses) == 0:
            return supersenses
        if self.POS_FILTER_KEEP in taggingState:
            keep = taggingState[self.POS_FILTER_KEEP]
        else:
            keep = self.posFilter.filterByPOS(tokens)
            taggingState[self.POS_FILTER_KEEP] = keep
        if keep != "*":
            supersenses = [x for x in supersenses if x[0:2] in keep]
        return supersenses