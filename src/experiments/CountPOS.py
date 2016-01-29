from src.Experiment import Experiment

class CountMWE(Experiment):
    def __init__(self):
        super(CountMWE, self).__init__()
    
    def getTokenValue(self, sentence, key, index):
        if index < 0 or index > len(sentence):
            return None
        else:
            return sentence[index][key]
    
    def closeMWE(self, mwe, sentence):
        self.meta.insert("mwe", {"mwe":"".join([x["MWE"] for x in mwe]),
                                 "supersense":mwe[0]["supersense"],
                                 "before":self.getTokenValue(sentence, "word", mwe[0]["index"] - 1),
                                 "after":self.getTokenValue(sentence, "word", mwe[-1]["index"] + 1), 
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
            self.meta.insert("token", dict(token, token_id=self._getTokenId(token)))
            
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
