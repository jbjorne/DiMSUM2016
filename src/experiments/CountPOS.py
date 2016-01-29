from src.Experiment import Experiment
from _collections import defaultdict
from itertools import groupby

class CountPOS(Experiment):
    def __init__(self):
        super(CountPOS, self).__init__()
        self.posCounts = {}
        self.goldCounts = {}
    
    def processSentence(self, sentence, setName):
        for i in range(len(sentence)):
            token = sentence[i]
            self.meta.insert("token", dict(token, token_id=self._getTokenId(token)))
            self.countPOS(token)
            self.countGoldPOS(i, sentence, setName)
    
    def countGoldPOS(self, i, sentence, setName):       
        goldTokens = self.getGoldExample(i, sentence, includeGaps=False)
        if goldTokens:
            self.insertExampleMeta(label=None, 
                                   supersense=None, 
                                   goldSupersense=goldTokens[0]["supersense"], 
                                   tokens=goldTokens, 
                                   features={}, 
                                   setName=setName, 
                                   textDetected=False, 
                                   isNested=False)
            goldPOS = [x["POS"] for x in goldTokens]
            goldPOS = [x[0] for x in groupby(goldPOS)]
            goldPOS = ":".join(goldPOS)
            if goldPOS not in self.goldCounts:
                self.goldCounts[goldPOS] = 0
            self.goldCounts[goldPOS] += 1
            
    def countPOS(self, token):
        pos = str(token["POS"])
        if pos not in self.posCounts:
            self.posCounts[pos] = {} #{c:0 for c in list("BIObio") + ["None"]}
            self.posCounts[pos]["POS"] = pos
            self.posCounts[pos]["not_O"] = 0
            self.posCounts[pos]["total"] = 0
            for char in "bio":
                self.posCounts[pos][char + "_low"] = 0
                self.posCounts[pos][char.upper() + "_up"] = 0
        
        self.posCounts[pos]["total"] += 1      
        if token["supersense"] != None or token["MWE"] != "O":
            mwe = token["MWE"]
            if mwe not in ("O", "o"):
                self.posCounts[pos]["not_O"] += 1
            if mwe.islower():
                mwe += "_low"
            else:
                mwe += "_up"
            self.posCounts[pos][mwe] += 1
    
    def endExperiment(self):
        rows = [self.posCounts[key] for key in sorted(self.posCounts.keys())]
        self.meta.insert_many("pos_count", rows, True)
        
        self.meta.insert_many("gold_count", [{"POS":key, "total":self.goldCounts[key]} for key in sorted(self.goldCounts.keys())], True)
        
        super(CountPOS, self).endExperiment()
            