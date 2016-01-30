from Tagger import Tagger
from nltk.corpus import wordnet

class WordNetTagger(Tagger):
    def __init__(self):
        super(WordNetTagger, self).__init__("WN", ["WordNet"])
        self.lexnames = wordnet._lexnames
        self.nounPOS = set(["NOUN", "PROPN"])
        self.verbPOS = set(["VERB"])
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
        firstPOS = tokens[0]["POS"]
        lastPOS = tokens[0]["POS"]
        noun
        if pos in ("NOUN", "PROPN"):
            keep = ("n.",)
        elif firstPOS in self.verbPOS:
            keep = "v." if lastPOS not in self.nounPOS else ".n"
        else: # no filtering
            return lexnames
        return [x for x in lexnames if x[0:2] not in keep]
    
    def tag(self, tokens):
        for key, useLowerCase in [("lemma", False), ("word", True)]:
            text = "_".join([x[key] for x in tokens])
            if useLowerCase:
                text = text.lower()
            supersenses = self.getSuperSenses(text)
            if len(supersenses) > 0:
                return supersenses
        return None
        