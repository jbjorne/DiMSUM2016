from Tagger import Tagger
from nltk.corpus import wordnet

class WordNetTagger(Tagger):
    def __init__(self):
        super(WordNetTagger, self).__init__("WN", ["WordNet"])
        self.lexnames = wordnet._lexnames
        assert len(self.lexnames) > 0
    
    def getSuperSenses(self, lemma, tokens, taggingState):
        lexnames = sorted(set([x.lexname() for x in wordnet.synsets(lemma)]))
        if "noun.Tops" in lexnames:
            lexnames.remove("noun.Tops")
            potential = "noun." + lemma
            if potential in self.lexnames:
                lexnames.append(potential)
        lexnames = [x.replace("noun.", "n.").replace("verb.", "v.") for x in lexnames if x.startswith("noun.") or x.startswith("verb.")]
        lexnames = self.filterByPOS(tokens, lexnames, taggingState)
        return lexnames
    
    def tag(self, tokens, sentence, taggingState):
        for key, useLowerCase in [("lemma", False), ("word", True)]:
            text = "_".join([x[key] for x in tokens])
            if useLowerCase:
                text = text.lower()
            supersenses = self.getSuperSenses(text, tokens, taggingState)
            if len(supersenses) > 0:
                return supersenses
        return []
        