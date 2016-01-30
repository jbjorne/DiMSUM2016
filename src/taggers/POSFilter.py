class POSFilter():
    def __init__(self):
        self.nounPOS = set(["NOUN", "PROPN"])
        self.verbPOS = set(["VERB"])
        self.removeSingle = set(["ADJ", "ADP", "ADV", "CONJ", "DET", "INTJ", "PART", "PRON", "SCONJ", "X"])
    
    def filterByPOS(self, tokens):
        firstPOS = tokens[0]["POS"]
        lastPOS = tokens[0]["POS"]
        numTokens = len(tokens)
        if firstPOS in self.nounPOS: # Noun
            keep = ("n.",)
            if lastPOS in self.verbPOS:
                keep = ("v.", ".n")
        elif firstPOS in self.verbPOS: # Verb
            keep = ("v.") 
            if lastPOS in self.nounPOS:
                keep = ("v.", ".n")
        elif numTokens == 1:
            if firstPOS in ("NUM", "SYM"):
                keep = ("n.",)
            if firstPOS in ("ADJ", "ADP", "ADV", "CONJ", "DET", "INTJ", "PART", "PRON", "SCONJ", "X"):
                return []
        else: # no filtering
            return "ANY"
        