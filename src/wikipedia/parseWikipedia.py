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
        pass
    
    def checkTags(self, line, tag):
        openTag = "<" + tag + ">"
        closeTag = "</" + tag + ">"
        if line.startswith(openTag) and line.endswith(closeTag):
            return line[len(openTag):-len(closeTag)]
        else:
            return None
    
    def processLine(self, line):
        line = line.strip()
        title = None
        redirect = None
        categories = []
        infobox = None
        if line.startswith("<"):
            newTitle = self.checkTags(line, "title")
            if newTitle:
                print newTitle, title
                if title != None:
                    item = {"t":title, "r":redirect, "i":infobox, "c":categories}
                    print item
                    if self.outFile:
                        self.outFile.write(json.dumps(item))
                title = newTitle
                redirect = None
                categories = []
                infobox = None
            else:
                newRedirect = self.checkTags(line, "redirect title")
                if newRedirect:
                    redirect = newRedirect
        elif line.startswith("{{Infobox"):
            infobox = line[9:].strip()
        elif line.startswith("[[Category:"):
            categories.append(line[11:].strip())
            
    def parseWikipedia(self, inPath, outPath):
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
        for line in f:
            if lineNum % 100000 == 0:
                print "Processing line", lineNum
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
    parser.add_argument('-i', '--input', help='Yelp Academic Dataset', default=None)
    options = parser.parse_args()
    
    p = WikipediaParser()
    p.parseWikipedia(options.input, options.output)