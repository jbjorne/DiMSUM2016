import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ExampleIO():
    def __init__(self, fileStem, makeDirs=True):
        self.featureFilePath = fileStem + ".X"
        self.labelFilePath = fileStem + ".y"
        self.makeDirs = makeDirs
        # The files
        self.featureFile = None
        self.labelFile = None
    
    def writeExample(self, classId, features):
        raise NotImplementedError
    
    def newFiles(self):
        if self.featureFilePath != None:
            self.featureFile = self._newFile(self.featureFilePath, "wt")
        if self.labelFilePath != None and self.labelFilePath != self.featureFilePath:
            self.labelFile = self._newFile(self.labelFilePath, "wt")
    
    def closeFiles(self):
        if self.featureFile:
            self.featureFile.close()
            self.featureFile = None
        if self.labelFile:
            self.labelFile.close()
            self.labelFile = None
    
    def _newFile(self, filePath, mode):
        if os.path.exists(filePath):
            os.remove(filePath)
        if not os.path.exists(os.path.dirname(filePath)):
            os.makedirs(os.path.dirname(filePath))
        return open(filePath, mode)
    
    def readFiles(self, readFeatures=None):
        if self.labelFilePath == None or self.featureFilePath == self.labelFilePath or not os.path.exists(self.labelFilePath):
            from sklearn.datasets import load_svmlight_file
            print "Loading SVM-light features and labels from", self.featureFilePath
            if readFeatures != None:
                raise Exception("readFeatures is not supported with the SVM-light format")
            X, y = load_svmlight_file(self.featureFilePath)
        else:
            import numpy
            print "Loading numpy txt labels from", self.labelFilePath
            y = numpy.loadtxt(self.labelFilePath)
            print "Loading numpy txt features from", self.featureFilePath
            X = numpy.loadtxt(self.featureFilePath, usecols=readFeatures)
        return X, y

###############################################################################
# Concrete Writers
###############################################################################

class SVMLightExampleIO(ExampleIO):
    def __init__(self, fileStem, makeDirs=True):
        ExampleIO.__init__(self, fileStem, makeDirs)
        self.featureFilePath = fileStem + ".yX"
        self.labelFilePath = None
    
    def writeExample(self, classId, features):
        self.featureFile.write(str(classId) + " " + " ".join([str(key) + ":" + str(features[key]) for key in sorted(features.keys())]) + "\n")

class NumpyExampleIO(ExampleIO):
    def __init__(self, fileStem, makeDirs=True, singleFile=False):
        ExampleIO.__init__(self, fileStem, makeDirs)
        if singleFile:
            self.labelFilePath = self.featureFilePath = fileStem + ".yX"
        self.numExamples = 0
    
    def newFiles(self):
        super(NumpyExampleIO, self).newFiles()
        self.numExamples = 0
    
    def writeExample(self, classId, features):
        self.numExamples += 1
        if self.labelFile != None: # write class
            self.labelFile.write(str(classId))
            if self.labelFile != self.featureFile: # classes go to a separate file
                self.labelFile.write("\n")
            else: # classes go to the same file
                self.labelFile.write(" ")
        if self.featureFile != None: # write features
            index = 0
            line = ""
            for key in sorted(features.keys()):
                while index < key:
                    line += "0 "
                    index += 1
                line += str(features[key]) + " "
                index = key + 1
            self.featureFile.write(line[:-1] + "\n") # remove trailing space before writing the line
        
    def closeFiles(self):
        super(SVMLightExampleIO, self).closeFiles()
        self._padNumpyFeatureFile(self.featureFilePath, self.numFeatures)
    
    def _padNumpyFeatureFile(self, filename, numFeatures):
        filename = os.path.abspath(os.path.expanduser(filename))
        temp = filename + "-tempfile"
        os.rename(filename, temp)
        fI = open(temp, "rt")
        fO = open(filename, "wt")
        for line in fI:
            line = line.strip()
            if line == "":
                line = " 0" * numFeatures
            else:
                line = line + ((numFeatures - line.count(" ") - 1) * " 0")
            line = line.strip()
            fO.write(line + "\n")
        fI.close()
        fO.close()
        os.remove(temp)

