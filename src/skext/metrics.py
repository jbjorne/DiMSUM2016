from sklearn.metrics.classification import _check_targets, confusion_matrix
import numpy as np

"""
Balanced Accuracy Score from https://github.com/TTRh/scikit-learn/blob/balanced_accuracy_score/sklearn/metrics/classification.py
"""

def balanced_accuracy_score(y_true, y_pred, balance=0.5):
    """Balanced accuracy classification score.
    The formula for the balanced accuracy score ::
        balanced accuracy = balance * TP/(TP + FP) + (1 - balance) * TN/(TN + FN)
    Because it needs true/false negative/positive notion it only
    supports binary classification.
    The `balance` parameter determines the weight of sensitivity in the combined
    score. ``balance -> 1`` lends more weight to sensitiviy, while ``balance -> 0``
    favors specificity (``balance = 1`` considers only sensitivity, ``balance = 0``
    only specificity).
    Read more in the :ref:`User Guide <balanced_accuracy_score>`.
    Parameters
    ----------
    y_true : 1d array-like, or label indicator array / sparse matrix
        Ground truth (correct) labels.
    y_pred : 1d array-like, or label indicator array / sparse matrix
        Predicted labels, as returned by a classifier.
    balance : float between 0 and 1. Weight associated with the sensitivity
        (or recall) against specificty in final score.
    Returns
    -------
    score : float
    See also
    --------
    accuracy_score
    References
    ----------
    .. [1] `Wikipedia entry for the accuracy and precision
           <http://en.wikipedia.org/wiki/Accuracy_and_precision>`
    Examples
    --------
    >>> import numpy as np
    >>> from sklearn.metrics import balanced_accuracy_score
    >>> y_pred = [0, 0, 1]
    >>> y_true = [0, 1, 1]
    >>> balanced_accuracy_score(y_true, y_pred)
    0.75
    >>> y_pred = ["cat", "cat", "ant"]
    >>> y_true = ["cat", "ant", "ant"]
    >>> balanced_accuracy_score(y_true, y_pred)
    0.75
    """

    if balance < 0. or 1. < balance:
        raise ValueError("balance has to be between 0 and 1")

    y_type, y_true, y_pred = _check_targets(y_true, y_pred)
    if y_type is not "binary":
        raise ValueError("%s is not supported" % y_type)

    cm = confusion_matrix(y_true, y_pred)
    neg, pos = cm.sum(axis=1, dtype='float')
    tn, tp = np.diag(cm)

    sensitivity = tp / pos
    specificity = tn / neg

    return balance * sensitivity + (1 - balance) * specificity