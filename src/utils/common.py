from collections import OrderedDict
def splitOptions(optionString, allowedValues=None, delimiter=","):
    actions = [x.strip() for x in optionString.split(delimiter)]
    if allowedValues:
        for action in actions:
            assert action in allowedValues
    return actions

def getOptions(string):
    d = OrderedDict()
    if string and len(string) > 0:
        for pair in string.split(";"):
            key, value = pair.split("=", 1)
            value = eval(value)
            d[key] = value
    return d