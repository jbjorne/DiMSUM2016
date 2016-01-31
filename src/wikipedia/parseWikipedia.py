import sys, os
import bz2file
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class WikipediaParser():
    def __init__(self):
        pass
    
    def checkTags(self, line, tag):
        return line.startswith("<" + tag + ">") and line.endswith("</" + tag + ">")
    
    def processLine(self, line):
        line = line.strip()
        if line.startswith("<"):
            if line.startswith("title"):
                print line
            elif line.startswith("redirect title"):
                print line
            
    def parseWikipedia(self, inPath, outPath):
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