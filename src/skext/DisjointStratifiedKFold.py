from sklearn.cross_validation import StratifiedKFold, KFold, _BaseKFold
import numpy as np
from sklearn.utils.fixes import bincount
import warnings
from sklearn.utils import check_random_state

class DisjointStratifiedKFold():

    def __init__(self, y, n_folds=3, shuffle=False, random_state=None):
        indicesByLabel = {}
        for i in range(len(y)):
            label = y[i]
            if label not in indicesByLabel:
                indicesByLabel[label] = []
            indicesByLabel[label].append(i)
        folds = n_folds * [[]]
        print indicesByLabel
        for label in sorted(indicesByLabel.keys()):
            indices = indicesByLabel[label]
            chunkSize = len(indices) / n_folds
            chunkedIndices = [indices[i*chunkSize:(i+1)*chunkSize] for i in range(n_folds)]
            folds = [folds[i] + chunkedIndices[i] for i in range(n_folds)]
        self.folds = [np.array(x) for x in folds]
        #self.y_indices = np.array(range(len(y)))
        self.y = y
        print self.folds
        print len(self.y)
        print [x for x in self]
    
    def __len__(self):
        return len(self.folds)
    
    def __iter__(self):
        self._iterIndex = 0
        return self

    def next(self):
        if self._iterIndex >= len(self.folds):
            raise StopIteration
        else:
            i = self._iterIndex
            self._iterIndex += 1
            test_indices = self.folds[i]
            train_indices = np.array([i for i in range(len(self.y)) if i not in set(test_indices)])
            #print (train_indices, test_indices)
            return (train_indices, test_indices)