import csv

def readData(inPath):
    columns = ["index", "word", "lemma", "POS", "MWE", "parent", "strength", "supersense", "sentence"]
    with open(inPath) as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=columns,  delimiter="\t")
        for row in reader:
            print row
            
readData("../data/dimsum-data-1.5/dimsum16.train")