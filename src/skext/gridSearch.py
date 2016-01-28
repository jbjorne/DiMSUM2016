# Imports for ExtendedGridSearchCV
from sklearn.grid_search import GridSearchCV, ParameterGrid, _CVScoreTuple
from sklearn.metrics.scorer import check_scoring
from sklearn.utils.validation import _num_samples, indexable
from sklearn.cross_validation import _check_cv as check_cv
from sklearn.base import is_classifier, clone
from sklearn.externals.joblib import Parallel, delayed
from sklearn.cross_validation import _fit_and_score
from collections import Sized
import numpy as np

# Imports for _extended_fit_and_score
import time, numbers, warnings
from sklearn.externals.joblib import logger
from sklearn.cross_validation import _index_param_value, _safe_split, _score, FitFailedWarning
from sklearn.utils import safe_mask

def _extended_fit_and_score(estimator, X, y, scorer, train, test, verbose,
                   parameters, fit_params, return_train_score=False,
                   return_parameters=False, error_score='raise', extraOut="auto"):
    if verbose > 1:
        if parameters is None:
            msg = "no parameters to be set"
        else:
            msg = '%s' % (', '.join('%s=%s' % (k, v)
                          for k, v in parameters.items()))
        print("[CV] %s %s" % (msg, (64 - len(msg)) * '.'))

    # Adjust length of sample weights
    fit_params = fit_params if fit_params is not None else {}
    fit_params = dict([(k, _index_param_value(X, v, train))
                      for k, v in fit_params.items()])

    if parameters is not None:
        estimator.set_params(**parameters)

    start_time = time.time()

    X_train, y_train = _safe_split(estimator, X, y, train)
    X_test, y_test = _safe_split(estimator, X, y, test, train)

    try:
        if y_train is None:
            estimator.fit(X_train, **fit_params)
        else:
            estimator.fit(X_train, y_train, **fit_params)

    except Exception as e:
        if error_score == 'raise':
            raise
        elif isinstance(error_score, numbers.Number):
            test_score = error_score
            if return_train_score:
                train_score = error_score
            warnings.warn("Classifier fit failed. The score on this train-test"
                          " partition for these parameters will be set to %f. "
                          "Details: \n%r" % (error_score, e), FitFailedWarning)
        else:
            raise ValueError("error_score must be the string 'raise' or a"
                             " numeric value. (Hint: if using 'raise', please"
                             " make sure that it has been spelled correctly.)"
                             )

    else:
        test_score = _score(estimator, X_test, y_test, scorer)
        if return_train_score:
            train_score = _score(estimator, X_train, y_train, scorer)

    scoring_time = time.time() - start_time

    if verbose > 2:
        msg += ", score=%f" % test_score
    if verbose > 1:
        end_msg = "%s -%s" % (msg, logger.short_format_time(scoring_time))
        print("[CV] %s %s" % ((64 - len(end_msg)) * '.', end_msg))

    ret = [train_score] if return_train_score else []
    ret.extend([test_score, _num_samples(X_test), scoring_time])
    if return_parameters:
        ret.append(parameters)
    
    # Add additional return values
    extraRVs = {}
    if extraOut != None:
        extraRVs["counts"] = {"train":train.shape[0], "test":test.shape[0]}
        if "estimator" in extraOut:
            extraRVs["estimator"] = estimator
        if extraOut == "auto" or "predictions" in extraOut:
            assert test.shape[0] == X_test.shape[0]
            probabilities = estimator.predict_proba(X_test)
            probabilityByIndex = {}
            for exampleIndex, prediction in zip(test, probabilities):
                probabilityByIndex[exampleIndex] = prediction
            extraRVs["probabilities"] = probabilityByIndex
        if (extraOut == "auto" or "importances" in extraOut) and hasattr(estimator, "feature_importances_"):
            extraRVs["importances"] = estimator.feature_importances_
    ret.append(extraRVs)
    
    return ret

class ExtendedGridSearchCV(GridSearchCV):

    def __init__(self, estimator, param_grid, scoring=None, loss_func=None,
                 score_func=None, fit_params=None, n_jobs=1, iid=True,
                 refit=True, cv=None, verbose=0, pre_dispatch='2*n_jobs'):
        super(ExtendedGridSearchCV, self).__init__(
            estimator=estimator, 
            param_grid=param_grid, 
            scoring=scoring, 
            loss_func=loss_func, 
            score_func=score_func, 
            fit_params=fit_params, 
            n_jobs=n_jobs, 
            iid=iid,
            refit=refit, 
            cv=cv, 
            verbose=verbose, 
            pre_dispatch=pre_dispatch)

    def fit(self, X, y=None):
        return self._extendedFit(X, y, ParameterGrid(self.param_grid))
    
    def _extendedFit(self, X, y, parameter_iterable):
        estimator = self.estimator
        cv = self.cv
        self.scorer_ = check_scoring(self.estimator, scoring=self.scoring)

        n_samples = _num_samples(X)
        X, y = indexable(X, y)

        if y is not None:
            if len(y) != n_samples:
                raise ValueError('Target variable (y) has a different number '
                                 'of samples (%i) than data (X: %i samples)'
                                 % (len(y), n_samples))
        cv = check_cv(cv, X, y, classifier=is_classifier(estimator))

        if self.verbose > 0:
            if isinstance(parameter_iterable, Sized):
                n_candidates = len(parameter_iterable)
                print("Fitting {0} folds for each of {1} candidates, totalling"
                      " {2} fits".format(len(cv), n_candidates,
                                         n_candidates * len(cv)))

        base_estimator = clone(self.estimator)

        pre_dispatch = self.pre_dispatch

        out = Parallel(
            n_jobs=self.n_jobs, verbose=self.verbose,
            pre_dispatch=pre_dispatch
        )(
            delayed(_extended_fit_and_score)(clone(base_estimator), X, y, self.scorer_,
                                    train, test, self.verbose, parameters,
                                    self.fit_params, return_parameters=True,
                                    error_score=self.error_score)
                for parameters in parameter_iterable
                for train, test in cv)

        # Out is a list of triplet: score, estimator, n_test_samples
        n_fits = len(out)
        n_folds = len(cv)

        scores = list()
        grid_scores = list()
        grid_extras = list()
        for grid_start in range(0, n_fits, n_folds):
            n_test_samples = 0
            score = 0
            all_scores = []
            all_extras = []
            for this_score, this_n_test_samples, _, parameters, extra in \
                    out[grid_start:grid_start + n_folds]:
                all_scores.append(this_score)
                all_extras.append(extra)
                if self.iid:
                    this_score *= this_n_test_samples
                    n_test_samples += this_n_test_samples
                score += this_score
            if self.iid:
                score /= float(n_test_samples)
            else:
                score /= float(n_folds)
            scores.append((score, parameters))
            # TODO: shall we also store the test_fold_sizes?
            grid_scores.append(_CVScoreTuple(
                parameters,
                score,
                np.array(all_scores)))
            grid_extras.append(all_extras)
        # Store the computed scores
        self.grid_scores_ = grid_scores
        self.extras_ = grid_extras

        # Find the best parameters by comparing on the mean validation score:
        # note that `sorted` is deterministic in the way it breaks ties
        best = sorted(grid_scores, key=lambda x: x.mean_validation_score,
                      reverse=True)[0]
        self.best_params_ = best.parameters
        self.best_score_ = best.mean_validation_score

        if self.refit:
            print "Refitting best estimator"
            # fit the best estimator using the entire dataset
            # clone first to work around broken estimators
            best_estimator = clone(base_estimator).set_params(
                **best.parameters)
            if y is not None:
                best_estimator.fit(X, y, **self.fit_params)
            else:
                best_estimator.fit(X, **self.fit_params)
            self.best_estimator_ = best_estimator
        return self