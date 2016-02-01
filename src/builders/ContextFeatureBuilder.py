from FeatureBuilder import FeatureBuilder

class ContextFeatureBuilder(FeatureBuilder):
    
    def __init__(self):
        super(ContextFeatureBuilder, self).__init__("Context")
    
    def getFlankingTokens(self, tokens, sentence):
        left = None
        right = None
        minIndex = tokens[0]["index"]
        maxIndex = tokens[-1]["index"]
        if minIndex > 0:
            left = sentence[minIndex - 1]
        if maxIndex < len(sentence) - 1:
            right = sentence[maxIndex + 1]
        return left, right
    
    def buildSpanFeatures(self):
        left, right = self.getFlankingTokens(self.tokens, self.sentence)
        supersensePOS = self.supersense.split(".")[0]
        pos = ":".join(x["POS"] for x in self.tokens)
        lemma = ":".join(x["lemma"] for x in self.tokens)
        for tag, token in ("LEFT", left), ("RIGHT", right):
            if token == None:
                self.build("TERMINAL_" + tag)
                continue
            for key in ("lemma", "POS"):
                value = token[key].lower()
                self.build(tag + "_" + key + "_" + value)
                #self.build(tag + "_" + key + "_" + value + ":" + lemma)
                self.build(tag + "_" + key + "_" + value + ":" + pos)
                self.build(tag + "_" + key + "_" + value + ":" + self.supersense)
                self.build(tag + "_" + key + "_" + value + ":" + supersensePOS)