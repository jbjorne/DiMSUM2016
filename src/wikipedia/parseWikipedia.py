import sys, os
import bz2file
import codecs
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class WikipediaParser():
    def __init__(self):
        pass
    
    def checkTags(self, line, tag):
        openTag = "<" + tag + ">"
        closeTag = "</" + tag + ">"
        if line.startswith("<" + tag + ">") and line.endswith("</" + tag + ">"):
            return line[len]
    
    def processLine(self, line):
        line = line.strip()
        title = None
        if line.startswith("<"):
            if self.checkTags(line, "title"):
                print line
            elif self.checkTags(line, "redirect title"):
                print line
        elif line.startswith("{{Infobox"):
            print line
        elif line.startswith("[[Category:"):
            print line
            
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