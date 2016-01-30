from collections import OrderedDict

class Resources:
    def __init__(self):
        self.__resources = OrderedDict()
        # Group 1
        self.__add(1, "labeled training data", "v. 1.5")
        self.__add(1, "English WordNet")
        self.__add(1, "ARK TweetNLP clusters")
        self.__add(1, "clusters: yelpac-c1000-m25.gz")
        # Group 2
        self.__add(2, "Yelp Academic Dataset (other than for the above clusters)")
        # Group 3
        
    def __add(self, level, name, details=None):
        assert level in (1, 2, 3)
        assert name not in self.__resources
        self.__resources[name] = {"level":level, "name":name, "details":details}
    
    def __addToReport(self, used, level, report):
        assert level in (1, 2, 3)
        for name in self.__resources:
            resource = self.__resources[name]
            if resource["level"] == level:
                s = resource["name"] + ","
                s += ("Y" if resource["name"] in used else "N") + ","
                if resource["details"]:
                    s += resource["details"]
                s += "\n"
                report += s
        report += ",,"
        return report
    
    def buildReport(self, used):
        report = "Resource,Used?,Details if used\n"
        report += ",,"
        report += "GROUP I,,"
        for name in self.__resources:
            if