import codecs
try:
    import ujson as json
except:
    import json
from nltk.corpus import wordnet

def getSuperSenses(text):
    try:
        lexnames = sorted(set([x.lexname() for x in wordnet.synsets(text)]))
    except:
        print "Warning, exception on text", text
        lexnames = []
    if "noun.Tops" in lexnames:
        lexnames.remove("noun.Tops")
        potential = "noun." + text
        lexnames.append(potential)
    lexnames = sorted(set(lexnames))
    return lexnames
    
def process(inPath, outPath):
    f = codecs.open(inPath, "rt", "utf-8")
    data = json.loads(f.read(), "utf-8")
    f.close()
    outItems = []
    for item in data:
        if item["e"]:
            continue
        categories = []
        supersenses = []
        for cat in item["c"]:
            skip = False
            for word in ("wiki", 
                         "dispute", 
                         "article", 
                         " dmy ",
                         " mdy ",
                         "vague",
                         "ambiguous", 
                         "error", 
                         "pages", 
                         "infobox", 
                         "stubs", 
                         "template",
                         "user groups"):
                if word in cat.lower():
                    skip = True
                    break
            for word in (" in ", " of "):
                if word in cat:
                    cat = cat.split(word)[0]
            if cat.split()[0].isdigit():
                cat = " ".join(cat.split()[1:])
            if not skip:
                categories.append(cat)
        categories = sorted(set(categories))
        item["c"] = categories
        
        for cat in categories:
            cat = cat.lower()
            if cat == "births" or cat.endswith("people"):
                supersenses.append("noun.person")
            elif "establish" in cat:
                supersenses += ["noun.group", "noun.communication"]
            elif cat in ("given names", "surnames") or "names" in cat:
                supersenses.append("noun.person")
            elif "album" in cat:
                supersenses.extend([u'noun.communication', u'noun.artifact'])
            elif "game" in cat:
                supersenses.extend(["noun.communication", "noun.act"])
            elif cat.endswith("companies"):
                supersenses.append("noun.group")
            elif "cuisine" in cat:
                supersenses.append("noun.food")
            elif "television" in cat:
                supersenses.append("noun.communication")
            elif "song" in cat:
                supersenses.append("noun.communication")
            elif "comics" in cat:
                supersenses.append("noun.communication")
            elif "even" in cat:
                supersenses.append("noun.event")
        #for cat in categories:
        #    if cat.lower
        if len(supersenses) > 0:
            del item["c"]
            categories = None
        else:
            for cat in categories:
                splits = cat.split()
                catsenses = []
                for i in range(len(splits)):
                    substring = " ".join(splits[i:])
                    catsenses = getSuperSenses(substring)
                    if catsenses:
                        #print "SUB", substring, catsenses
                        break
                supersenses += catsenses
        supersenses = sorted(set(supersenses))
        supersenses = [x.replace("noun.", "n.").replace("verb.", "v.") for x in supersenses if x.startswith("noun.") or x.startswith("verb.")]
        item["s"] = supersenses
        #del item["c"]
        print item["t"], categories, supersenses
        outItems.append(item)
    
    if outPath:
        f = codecs.open(outPath, "wt", "utf-8")
        f.write(json.dumps(outItems, indent=4))
        f.close()
        

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-i', '--input', help='', default=None)
    options = parser.parse_args()
    
    process(options.input, options.output)