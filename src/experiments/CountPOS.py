from src.Experiment import Experiment
from _collections import defaultdict

class CountPOS(Experiment):
    def __init__(self):
        super(CountPOS, self).__init__()
        self.posCounts = {}
    
    def processSentence(self, sentence, setName):
        for token in sentence:
            self.meta.insert("token", dict(token, token_id=self._getTokenId(token)))
            pos = str(token["POS"])
            if pos not in self.posCounts:
                self.posCounts[pos] = defaultdict(int) #{c:0 for c in list("BIObio") + ["None"]}
                self.posCounts[pos]["POS"] = pos
                self.posCounts[pos]["None"] = 0
                for char in "bio":
                    self.posCounts[pos][char + "_low"] = 0
                    self.posCounts[pos][char.upper() + "_up"] = 0
                    
            mwe = token["MWE"]
            if mwe.islower():
                mwe += "_low"
            else:
                mwe += "_up"
            self.posCounts[pos][mwe] += 1
    
    def endExperiment(self):
        rows = [self.posCounts[key] for key in sorted(self.posCounts.keys())]
        print rows
        self.meta.insert_many("pos_count", rows, True)
        super(CountPOS, self).endExperiment()
            