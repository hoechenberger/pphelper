# -*- coding: utf-8 -*-

"""
Some functions that come in handy when working with psychophysics
datasets.

Provides
--------
 - ``add_zero_padding`` : Convert numbers (typically participant IDs) to strings of specific length, with leading zeros where necessary.
 - ``get_max_from_list`` : Return the maximum value from a list or a list of lists.
"""

from __future__ import division, unicode_literals
import sys
import pandas as pd
import itertools
import numpy as np
from collections import namedtuple


def add_zero_padding(data, length=3, return_series=True):
    """
    Convert input values to strings and add a zero-padding.

    Parameters
    ----------
    data : array_like
        The data to process.
    length : int, optional
        The desired length of the padded output values.
    return_series : bool, optional
        If `True`, return a pandas `Series` object. If false, return a
        numpy array.

    Returns
    -------
    result : Series or ndarray
        The padded input vector. All strings are created as unicode
        literals.

    Notes
    -----
    If ``length`` is less than the length of one of the elements, these
    elements will be converted to strings only and returned. They will
    obviously not be zero-padded, but they will also not be truncated.

    """
    data = pd.Series(data)

    # Unicode is the default in Python >= 3.0.
    if sys.version_info > (3, 0):
        result = data.apply(lambda x: str(x).zfill(length))
    else:
        result = data.apply(lambda x: unicode(x).zfill(length))

    if return_series:
        return result
    else:
        return result.values


def get_max_from_list(x):
    """
    Return the maximum value from a list or a list of lists.

    Parameters
    ----------
    x : list
        A list or a list of lists.

    Returns
    -------
    float
        The maximum value.

    """
    return np.array(list(itertools.chain.from_iterable(x))).max()


def bootstrap_ci(data, stat_fun=np.mean, n_samples=2000, alpha=0.05):
    """
    Return bootstrap estimate of ``100 * (1-alpha)`` confidence intervals
    (CIs) for the statistic calculated by stat_fun().

    Parameters
    ----------
    data : array_like
        The input data.
    stat_fun : function, optional
        The function to use for calculating the statistics.
        Defaults to ``np.mean``.
    n_samples : int, optional
        The number of samples to draw with replacement.
    alpha : float, optional
        The alpha level used to calculate the CIs.

    Returns
    -------
    result : namedtuple
        The lower and upper bounds of the confidence interval.

    Notes
    -----
    Adapted from http://people.duke.edu/~ccc14/pcfb/analysis.html
    © Copyright 2012, Cliburn Chan.

    """
    data = np.array(data)
    n = len(data)
    idx = np.random.randint(0, n, (n_samples, n))
    samples = data[idx]
    stat = np.sort(stat_fun(samples, 1))

    confidence_interval = namedtuple('CI', 'lower upper')
    result = confidence_interval(
        lower=stat[int((alpha/2) * n_samples)],
        upper=stat[int((1 - alpha/2) * n_samples)]
    )

    return result
