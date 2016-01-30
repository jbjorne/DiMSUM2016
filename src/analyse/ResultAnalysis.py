from Analysis import Analysis

class ResultAnalysis(Analysis):
    def __init__(self, dataPath=None):
        super(ResultAnalysis, self).__init__(dataPath=dataPath)
        
    def analyse(self, inDir, fileStem=None, hidden=False, clear=True):
        meta = self._getMeta(inDir, fileStem)
        #if clear:
        #    meta.drop("project_analysis")
        self.predictions = None
        if "prediction" in meta.db:
            self.predictions = {x["example"]:x["predicted"] for x in meta.db["prediction"].all()}
