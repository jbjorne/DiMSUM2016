import os
from src.yelp.YelpParser import YelpParser

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i', '--input', help='Yelp Academic Dataset', default=None)
    parser.add_argument('-o', '--output', help='Output file (optional)', default=None)
    options = parser.parse_args()
    
    p = YelpParser()
    if options.output == None:
        options.output = "data/yelp/yelp.sqlite"
        outDir = os.path.dirname(options.output)
        if not os.path.exists(outDir):
            raise Exception("Output directory '" + outDir + "' not found")
    p.parseYelp(options.input, options.output)