from sklearn.metrics.scorer import SCORERS, make_scorer
def getMajorityPredictions(labels, groups=None):
    majorityLabel = getMajorityClasses(labels, groups)
    return [majorityLabel[group] for group in groups]

def getMajorityPredictionsPredefined(groups, majorityLabel):
    return [majorityLabel[group] for group in groups]

def getMajorityClasses(labels, groups=None):
    counts = {}
    # Count labels by group
    if groups == None:
        groups = len(labels) * ["ALL"]
    assert len(groups) == len(labels)
    for label, groupKey in zip(labels, groups):
        if groupKey not in counts:
            counts[groupKey] = {} 
        groupCounts = counts[groupKey]
        if label not in groupCounts:
            groupCounts[label] = 0
        groupCounts[label] += 1
    # Determine majority labels
    majorityLabel = {}
    for groupKey in counts:
        majorityLabel[groupKey] = max(counts[groupKey], key=counts[groupKey].get)
    return majorityLabel

def majorityBaseline(labels, groups=None, metric=None):
    if metric == None:
        metric = aucForPredictions
    if isinstance(metric, basestring):
        metric = SCORERS[metric]._score_func
    return metric(labels, getMajorityPredictions(labels, groups))

def aucForPredictions(labels, predictions):
    return listwisePerformance(labels, predictions)

def getClassPredictions(probabilities, classes):
    predictions = []
    for prob in probabilities:
        assert len(prob) == len(classes)
        if prob[0] > prob[1]:
            predictions.append(prob[0] * classes[0])
        else:
            predictions.append(prob[1] * classes[1])
    return predictions

def aucForProbabilites(labels, probabilities, classes):
    return listwisePerformance(labels, getClassPredictions(probabilities, classes))

def listwisePerformance(correct, predicted):
    assert len(correct) == len(predicted)
    pos, neg = 0., 0.
    posindices = []
    negindices = []
    for i in range(len(correct)):
        if correct[i]>0:
            pos += 1.
            posindices.append(i)
        else:
            neg += 1
            negindices.append(i)
    auc = 0.
    for i in posindices:
        for j in negindices:
            if predicted[i] > predicted[j]:
                auc += 1.
            elif predicted[i] == predicted[j]:
                auc += 0.5
    auc /= pos * neg
    return auc

def statistics(correct, predicted):
    assert len(correct) == len(predicted)
    results = {}
    for label, pred in zip(correct, predicted):
        if pred not in results:
            results[pred] = {True:0, False:0}
        if label != pred:
            results[pred][False] += 1
        else:
            results[pred][True] += 1
    return results