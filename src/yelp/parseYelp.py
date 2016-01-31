import gzip
from _collections import defaultdict
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.Meta import Meta
try:
    import ujson as json
except:
    import json

class YelpParser():
    def __init__(self):
        self.firstNames = defaultdict(int)
        self.locations = set()
        self.locationRows = []
    
    def writeDatabase(self, outPath):
        meta = Meta(outPath, clear=True)
        meta.insert_many("location", self.locationRows, True)
        names = [{"name":key, "lower":key.lower(), "total":self.firstNames[key]} for key in sorted(self.firstNames)]
        meta.insert_many("first_name", names, True)
    
    def processLine(self, data):
        itemType = data["type"]
        if itemType == "user":
            name = data["name"].split()[0]
            self.firstNames[name] += 1
        elif itemType == "business":
            name = data["name"]
            categories = data["categories"]
            for i in range(len(categories)):
                category = categories[-i - 1]
                combined = name + "_" + category
                if combined not in self.locations:
                    self.locationRows.append({"name":name, "lower":name.lower(), "level":i, "category":category})
                    self.locations.add(combined)
            schools = data["schools"]
            for school in schools:
                if school not in self.locations:
                    self.locationRows.append({"name":school, "lower":school.lower(), "level":0, "category":"school"})
                    self.locations.add(school)
            neighborhoods = data["neighborhoods"]
            for nb in neighborhoods:
                if nb not in self.locations:
                    self.locationRows.append({"name":nb, "lower":nb.lower(), "level":0, "category":"neighborhood"})
                    self.locations.add(nb)           
            
    def parseYelp(self, inPath, outPath):
        f = gzip.open(inPath, "rt")
        lineNum = 0
        for line in f:
            if lineNum % 100000 == 0:
                print "Processing line", lineNum
            data = json.loads(line)
            self.processLine(data)
            lineNum += 1
        
        print "Read", len(self.firstNames), "unique first names."
        print "Read", len(self.locationRows), "location rows."
        if outPath:
            assert outPath != inPath
            self.writeDatabase(outPath)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-i', '--input', help='Yelp Academic Dataset', default=None)
    options = parser.parse_args()
    
    p = YelpParser()
    p.parseYelp(options.input, options.output)