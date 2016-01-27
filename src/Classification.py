import sys, os
from learn.evaluation import aucForPredictions, aucForProbabilites, getClassPredictions,\
    majorityBaseline
from learn.skext.DisjointStratifiedKFold import DisjointStratifiedKFold
from utils.common import getOptions
from learn.skext.metrics import balanced_accuracy_score
from sklearn.metrics.scorer import make_scorer
from learn.skext.BalancedIteratorCV import BalancedIteratorCV
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sklearn.cross_validation import StratifiedKFold
from skext.gridSearch import ExtendedGridSearchCV
from sklearn.metrics import classification_report
from collections import defaultdict, OrderedDict
from HiddenSet import splitData
from ExampleIO import SVMLightExampleIO
from Meta import Meta
import numpy as np

def importNamed(name):
    asName = name.rsplit(".", 1)[-1]
    imported = False
    attempts = ["from sklearn." + name.rsplit(".", 1)[0] + " import " + asName,
                "from " + name.rsplit(".", 1)[0] + " import " + asName,
                "import " + name + " as " + asName]
    for attempt in attempts:
        try:
            print "Importing '" + attempt + "', ",
            exec attempt
            imported = True
            print "OK"
            break;
        except ImportError:
            print "failed"
    if not imported:
        raise Exception("Could not import '" + name + "'")
    return eval(asName)

def countUnique(values):
    counts = defaultdict(int)
    for value in values:
        counts[value] += 1
    return dict(counts)

class Classification(object):
    def __init__(self, classifierName, classifierArgs, numFolds=10, parallel=1, metric='roc_auc', getCV=None, preDispatch='2*n_jobs', classifyHidden=False):
        # Data
        self.X = None
        self.y = None
        self.meta = None
        self.classes = None
        self.indices = None
        # Settings
        self.randomize = False
        self.numFolds = numFolds
        self.classifierName = classifierName
        self.classifierArgs = classifierArgs
        self.preDispatch = preDispatch
        self.metric = metric
        self.verbose = 3
        self.parallel = parallel
        self.classifyHidden = classifyHidden
        self.saveExtra = True
    
    def readExamples(self, inDir, fileStem=None, exampleIO=None, preserveTables=None):
        if fileStem == None:
            fileStem = "examples"
        # Read examples
        if exampleIO == None:
            exampleIO = SVMLightExampleIO(os.path.join(inDir, fileStem))
        self.X, self.y = exampleIO.readFiles()
        # Read metadata
        self.meta = Meta(os.path.join(inDir, fileStem + ".meta.sqlite"))
        self.groups = {row["id"]:row["project_code"] for row in self.meta.db.query("SELECT id, project_code FROM example")}
        self.classes = None
        if "class" in self.meta.db.tables:
            self.classes = [int(x["id"]) for x in self.meta.db["class"].all()]
        self._clearResults(preserveTables)
    
    def _clearResults(self, preserveTables):
        preserveTables = set(preserveTables if preserveTables else [])
        preserveTables = preserveTables.union(set(["class", "example", "experiment", "feature"]))
        for tableName in self.meta.db.tables:
            if tableName not in preserveTables:
                self.meta.drop(tableName)
    
    def _getClassifier(self):
        classifier = importNamed(self.classifierName)
        classifierArgs = getOptions(self.classifierArgs)
        print "Using classifier", classifier.__name__, "with arguments", classifierArgs
        return classifier, classifierArgs
    
    def _splitData(self, setNames=None):
        if self.classes:
            print "Class distribution = ", countUnique(self.y)
        if setNames == None:
            setNames = [x["set"] for x in self.meta.db["example"].all()]
        indices, X_train, X_hidden, y_train, y_hidden = splitData(self.X, self.y, setNames) #hidden.split(self.X, self.y, meta=self.meta.db["example"].all())
        print "Sizes", [X_train.shape[0], y_train.shape[0]], [X_hidden.shape[0], y_hidden.shape[0]]
        if self.classes:
            print "Classes y_train = ", countUnique(y_train)
            print "Classes y_hidden = ", countUnique(y_hidden)
            print "MCB(y_train) =", majorityBaseline(y_train, [self.groups[i] for i in indices["train"]], self.metric), "(" + self.metric + ")"
        return indices, X_train, X_hidden, y_train, y_hidden
                
    def classify(self):
        self.meta.dropTables(["result", "prediction", "importance"], 100000)
        self.indices, X_train, X_hidden, y_train, y_hidden = self._splitData()
        search = self._crossValidate(y_train, X_train, self.classifyHidden and (X_hidden.shape[0] > 0))
        if self.classifyHidden:
            self._predictHidden(y_hidden, X_hidden, search, y_train.shape[0])
        self.indices = None
        
    def _getResult(self, setName, classifier, cv, params, score=None, fold=None, mean_score=None, scores=None, extra=None):
        result = {"classifier":classifier.__name__, "cv":cv.__class__.__name__ if cv else None,
                  "params":str(params), "fold":fold, "score":score, "setName":setName}
        result["mean"] = float(mean_score) if mean_score is not None else None
        result["scores"] = ",".join([str(x) for x in list(scores)]) if mean_score is not None else None
        result["std"] = float(scores.std() / 2) if mean_score is not None else None
        if extra:
            result.update(extra)
        return result
    
    def _insert(self, tableName, rows):
        self.meta.insert_many(tableName, rows)
        
    def _crossValidate(self, y_train, X_train, refit=False):
        # Run the grid search
        print "Cross-validating for", self.numFolds, "folds"
        print "Args", self.classifierArgs
        cv = StratifiedKFold(y_train, n_folds=self.numFolds, shuffle=True, random_state=1) #self.getCV(y_train, self.meta.meta, numFolds=self.numFolds)
        #cv = BalancedIteratorCV(y_train, n_folds=self.numFolds, shuffle=True, random_state=1, examples=[x for x in self.meta.db.query("SELECT * from example WHERE [set] == 'train';")], groupBy="project_code")
        classifier, classifierArgs = self._getClassifier()
        metric = self.metric
        if metric == "bas":
            metric = make_scorer(balanced_accuracy_score)
        search = ExtendedGridSearchCV(classifier(), classifierArgs, refit=refit, cv=cv, 
                                      scoring=metric, verbose=self.verbose, n_jobs=self.parallel, 
                                      pre_dispatch=int(self.preDispatch) if self.preDispatch.isdigit() else self.preDispatch)
        search.fit(X_train, y_train)
        print "---------------------- Grid scores on development set --------------------------"
        results = []
        index = 0
        bestExtras = None
        bestScores = None
        for params, mean_score, scores in search.grid_scores_:
            print "Grid:", params
            results.append(self._getResult("train", classifier, cv, params, None, None, mean_score, scores, extra={"train_size":None, "test_size":None}))
            if bestScores == None or float(mean_score) > bestScores[1]:
                bestScores = (params, mean_score, scores)
                if hasattr(search, "extras_"):
                    bestExtras = search.extras_[index]
            for fold in range(len(scores)):
                result = self._getResult("train", classifier, cv, params, scores[fold], fold)
                if hasattr(search, "extras_"):
                    for key in search.extras_[index][fold].get("counts", {}).keys():
                        result[key + "_size"] = search.extras_[index][fold]["counts"][key]
                results.append(result)
            if hasattr(search, "extras_") and self.classes and len(self.classes) == 2:
                print ["%0.8f" % x for x in self._validateExtras(search.extras_[index], y_train)], "(eval:auc)"
            print scores, "(" + self.metric + ")"
            print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)                    
            index += 1
        print "---------------------- Best scores on development set --------------------------"
        params, mean_score, scores = bestScores
        print scores
        print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
        baselines = self._calculateBaseline(cv, y_train)
        print "MCB = %0.3f (+/-%0.03f) for" % (np.mean(baselines), np.std(baselines) / 2), ["%0.3f" % x for x in baselines], "(" + self.metric + ")"
        print "--------------------------------------------------------------------------------"
        # Save the grid search results
        print "Saving results"
        self._insert("result", results)
        self._saveExtras(bestExtras, "train")
        self.meta.flush() 
        return search
    
    def _calculateBaseline(self, cv, labels):
        exampleGroups = [self.groups[i] for i in self.indices["train"]]
        baselines = []
        for trainIndices, testIndices in cv:
            foldLabels = [labels[i] for i in testIndices]
            foldGroups = [exampleGroups[i] for i in testIndices]
            #print len(foldLabels)
            baselines.append(majorityBaseline(foldLabels, foldGroups, self.metric))
        return baselines
    
    def _validateExtras(self, folds, labels):
        validationScores = []
        for fold in range(len(folds)):
            if self.classes and len(self.classes) == 2 and "probabilities" in folds[fold]:
                probabilityByIndex = folds[fold]["probabilities"]
                foldIndices = sorted(probabilityByIndex.keys())
                foldLabels = [labels[i] for i in foldIndices]
                foldProbabilities = [probabilityByIndex[i] for i in foldIndices]
                foldPredictions = getClassPredictions(foldProbabilities, self.classes)
                #print fold, foldProbabilities
                #print len(foldLabels)
                folds[fold]["predictions"] = {i:x for i,x in zip(foldIndices, foldPredictions)}
                validationScores.append(aucForPredictions(foldLabels, foldPredictions))
        return validationScores   
    
    def _saveExtras(self, folds, setName, noFold=False):
        if folds == None or not self.saveExtra:
            return
        for fold in range(len(folds)):
            extras = folds[fold]
            foldIndex = None if noFold else fold
            if "predictions" in extras:
                rows = [OrderedDict([("example",self.indices[setName][setIndex]), ("fold",foldIndex), ("set",setName), ("predicted", extras["predictions"][setIndex])]) for setIndex in sorted(extras["predictions"].keys())]
                self._insert("prediction", rows)
            if "importances" in extras:
                importances = extras["importances"]
                self._insert("importance", [OrderedDict([("feature",i), ("fold",foldIndex), ("value",importances[i]), ("set",setName)]) for i in range(len(importances)) if importances[i] != 0])        
        
    def _predictHidden(self, y_hidden, X_hidden, search, trainSize=None):
        if X_hidden.shape[0] > 0:
            print "----------------------------- Classifying Hidden Set -----------------------------------"
            print "search.scoring", search.scoring
            print "search.scorer_", search.scorer_
            print "search.best_estimator_.score", search.best_estimator_.score
            score = search.score(X_hidden, y_hidden) #roc_auc_score(y_hidden, search.best_estimator_.predict(X_hidden))
            print "Score =", score, "(" + self.metric + ")"
            hiddenResult = self._getResult("hidden", search.best_estimator_.__class__, None, search.best_params_, score)
            hiddenResult["train_size"] = trainSize
            hiddenResult["test_size"] = y_hidden.shape[0]
            y_hidden_proba = search.predict_proba(X_hidden)
            #if self.classes and len(self.classes) == 2:
            #    y_hidden_pred = getClassPredictions(y_hidden_proba, self.classes)
            #    print "AUC =", aucForPredictions(y_hidden, y_hidden_pred), "(eval:auc)"
            #    hiddenExtra = {"predictions":{i:x for i,x in enumerate(y_hidden_pred)}}
            #else:
            hiddenExtra = {"probabilities":{i:x for i,x in enumerate(y_hidden_proba)}}
            print "AUC =", self._validateExtras([hiddenExtra], y_hidden)[0]
            print "MCB =", majorityBaseline(y_hidden, [self.groups[i] for i in self.indices["hidden"]], self.metric), "(" + self.metric + ")"
            if hasattr(search.best_estimator_, "feature_importances_"):
                hiddenExtra["importances"] = search.best_estimator_.feature_importances_
            print "Saving results"
            self._insert("result", [hiddenResult])
            self._saveExtras([hiddenExtra], "hidden", True)
            self.meta.flush()
            if "predictions" in hiddenExtra:
                try:
                    print classification_report(y_hidden, getClassPredictions(y_hidden_proba, self.classes))
                except ValueError, e:
                    print "ValueError in classification_report:", e
        print "--------------------------------------------------------------------------------"