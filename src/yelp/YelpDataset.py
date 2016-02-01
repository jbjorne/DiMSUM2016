import os
from src.Meta import Meta

YELP_DATASET = None

def getYelpDataset(dataPath):
    global YELP_DATASET
    if YELP_DATASET == None:
        YELP_DATASET = YelpDataset(dataPath)
    return YELP_DATASET

class YelpDataset():
    def __init__(self, dataPath):
        self.dataPath = dataPath

        dbPath = os.path.join(dataPath, "yelp", "yelp.sqlite")
        if not os.path.exists(dbPath):
            raise Exception("No Yelp database at " + dbPath)
        self.meta = Meta(dbPath)
        
        self.parts = {"middle":{}, "first":{}, "last":{}, "single":{}}
        for row in self.meta.db.query("select * from part where total > 10;"):
            pos = row["position"]
            text = row["token"]
            if text not in self.parts[pos]:
                self.parts[pos][text] = []
            self.parts[pos][text].append(row["category"])
        
        self.locations = {}
        for row in self.meta.db["location"].all():
            name = row["lower"]
            if row["lower"] not in self.locations:
                self.locations[name] = []
            self.locations[name].append(row)
        
        self.names = set([x["lower"] for x in self.meta.db.query("select * from first_name where total > 10;")])
        for name in ("the",):
            self.names.remove(name)
    