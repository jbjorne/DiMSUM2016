from collections import OrderedDict

class Resources:
    __resources = None
    
    def __init__(self):
        if Resources.__resources == None:
            self.__initResources()
    
    def __initResources(self):
        Resources.__resources = OrderedDict()
        # Group 1
        self.__add(1, "corpus", "labeled training data", "v. 1.5")
        self.__add(1, "WordNet", "English WordNet")
        self.__add(1, "ARK", "ARK TweetNLP clusters")
        self.__add(1, "yelpac", "clusters: yelpac-c1000-m25.gz")
        # Group 2
        self.__add(2, "Yelp", "Yelp Academic Dataset (other than for the above clusters)")
        # Group 3
        self.__add(3, "Wikipedia", "English Wikipedia")
    
    def validate(self, keys):
        for key in keys:
            if key not in self.__resources:
                raise Exception("Unknown resource key '" + str(key) + "'")
        return keys
        
    def __add(self, level, key, name, details=None):
        assert level in (1, 2, 3)
        assert key not in Resources.__resources
        Resources.__resources[key] = {"level":level, "name":name, "details":details}
    
    def __addToReport(self, used, level, report):
        assert level in (1, 2, 3)
        report += "GROUP " + level * "I" + ",,\n"
        for key in Resources.__resources:
            resource = self.__resources[key]
            if resource["level"] == level:
                s = resource["name"] + ","
                s += ("Y" if key in used else "N") + ","
                if resource["details"]:
                    s += resource["details"]
                s += "\n"
                report += s
        report += ",,\n"
        return report
    
    def buildReport(self, used):
        if "corpus" not in used: # The labeled training data is always used for classification
            used = used + ["corpus"]
        
        report = "Resource,Used?,Details if used\n"
        report += ",,\n"
        for level in (1,2,3):
            report = self.__addToReport(used, level, report)
        report += "\"RULES: If you put Y for any resource in Group III, the system will be counted under the Open condition.\",,\n"
        report += "\"Otherwise, if you put Y for the resource in Group II, the system will be counted under the Semi-supervised Closed condition.\",,\n"
        report += "\"Otherwise, the system will be counted under the Supervised Closed condition.\",,"
        return report