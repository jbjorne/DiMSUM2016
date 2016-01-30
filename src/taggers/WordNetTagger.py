from Tagger import Tagger
from nltk.corpus import wordnet
from POSFilter import POSFilter

class WordNetTagger(Tagger):
    def __init__(self):
        super(WordNetTagger, self).__init__("WN", ["WordNet"])
        self.lexnames = wordnet._lexnames
        self.posFilter = POSFilter()
        assert len(self.lexnames) > 0
    
    def getSuperSenses(self, lemma, tokens):
        lexnames = sorted(set([x.lexname() for x in wordnet.synsets(lemma)]))
        if "noun.Tops" in lexnames:
            lexnames.remove("noun.Tops")
            potential = "noun." + lemma
            if potential in self.lexnames:
                lexnames.append(potential)
        lexnames = [x.replace("noun.", "n.").replace("verb.", "v.") for x in lexnames if x.startswith("noun.") or x.startswith("verb.")]
        if len(lexnames) > 0:
            keep = self.posFilter.filterByPOS(tokens)
            if keep != "*":
                lexnames = [x for x in lexnames if x[0:2] in keep]
        return lexnames
    
    def filterByPOS(self, lexnames, tokens):
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
            return lexnames
        return [x for x in lexnames if x[0:2] in keep]
    
    def tag(self, tokens):
        for key, useLowerCase in [("lemma", False), ("word", True)]:
            text = "_".join([x[key] for x in tokens])
            if useLowerCase:
                text = text.lower()
            supersenses = self.getSuperSenses(text, tokens)
            if len(supersenses) > 0:
                return supersenses
        return None
        