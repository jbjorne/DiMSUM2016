from sklearn.cross_validation import StratifiedKFold
from _collections import defaultdict
import numpy as np
import random

class BalancedIteratorCV():
    def __init__(self, y_train, n_folds, shuffle, random_state, examples, groupBy, balanced=True):
        assert len(y_train) == len(examples)
        self.cv = StratifiedKFold(y_train, n_folds=n_folds, shuffle=shuffle, random_state=random_state)
        self.folds = [x for x in self.cv]
        
        if balanced:
            exampleByIndex = {i:examples[i] for i in range(len(examples))}
            for foldIndex in range(len(self.folds)): 
                train_indices, test_indices = self.folds[foldIndex]
                # Count examples grouped
                counts = defaultdict(lambda: defaultdict(int))
                indices = {}
                i = 0
                for i in train_indices:
                    i = int(i)
                    example = exampleByIndex[i]
                    group = example[groupBy]
                    classId = y_train[i]
                    counts[group][classId] += 1
                    if group not in indices: indices[group] = {}
                    if classId not in indices[group]:
                        indices[group][classId] = []
                    indices[group][classId].append(i)
                # Determine per class sizes
                extra = defaultdict(lambda: defaultdict(int))
                for groupKey in counts:
                    groupCounts = counts[groupKey]
                    minorityClassSize = groupCounts[min(groupCounts, key=groupCounts.get)]
                    for classId in groupCounts:
                        extra[groupKey][classId] = groupCounts[classId] - minorityClassSize
                # Oversample training data
                newIndices = []
                for groupKey in extra:
                    for classId in extra[groupKey]:
                        newIndices.extend([random.choice(indices[groupKey][classId]) for _ in range(extra[groupKey][classId])])
                        #newIndices.extend(random.sample(indices[groupKey][classId], extra[groupKey][classId]))
                self.folds[foldIndex] = (np.append(train_indices, np.array(newIndices)), test_indices)
        
    def __len__(self):
        return len(self.cv)
    
    def __iter__(self):
        self._iterIndex = 0
        return self

    def next(self):
        if self._iterIndex >= len(self.folds):
            raise StopIteration
        else:
            i = self._iterIndex
            self._iterIndex += 1
            #print self.folds[i]
            return self.folds[i]