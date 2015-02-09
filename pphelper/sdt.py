# -*- coding: utf-8 -*-

"""
Some functions that come in handy when working with psychophysics
datasets.

Provides
--------
 - ``d_prime`` : Calculate the sensitivity index d' ("d-prime").
 - ``criterion`` : Calculate the decision criterion C.
"""

from __future__ import division, unicode_literals
from scipy.stats import norm


def d_prime(hits, false_alarms, n, nafc=1):
    """
    Calculate the sensitivity index d' ("d-prime").

    Parameters
    ----------
    hits : float
        The number of hits when detecting a signal.
    false_alarms : float
        The number of false alarms.
    n : int
        The number of trials in target and no-target trials.
    nafc : int, optional
        The number of alternative choices in the task. A value of ``1``
        implies a Yes/No task.
        Defaults to 1.

    Returns
    -------
    d : float
        The calculated d' value, z(hit_rate) - z(fa_rate).

    Example
    -------
    >>> from pphelper import sdt
    >>> sdt.d_prime(20, 10, 25)
    1.094968336708714

    """
    if nafc != 1:
        raise NotImplementedError('Only 1-AFC implemented so far.')

    hit_rate, fa_rate = _calculate_hit_and_fa_rates(hits, false_alarms, n)
    d = norm.ppf(hit_rate) - norm.ppf(fa_rate)
    return d


def criterion(hits, false_alarms, n, nafc=1):
    """
    Calculate the decision criterion C.

    Parameters
    ----------
    hits : float
        The number of hits when detecting a signal.
    false_alarms : float
        The number of false alarms.
    n : int
        The number of trials in target and no-target trials.
    nafc : int, optional
        The number of alternative choices in the task. A value of ``1``
        implies a Yes/No task.
        Defaults to 1.

    Returns
    -------
    C : float
        The decision criterion. This will be zero for an unbiased observer,
        and non-zero otherwise. In a 1-AFC (Yes/No) task, a value smaller
        than 0 implies a bias to responding "Yes", and a value greater
        than 0 a bias to responding "No".

    Example
    -------
    >>> from pphelper import sdt
    >>> sdt.criterion(20, 10, 25)
    -0.29413706521855731

    """
    if nafc != 1:
        raise NotImplementedError('Only 1-AFC implemented so far.')

    hit_rate, fa_rate = _calculate_hit_and_fa_rates(hits, false_alarms, n)
    C = -0.5 * (norm.ppf(hit_rate) + norm.ppf(fa_rate))
    return C


def _calculate_hit_and_fa_rates(hits, false_alarms, n):
    hit_rate = hits / n
    fa_rate = false_alarms / n

    # Adjust for exteme cases, loglinear approach
    # http://stats.stackexchange.com/a/134802
    if (hit_rate == 0) or (hit_rate == 1) or (fa_rate == 0) or \
            (fa_rate == 1):
        hit_rate = (hits + 0.5) / (n + 1)
        fa_rate = (false_alarms + 0.5) / (n + 1)

    return hit_rate, fa_rate