import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.Database import Database

class Analysis(object):
    def __init__(self, dataPath=None):
        self.dataPath = dataPath
    
    def _getDatabase(self, inDir, fileStem=None):
        if fileStem == None:
            fileStem = "examples"
        return Database(os.path.join(inDir, fileStem + ".sqlite"))
        
    def analyse(self, inDir, fileStem=None, hidden=False):
        raise NotImplementedError