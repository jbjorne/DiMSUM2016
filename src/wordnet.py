import sys, os
import dataset

def openDB(dbPath, clear=False):
    if clear and os.path.exists(dbPath):
        os.remove(dbPath)
    dbPath = "sqlite:///" + os.path.abspath(dbPath)
    print "Opening DB at", dbPath, "(clear:" + str(clear) + ")"
    return dataset.connect(dbPath)

wordnetDB = openDB(os.path.expanduser("~/data/WikiNames/wordnet-sqlite-31.db"))

def loadSenses():
    words = {}
    synsetWords = {}
    print "Loading words...",
    keys = []
    query = "SELECT wordid,lemma,pos,sensekey,synsetid,definition FROM wordsxsensesxsynsets"
    for row in wordnetDB.query(query):
        lemma = row["lemma"]
        if lemma not in words:
            words[lemma] = []
        words[lemma].append(row)
        keys.append(lemma)
        synsetid = row["synsetid"]
        if synsetid not in synsetWords:
            synsetWords[synsetid] = lemma
    for word in keys:
        tokens = word.split()
        for i in range(1, len(tokens)):
            substring = " ".join(tokens[:i])
            if substring not in words:
                words[substring] = [{"definition":"sub"}]
    print "done"
    return words, synsetWords

def loadHypernyms():
    print "Loading hypernyms...",
    hypernyms = {}
    query = "SELECT * FROM semlinks WHERE linkid == 1 or linkid == 3"
    for row in wordnetDB.query(query):
        synset1id = row["synset1id"]
        if synset1id not in hypernyms:
            hypernyms[synset1id] = []
        hypernyms[synset1id].append(row["synset2id"])
    print "done"
    return hypernyms

def mapId(word):
    matches = words.get(word)
    if matches:
        for match in matches:
            if "hypernyms" not in match and "synsetid" in match:
                match["hypernyms"] = getHypernyms(match["synsetid"])
        return matches
    return None

def getHypernyms(synsetid, level=0, maxlevel=5):
    chains = []
    if level < maxlevel:
        for hypernym in hypernyms.get(synsetid, []):
            parents = (synsetWords[hypernym], getHypernyms(hypernym, level=level+1))
            if len(parents[1]) == 0:
                parents = parents[0]
            chains.append(parents)
    return chains

def match(text):
    rows = wordnetDB.query("""
        SELECT words.wordid,words.lemma,sensekey,synsets.synsetid,definition 
        FROM words, senses, synsets
        WHERE words.wordid = senses.wordid AND senses.synsetid = synsets.synsetid
        AND words.lemma = '%s';""" % text)
    return rows

# Initialization

words, synsetWords = loadSenses()
hypernyms = loadHypernyms()