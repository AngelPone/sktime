# -*- coding: utf-8 -*-
"""Summary Classifier.

Pipeline classifier using the basic summary statistics and an estimator.
"""

__author__ = ["MatthewMiddlehurst"]
__all__ = ["SummaryClassifier"]

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from sktime.base._base import _clone_estimator
from sktime.classification.base import BaseClassifier


class SummaryClassifier(BaseClassifier):
    """Summary statistic classifier.

    This classifier simply transforms the input data using the SummaryTransformer
    transformer and builds a provided estimator using the transformed data.

    Parameters
    ----------
    summary_functions=("mean", "std", "min", "max"),

    summary_quantiles=(0.25, 0.5, 0.75),

    estimator : sklearn classifier, default=None
        An sklearn estimator to be built using the transformed data. Defaults to a
        Random Forest with 200 trees.
    n_jobs : int, default=1
        The number of jobs to run in parallel for both `fit` and `predict`.
        ``-1`` means using all processors.
    random_state : int or None, default=None
        Seed for random, integer.

    Attributes
    ----------
    n_classes_ : int
        Number of classes. Extracted from the data.
    classes_ : ndarray of shape (n_classes)
        Holds the label for each class.

    See Also
    --------
    SummaryTransformer

    Examples
    --------
    >>> from sktime.classification.feature_based import SummaryClassifier
    >>> from sklearn.ensemble import RandomForestClassifier
    >>> from sktime.datasets import load_unit_test
    >>> X_train, y_train = load_unit_test(split="train", return_X_y=True)
    >>> X_test, y_test = load_unit_test(split="test", return_X_y=True)
    >>> clf = SummaryClassifier(estimator=RandomForestClassifier(n_estimators=10))
    >>> clf.fit(X_train, y_train)
    SummaryClassifier(...)
    >>> y_pred = clf.predict(X_test)
    """

    _tags = {
        "capability:multivariate": True,
        "capability:multithreading": True,
    }

    def __init__(
        self,
        summary_functions=("mean", "std", "min", "max"),
        summary_quantiles=(0.25, 0.5, 0.75),
        estimator=None,
        n_jobs=1,
        random_state=None,
    ):
        self.summary_functions = summary_functions
        self.summary_quantiles = summary_quantiles
        self.estimator = estimator

        self.n_jobs = n_jobs
        self.random_state = random_state

        self._transformer = None
        self._estimator = None

        super(SummaryClassifier, self).__init__()

    def _fit(self, X, y):
        # self._transformer = SummaryTransformer(
        #     summary_function=self.summary_functions,
        #     quantiles=self.summary_quantiles,
        # )

        self._estimator = _clone_estimator(
            RandomForestClassifier(n_estimators=200)
            if self.estimator is None
            else self.estimator,
            self.random_state,
        )

        m = getattr(self._estimator, "n_jobs", None)
        if m is not None:
            self._estimator.n_jobs = self._threads_to_use

        X_t = self._transformer.fit_transform(X, y)
        self._estimator.fit(X_t, y)

        return self

    def _predict(self, X):
        return self._estimator.predict(self._transformer.transform(X))

    def _predict_proba(self, X):
        m = getattr(self._estimator, "predict_proba", None)
        if callable(m):
            return self._estimator.predict_proba(self._transformer.transform(X))
        else:
            dists = np.zeros((X.shape[0], self.n_classes_))
            preds = self._estimator.predict(self._transformer.transform(X))
            for i in range(0, X.shape[0]):
                dists[i, self._class_dictionary[preds[i]]] = 1
            return dists
