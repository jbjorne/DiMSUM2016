from Tagger import Tagger

class OutOfVocabularyTagger(Tagger):
    def __init__(self):
        super(OutOfVocabularyTagger, self).__init__("OoV", ["corpus"])
    
    def tag(self, tokens):
        if len(tokens) == 1:
            token = tokens[0]
            if token["word"] == "@USER":
                return ["n.person"]
        return None
        