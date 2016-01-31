import os
import inspect
from experiments import *
from src.experiments.CountMWE import CountMWE
from src.experiments.CountPOS import CountPOS
from src.Classification import Classification
import src.utils.Stream as Stream
from src.utils.common import splitOptions, getOptions

DATA_PATH = os.path.expanduser("data")

def getFeatureGroups(names, dummy=False):
    global DATA_PATH
    groups = [eval(x) if isinstance(x, basestring) else x for x in names]
    for i in range(len(groups)): # Initialize classes
        if inspect.isclass(groups[i]):
            groups[i] = groups[i]()
        groups[i].initialize(DATA_PATH)
    return groups

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run University of Turku experiments for CAMDA 2015')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    #parser.add_argument('-d', "--debug", default=False, action="store_true", dest="debug")
    parser.add_argument('-a', "--action", default="build,classify,analyse", dest="action")
    groupE = parser.add_argument_group('build', 'Example Generation')
    #groupE.add_argument('-e', "--examples", default=False, action="store_true", dest="examples")
    groupE.add_argument('-e', '--experiment', help='Experiment class', default="RemissionMutTest")
    groupE.add_argument('-f', '--features', help='Feature groups (comma-separated list)', default=None)
    groupE.add_argument('-x', '--extra', default=None)
    groupC = parser.add_argument_group('classify', 'Example Classification')
    groupC.add_argument('-s', '--classification', help='', default="Classification")
    groupC.add_argument('-c','--classifier', help='', default=None)
    groupC.add_argument('-r','--classifierArguments', help='', default=None)
    groupC.add_argument('-m','--metric', help='', default="roc_auc")
    #groupC.add_argument('-i','--iteratorCV', help='', default='getStratifiedKFoldCV')
    groupC.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=10)
    groupC.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=4)
    groupC.add_argument('-l', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    groupC.add_argument("--hidden", default=False, action="store_true", dest="hidden")
    groupC.add_argument('--preDispatch', help='', default='2*n_jobs')
    groupA = parser.add_argument_group('Analysis', 'Analysis for classified data')
    groupA.add_argument("-y", "--analyses", default="ResultAnalysis")
    options = parser.parse_args()
    
    actions = splitOptions(options.action, ["build", "classify", "analyse"])
    Stream.openLog(os.path.join(options.output, "log.txt"), clear = "build" in actions)
    print "Options:", options.__dict__
    
    if "build" in actions:
        print "======================================================"
        print "Building Examples"
        print "======================================================"
        ExperimentClass = eval(options.experiment)
        if options.extra:
            e = ExperimentClass(**getOptions(options.extra))
        else:
            e = ExperimentClass()
        e.dataPath = DATA_PATH
        e.includeSets = ("train", "test") if options.hidden else ("train",)
        featureGroups = (e.featureGroups if e.featureGroups != None else []) + (options.features.split(",") if options.features else [])
        print "Using feature groups:", featureGroups
        e.featureGroups = getFeatureGroups(featureGroups)
        taggers = e.taggers
        print "Using taggers:", taggers
        e.taggers = getFeatureGroups(taggers)
        e.run(options.output)
        e = None
    
    resultPath = os.path.join(options.output, "classification.json")
    if "classify" in actions:
        print "======================================================"
        print "Classifying"
        print "======================================================"
        ClassificationClass = eval(options.classification)
        classification = ClassificationClass(options.classifier, options.classifierArguments, options.numFolds, options.parallel, options.metric, classifyHidden=options.hidden)
        classification.readExamples(options.output)
        classification.classify()
        classification = None
    
    if "analyse" in actions and options.analyses is not None:
        for analysisName in options.analyses.split(","):
            print "======================================================"
            print "Analysing", analysisName
            print "======================================================"
            exec "from src.analyse." + analysisName + " import " + analysisName
            analysisClass = eval(analysisName)
            analysisObj = analysisClass(dataPath=DATA_PATH)
            analysisObj.analyse(options.output, hidden=options.hidden)