from Tagger import Tagger
from nltk.corpus import wordnet

class WordNetTagger(Tagger):
    def __init__(self):
        super(WordNetTagger, self).__init__("WN", ["WordNet"])
    
    def getSuperSenses(self, lemma):
        lexnames = sorted(set([x.lexname() for x in wordnet.synsets(lemma)]))
        return [x.replace("noun.", "n.").replace("verb.", "v.") for x in lexnames if x.startswith("noun.") or x.startswith("verb.")]
    
    def tag(self, tokens):
        for key, useLowerCase in [("lemma", False), ("word", True)]:
            text = "_".join([x[key] for x in tokens])
            if useLowerCase:
                text = text.lower()
            supersenses = self.getSuperSenses(text)
            if len(supersenses) > 0:
                return supersenses
        return None
        