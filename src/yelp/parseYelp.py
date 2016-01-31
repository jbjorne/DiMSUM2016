import gzip
try:
    import ujson as json
except:
    import json

def parseYelp(inPath, outPath):
    f = gzip.open(inPath, "rt")
    lineNum = 1
    for line in f:
        if lineNum % 1000 == 0:
            print "Processing line", lineNum
        data = json.loads(line)
        lineNum += 1

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-i', '--input', help='Yelp Academic Dataset', default=None)
    options = parser.parse_args()
    
    parseYelp(options.input, options.output)