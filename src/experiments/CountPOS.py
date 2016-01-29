from src.Experiment import Experiment

class CountPOS(Experiment):
    def __init__(self):
        super(CountPOS, self).__init__()
        self.posCounts = {None:0}
        for c in "BIObio":
            self.posCounts[c] = 0
    
    def processSentence(self, sentence, setName):
        for token in sentence:
            self.meta.insert("token", dict(token, token_id=self._getTokenId(token)))
            pos = token["POS"]
            if pos not in self.posCounts:
                self.posCounts[pos] = {c:0 for c in list("BIObio") + [None]}
            self.posCounts[pos][token["MWE"]] += 1
    
    def endExperiment(self):
        rows = [self.posCounts[key] for key in sorted(self.posCounts.keys())]
        self.meta.insert_many("pos_count", rows, True)
        super(CountPOS, self).endExperiment()
            