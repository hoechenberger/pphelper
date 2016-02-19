# -*- coding: utf-8 -*-

"""
Some functions that come in handy when working with psychophysics
datasets.

"""

from __future__ import division, unicode_literals
import sys
import pandas as pd
import itertools
import numpy as np


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


def join_multi_level_index(index, sep='_'):
    """

    Parameters
    ----------
    index : MultiIndex
        The index to join.

    sep : string, optional
        The separator to insert between the joined index.
        Defaults to an underscore (`_`).

    Returns
    -------
    The joined index.
    """
    return [sep.join(x) for x in index]
