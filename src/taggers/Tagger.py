from src.Resources import Resources

def Tagger(object):
    def __init__(self, resources=None):
        self.resources = []
        if resources != None:
            validator = Resources()
            for key in resources:
                self.resources.append(validator.validate(key))
    
    def tag(self, tokens):
        raise NotImplementedError