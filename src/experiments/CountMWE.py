from src.Experiment import Experiment

class CountMWE(Experiment):
    def __init__(self):
        super(CountMWE, self).__init__()
    
    def closeMWE(self, mwe, sentence):
        self.meta.insert("mwe", {"mwe":"".join(mwe), "sentence":sentence[0]["sentence"], "size":len(mwe)})
    
    def processSentence(self, sentence, setName):
        upperMWE = []
        lowerMWE = []
        for token in sentence:
            tag = token["MWE"]
            mwe = lowerMWE if tag.islower() else upperMWE
            if tag in ("B", "b"):
                assert len(mwe) == 0, self.printSentence(sentence)
                mwe.append(tag)
            elif tag in ("I", "i"):
                assert len(mwe) > 0, self.printSentence(sentence)
                mwe.append(tag)
            elif tag == "o":
                if len(upperMWE) > 0:
                    upperMWE.append(tag)
                if len(lowerMWE) > 0:
                    lowerMWE.append(tag)
            else:
                assert tag == "O", self.printSentence(sentence)
                if upperMWE:
                    self.closeMWE(upperMWE, sentence)
                    upperMWE = []
                if lowerMWE:
                    self.closeMWE(lowerMWE, sentence)
                    lowerMWE = []
