from src.Experiment import Experiment

class CountMWE(Experiment):
    def __init__(self):
        super(CountMWE, self).__init__()
    
    def closeMWE(self, mwe, sentence):
        self.meta.insert("mwe", {"mwe":"".join([x["MWE"] for x in mwe]), 
                                 "sentence":sentence[0]["sentence"], 
                                 "num_tokens":len(mwe),
                                 "span":" ".join([x["word"] for x in mwe]),
                                 "text":" ".join([x["lemma"] for x in mwe if x["MWE"] not in ("o", "O")])
                                 })
        assert mwe in (self.lowerMWE, self.upperMWE)
        if mwe == self.lowerMWE:
            self.lowerMWE = []
            return self.lowerMWE
        else:
            assert mwe == self.upperMWE
            self.upperMWE = []
            return self.upperMWE
    
    def processSentence(self, sentence, setName):
        self.upperMWE = []
        self.lowerMWE = []
        for token in sentence:
            tag = token["MWE"]
            mwe = self.lowerMWE if tag.islower() else self.upperMWE
            if tag in ("B", "b"):
                if len(mwe) > 0:
                    mwe = self.closeMWE(mwe, sentence)
                mwe.append(token)
            elif tag in ("I", "i"):
                assert len(mwe) > 0, token
                mwe.append(token)
            elif tag == "o":
                if len(self.upperMWE) > 0:
                    self.upperMWE.append(token)
                if len(self.lowerMWE) > 0:
                    self.lowerMWE.append(token)
            else:
                assert tag == "O", token
                if self.upperMWE:
                    self.closeMWE(self.upperMWE, sentence)
                if self.lowerMWE:
                    self.closeMWE(self.lowerMWE, sentence)
