from src.Experiment import Experiment

class CountMWE(Experiment):
    def __init__(self):
        super(CountMWE, self).__init__()
    def processSentence(self, sentence, setName):
        upperMWE = []
        lowerMWE = []
        for token in sentence:
            mwe = lowerMWE if token["MWE"].islower() else upperMWE
            if token["MWE"] in ("B", "b"):
                assert len(mwe) == 0
                mwe.append(token["MWE"])
            elif token["MWE"] in ("I", "i"):
                assert len(mwe) > 0
                mwe.append(token["MWE"])
            elif token["MWE"] == "o":
                if len(upperMWE) > 0:
                    upperMWE.append()
                

            self.meta.insert("bwe", dict(token, token_id=self._getTokenId(token), num_examples=len(supersenses), num_pos=numPos))
