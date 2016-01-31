from Tagger import Tagger

class OutOfVocabularyTagger(Tagger):
    def __init__(self):
        super(OutOfVocabularyTagger, self).__init__("OoV", ["corpus"])
    
    def tag(self, tokens, sentence, taggingState):
        supersenses = []
        if len(tokens) == 1:
            token = tokens[0]
            if token["word"].startswith("@"):
                supersenses.append("n.person")
            elif token["word"].startswith("'") and token["POS"] == "VERB":
                supersenses.append("v.stative")
            elif token["lemma"] in ("place", "restaurant", "store"):
                supersenses.append("n.group")
            elif token["lemma"] in ("place", "restaurant", "store", "hotel", "places", "shop", "guys", "salon"):
                supersenses.append("n.group")
        supersenses = self.filterByPOS(tokens, supersenses, taggingState)
        return supersenses #(None if len(supersenses) == 0 else supersenses)
        