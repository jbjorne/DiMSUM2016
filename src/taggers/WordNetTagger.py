from Tagger import Tagger
from nltk.corpus import wordnet

class WordNetTagger(Tagger):
    def __init__(self):
        super(WordNetTagger, self).__init__("WN", ["WordNet"])
        self.lexnames = wordnet._lexnames
        assert len(self.lexnames) > 0
    
    def getSuperSenses(self, lemma, tokens):
        lexnames = sorted(set([x.lexname() for x in wordnet.synsets(lemma)]))
        if "noun.Tops" in lexnames:
            lexnames.remove("noun.Tops")
            potential = "noun." + lemma
            if potential in self.lexnames:
                lexnames.append(potential)
        lexnames = [x.replace("noun.", "n.").replace("verb.", "v.") for x in lexnames if x.startswith("noun.") or x.startswith("verb.")]
        return lexnames
    
    def filterByPOS(self, lexnames, tokens):
        pos = tokens[0]["POS"]
        if pos in ("NOUN", "PROPN"):
            keep = "n."
        elif pos in ("VERB"):
            keep = "v."
        else: # no filtering
            return lexnames
        return [x for x in lexnames if x.startswith(keep)]
    
    def tag(self, tokens):
        for key, useLowerCase in [("lemma", False), ("word", True)]:
            text = "_".join([x[key] for x in tokens])
            if useLowerCase:
                text = text.lower()
            supersenses = self.getSuperSenses(text)
            if len(supersenses) > 0:
                return supersenses
        return None
        