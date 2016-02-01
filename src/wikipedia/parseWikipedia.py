import sys, os
import bz2file
import codecs
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    import ujson as json
except:
    import json

class WikipediaParser():
    def __init__(self):
        self.title = None
        self.redirect = None
        self.categories = []
        self.infobox = None
        self.verbose = False
        self.numTitles = 0
        
        self.limit = None
        self.skip = False
    
    def checkTags(self, line, tag):
        openTag = "<" + tag + ">"
        closeTag = "</" + tag + ">"
        if line.startswith(openTag) and line.endswith(closeTag):
            return line[len(openTag):-len(closeTag)]
        else:
            return None
    
    def processLine(self, line):
        line = line.strip()
        if line.startswith("<"):
            newTitle = self.checkTags(line, "title")
            if self.limit and newTitle not in self.limit:
                skip = True
            else:
                skip = False
            
            if newTitle:
                self.numTitles += 1
                if self.title != None:
                    disambiguation = None
                    if self.title.endswith(")") and "(" in self.title:
                        self.title, disambiguation = self.title.rsplit("(", 1)
                        self.title = self.title.strip()
                        disambiguation = disambiguation.rstrip(" )")
                    if disambiguation == None or disambiguation != u"disambiguation":
                        if disambiguation != None and self.verbose:
                            print (self.title, disambiguation)
                        item = {"t":self.title, "d":disambiguation, "r":self.redirect, "i":self.infobox, "c":self.categories}
                        if self.outFile:
                            self.outFile.write(json.dumps(item))
                            self.outFile.write("\n")
                self.title = newTitle
                self.redirect = None
                self.categories = []
                self.infobox = None
            else:
                newRedirect = self.checkTags(line, "redirect title")
                if newRedirect:
                    self.redirect = newRedirect
        elif line.startswith("{{Infobox"):
            self.infobox = line[9:].strip()
        elif line.startswith("[[Category:"):
            line = line[11:-2]
            if "]]" in line:
                line = line.split("]]")[0]
            self.categories.append(line.strip("| "))
    
    def loadTitles(self, titlesPath):
        self.limit = set()
        if titlesPath:
            f = codecs.open(titlesPath, "rt", "utf-8")
            for line in f:
                line = line.strip("\"\n")
                print line
            self.limit.add(line)
            
    def parseWikipedia(self, inPath, outPath, titlesPath):
        assert inPath != outPath
        
        self.outFile = None
        if outPath:
            self.outFile = codecs.open(outPath, "wt", "utf-8")
        
        compressed = inPath.endswith(".bz2")
        originalFile = open(inPath, "r" if compressed else "rt")
        if inPath.endswith(".bz2"):
            f = bz2file.BZ2File(originalFile, mode="r")
        else:
            f = originalFile

        lineNum = 0
        c = codecs.iterdecode(f, "utf-8")
        for line in c:
            if lineNum % 100000 == 0:
                print "Processing line", lineNum, "title", self.numTitles, "=", self.title
            self.processLine(line)
            lineNum += 1
        
        originalFile.close()
        if self.outFile:
            self.outFile.close()
        
#         if outPath:
#             assert outPath != inPath
#             self.writeDatabase(outPath)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-i', '--input', help='', default=None)
    parser.add_argument('-t', '--titles', help='', default=None)
    options = parser.parse_args()
    
    p = WikipediaParser()
    p.parseWikipedia(options.input, options.output, options.titles)