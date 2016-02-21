import gzip
from _collections import defaultdict
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.Database import Database
try:
    import ujson as json
except:
    import json

class YelpParser():
    def __init__(self):
        self.firstNames = defaultdict(int)
        self.skippedNames = defaultdict(int)
        self.locations = set()
        self.locationRows = []
    
    def writeDatabase(self, outPath):
        db = Database(outPath, clear=True)
        db.insert_many("location", self.locationRows, True)
        self.addLocationParts(db)
        #names = [name.lstrip(".,'-_") for name in self.firstNames]
        names = [{"name":key, "lower":key.lower(), "length":len(key), "total":self.firstNames[key]} for key in sorted(self.firstNames)]
        db.insert_many("first_name", names, True)
        print "Indexing"
        for column in ("name", "lower", "level"):
            db.db["location"].create_index([column])
        for column in ("name", "lower", "length"):
            db.db["first_name"].create_index([column])
    
    def addLocationParts(self, db):
        counts = defaultdict(int)
        for location in self.locationRows:
            parts = location["lower"].split()
            if len(parts) == 0:
                counts[(parts[0], "single", location["category"])] += 1
            else:
                counts[(parts[0], "first", location["category"])] += 1
                counts[(parts[-1], "last", location["category"])] += 1
                for i in range(1, len(parts) - 1):
                    counts[(parts[i], "middle", location["category"])] += 1
        rows = []
        for key in sorted(counts.keys()):
            rows.append({"token":key[0], "position":key[1], "category":key[2], "total":counts[key]})
        db.insert_many("part", rows, True)
        
    def processLine(self, data):
        itemType = data["type"]
        if itemType == "user":
            name = data["name"].split()[0]
            name = name.lstrip(".,'-_")
            self.firstNames[name] += 1
            #if len(name) > 2 or (len(name) == 2 and name[0].isupper() and name[1].islower()):
            #    self.firstNames[name] += 1
            #else:
            #    self.skippedNames[name] += 1
        elif itemType == "business":
            name = data["name"]
            categories = data["categories"]
            for i in range(len(categories)):
                category = categories[-i - 1]
                combined = name + "_" + category
                if combined not in self.locations:
                    self.locationRows.append({"type":"business", "name":name, "lower":name.lower(), "level":i, "category":category})
                    self.locations.add(combined)
            schools = data["schools"]
            for school in schools:
                if school not in self.locations:
                    self.locationRows.append({"type":"school", "name":school, "lower":school.lower(), "level":0, "category":"school"})
                    self.locations.add(school)
            neighborhoods = data["neighborhoods"]
            for nb in neighborhoods:
                if nb not in self.locations:
                    self.locationRows.append({"type":"neighborhood", "name":nb, "lower":nb.lower(), "level":0, "category":"neighborhood"})
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
        print "Skipped", dict(self.skippedNames)
        if outPath:
            assert outPath != inPath
            self.writeDatabase(outPath)