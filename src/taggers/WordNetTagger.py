from Tagger import Tagger
from nltk.corpus import wordnet

class WordNetTagger(Tagger):
    def __init__(self, exact=True):
        name = "WN" if exact else "WNP"
        super(WordNetTagger, self).__init__(name, ["WordNet"])
        self.lexnames = wordnet._lexnames
#         self.extraSenses = {"n.time":["n.event"], 
#                             "n.group":["n.person"],
#                             "n.object":["n.location"],
#                             "n.artifact":["n.group"],
#                             "n.act":["n.group"],
#                             "n.location":["n.group"],
#                             "n.communication":["n.group"],
#                             "n.cognition":["n.group"],
#                             "n.state":["n.group"],
#                             "n.person":["n.group"],
#                             "v.change":["v.stative"],
#                             "v.possession":["n.group"],
#                             "v.communication":["n.group"]}
        assert len(self.lexnames) > 0
        self.exact = exact
    
    def getSuperSenses(self, lemma, tokens, taggingState):
        try:
            lexnames = sorted(set([x.lexname() for x in wordnet.synsets(lemma)]))
        except:
            print "Warning, exception on lemma", lemma
            lexnames = []
        if "noun.Tops" in lexnames:
            lexnames.remove("noun.Tops")
            potential = "noun." + lemma
            if potential in self.lexnames:
                lexnames.append(potential)
        lexnames = [x.replace("noun.", "n.").replace("verb.", "v.") for x in lexnames if x.startswith("noun.") or x.startswith("verb.")]
        lexnames = self.filterByPOS(tokens, lexnames, taggingState)
#         for lexname in lexnames[:]:
#             if lexname in self.extraSenses:
#                 lexnames += self.extraSenses[lexname]
        lexnames = sorted(set(lexnames))
        return lexnames
    
    def tag(self, tokens, sentence, taggingState):
        if self.exact:
            for key, useLowerCase in [("lemma", False), ("word", True)]:
                text = "_".join([x[key] for x in tokens])
                if useLowerCase:
                    text = text.lower()
                supersenses = self.getSuperSenses(text, tokens, taggingState)
                if len(supersenses) > 0:
                    return supersenses
        supersenses = []
        if not self.exact:
            supersenses = self.tagPartial(tokens, sentence, taggingState)
        return supersenses
    
    def tagPartial(self, tokens, sentence, taggingState):
        if len(tokens) <= 1:
            return []
        for token in tokens:
            if token["POS"] not in ("NOUN", "PROPN"):
                return []
        allUpper, leftUpper, rightUpper = self.getCapitalization(tokens, sentence)
        if allUpper and not leftUpper and not rightUpper:
            lastSense = self.getSuperSenses(tokens[-1]["lemma"], tokens, taggingState)
            if lastSense:
                #print "Match", [x["word"] for x in tokens], lastSense
                return lastSense
        return []
        