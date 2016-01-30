from Tagger import Tagger

class OutOfVocabularyTagger(Tagger):
    def __init__(self):
        super(OutOfVocabularyTagger, self).__init__("OoV", ["corpus"])
    
    def tag(self, tokens):
        supersenses = []
        if len(tokens) == 1:
            token = tokens[0]
            if token["word"].startswith("@"):
                supersenses.append("n.person")
            if token["word"].startswith("'") and token["POS"] == "VERB":
                supersenses.append("v.stative")
        return (None if len(supersenses) == 0 else supersenses)
        