from src.Experiment import Experiment

class CountMWE(Experiment):
    def __init__(self):
        super(CountMWE, self).__init__()
    
    def closeMWE(self, mwe, sentence):
        self.meta.insert("mwe", {"mwe":"".join(mwe), "sentence":sentence[0]["sentence"], "size":len(mwe)})
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
                    self.closeMWE(mwe, sentence)
                    if tag.islower():
                        lowerMWE = []
                        mwe = lowerMWE
                    else:
                        upperMWE = []
                        mwe = lowerMWE
                assert len(mwe) == 0, token
                mwe.append(tag)
            elif tag in ("I", "i"):
                assert len(mwe) > 0, token
                mwe.append(tag)
            elif tag == "o":
                if len(upperMWE) > 0:
                    upperMWE.append(tag)
                if len(lowerMWE) > 0:
                    lowerMWE.append(tag)
            else:
                assert tag == "O", token
                if upperMWE:
                    self.closeMWE(upperMWE, sentence)
                    upperMWE = []
                if lowerMWE:
                    self.closeMWE(lowerMWE, sentence)
                    lowerMWE = []
