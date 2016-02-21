if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-i', '--input', help='Yelp Academic Dataset', default=None)
    options = parser.parse_args()
    
    p = YelpParser()
    p.parseYelp(options.input, options.output)