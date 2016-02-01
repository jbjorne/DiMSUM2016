import codecs
try:
    import ujson as json
except:
    import json

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
            for word in ("wiki", "dispute", "article"):
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
        if categories[0] == "births":
            supersenses.append("noun.person")
        for cat in categories:
            cat = cat.lower()
            if cat in ("given names", "surnames"):
                supersenses.append("noun.person")
            elif "album" in cat:
                supersenses.extend([u'noun.communication', u'noun.artifact'])
            elif "game" in cat:
                supersenses.extend(["noun.communication", "noun.act"])
            elif cat.endswith("companies"):
                supersenses.append("noun.group")
        #for cat in categories:
        #    if cat.lower
        if len(supersenses) > 0:
            categories = None
            supersenses = sorted(set(supersenses))
        print item["t"], categories, supersenses
        
        

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-i', '--input', help='', default=None)
    options = parser.parse_args()
    
    process(options.input, options.output)