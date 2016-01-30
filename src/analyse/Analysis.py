import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.Meta import Meta

class Analysis(object):
    def __init__(self, dataPath=None):
        self.dataPath = dataPath
    
    def _getMeta(self, inDir, fileStem=None):
        if fileStem == None:
            fileStem = "examples"
        return Meta(os.path.join(inDir, fileStem + ".meta.sqlite"))
        
    def analyse(self, inDir, fileStem=None, hidden=False):
        raise NotImplementedError