import wikipedia
import codecs
import json

def downloadPages(inPath, outPath):
    print "Loading page list"
    f = codecs.open(inPath, "rt", "utf-8")
    titles = []
    for line in f:
        line = line[1:-4]
        print line
        titles.append(line)
    
    outFile = None
    if outPath:
        outFile = codecs.open(outPath, "wt", "utf-8")
        outFile.write("[")
    
    for i in range(len(titles)):
        title = titles[i]
        print "Downloading page", i, "out of", len(titles), title
        try:
            page = wikipedia.page(title)
            item = {"t":title, "c":page.categories, "e":False}
            print item
            if outFile:
                outFile.write(json.dumps(item))
                if i < len(titles) - 1:
                    outFile.write(",")
                outFile.write("\n")
        except:
            print "ERROR", title
            item = {"t":title, "c":[], "e":True}
            print item
            if outFile:
                outFile.write(json.dumps(item))
                if i < len(titles) - 1:
                    outFile.write(",")
                outFile.write("\n")
    
    if outPath:
        outFile.write("]")
        outFile.close/()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-i', '--input', help='', default=None)
    options = parser.parse_args()
    
    downloadPages(options.input, options.output)