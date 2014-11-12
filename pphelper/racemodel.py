# -*- coding: utf-8 -*-

"""
pphelper.racemodel
==================

Race model inequality analysis implementation, based on Ulrich, Miller,
and Schröter (2007): 'Testing the race model inequality: An algorithm
and computer programs', published in Behavior Research Methods 39 (2),
pp. 291-302.

Provides
--------
 - ``gen_cdf`` : Estimate the cumulative distribution function from response time data.
 - ``gen_cdfs_from_list`` : Convenience function: Applys `gen_cdf` to a list of data sets.
 - ``gen_percentiles`` : Calculate equally spaced percentiles values.
 - ``get_percentiles_from_cdf`` : Get the values (response times) of a cumulative distribution function at the specified percentiles.
 - ``gen_step_fun`` : Generate a step function from a set of observed response times.
 - ``ttest`` : Perform statistical tests.
 - ``plot_cdfs`` : Plot

"""

from __future__ import division, unicode_literals
import pandas as pd
import numpy as np
from scipy.stats import ttest_rel, wilcoxon
from . import utils


def gen_cdf(rts, t_max=None):
    """
    Estimate the cumulative frequency polygon from response time data.

    Parameters
    ----------
    rts : array_like
        The raw response time data. Data does not need to be ordered and
        may contain duplicate values.
    t_max : int, optional
        Up to which time point (in milliseconds) the model should be
        calculated. If not specified, the maximum value of the supplied
        input data will be used.

    Returns
    -------
    Series
        A Series containing the estimated cumulative frequency polygon,
        indexed by the time points in ms.

    Notes
    -----
    Response times will be rounded to 1 millisecond.
    The algorithm is described in Ulrich, Miller, and Schröter (2007):
    'Testing the race model inequality: An algorithm and computer
    programs', published in Behavior Research Methods 39 (2), pp. 291-302.

    Examples
    --------
    >>> from pphelper.racemodel import gen_cdf
    >>> import numpy as np
    >>> RTs = np.array([234, 238, 240, 240, 243, 243, 245, 251, 254, 256, 259, 270, 280])
    >>> gen_cdf(RTs, t_max=RTs.max())
    t
    0     0
    1     0
    2     0
    3     0
    4     0
    5     0
    6     0
    7     0
    8     0
    9     0
    10    0
    11    0
    12    0
    13    0
    14    0
    ...
    266    0.856643
    267    0.863636
    268    0.870629
    269    0.877622
    270    0.884615
    271    0.892308
    272    0.900000
    273    0.907692
    274    0.915385
    275    0.923077
    276    0.930769
    277    0.938462
    278    0.946154
    279    0.953846
    280    1.000000
    Length: 281, dtype: float64

    See Also
    --------
    get_percentiles_from_cdf

    """

    # Convert input data to a Series, and round to 1 ms
    rts = pd.Series(rts).round().astype('int')

    if t_max is None:
        t_max = rts.max()
    else:
        t_max = int(round(t_max))

    # The variable names correspond to following variables
    # in the paper:
    #
    # C == rts
    # n == n
    # k == n_unique
    # N == rt_count
    # s == rt_cumsum

    rts_sorted = rts.order()
    rts_unique = rts_sorted.unique()

    n = rts_sorted.size
    n_unique = rts_unique.size

    # Number of occurrences of each element.
    rt_count = rts_sorted.value_counts().sort_index()
    rt_cumsum = rt_count.cumsum()

    # Add leading 0 element because our algorithm
    # starts iteration at index 1.
    # This is done to maintain close similarity to the published algorithm.
    rts_unique = np.append(0, rts_unique)
    rt_cumsum = np.append(0, rt_cumsum)
    rt_count = np.append(0, rt_count)

    result = np.zeros(t_max+1)
    timeline = np.arange(t_max+1)
    i = 1

    for t in timeline:
        if t < rts_unique[1]:
            result[t] = 0
        elif t >= rts_unique[-1]:
            result[t] = 1
        elif i < n_unique:
            result[t] = 1/n * \
                (rt_cumsum[i-1] + rt_count[i]/2 +
                 (rt_count[i] + rt_count[i+1]) / 2 *
                 (t - rts_unique[i]) /
                 (rts_unique[i+1] - rts_unique[i]))

            if t+1 == rts_unique[i+1]:
                i += 1

    return pd.Series(result, index=pd.Index(timeline, name='t'))


def gen_cdfs_from_list(data, t_max=None, names=None):
    """
    Estimate the empirical CDFs for a list of arrays.

    The is a convenience function that wraps `gen_cdf`.

    Parameters
    ----------
    data : list of array_like objects
        A list of raw response time arrays. The RTs do not have to be
        ordered and may contain duplicate values.
    t_max : int, optional
        Up to which time point (in milliseconds) the model should be
        calculated. If not specified, the maximum value of the supplied
        input data will be used.

    Return
    ------
    list of Series
    A list of the estimated empirical CDFs.

    """

    if t_max is None:
        t_max = utils.get_max_from_list(data)

    if names and (len(data) != len(names)):
        raise ValueError('Please supply a name parameter with the same'
                         'number of elements as your data list.')

    results = pd.DataFrame([gen_cdf(x, t_max=t_max) for x in data]).T
    if names:
        results.columns = names

    return results


def gen_percentiles(n=10):
    """
    Calculate n equally spaced percentiles.

    Parameters
    ----------
    n : int, optional
        The number of percentiles to generate. Defaults to 10. Floats will
        be rounded.

    Returns
    -------
    p : ndarray
        1-dimensional array of the calculated percentiles.

    See Also
    --------
    get_percentiles_from_cdf

    Examples
    --------
    >>> from pphelper.racemodel import gen_percentiles
    >>> gen_percentiles()
    array([ 0.05,  0.15,  0.25,  0.35,  0.45,  0.55,  0.65,  0.75,  0.85,  0.95])

    """

    try:
        n = int(round(n))
    except TypeError:
        raise TypeError('Please supply an integer to gen_percentiles().')

    p = np.zeros(n)
    for i in range(1, n+1):
        p[i-1] = (i-0.5) / n

    return p


def get_percentiles_from_cdf(cdf, p):
    """
    Interpolate the percentile boundaries.

    Parameters
    ----------
    cdf : Series
        The cumulative distribution polygon. Usually generated by
        `gen_cdf()`.
    p : array_like
        The percentiles for which to get values from the polygon.
        Usually generated by `gen_percentiles()`.

    Returns
    -------
    Series
        Returns a Series of interpolated percentile boundaries (fictive
        response times).

    See Also
    --------
    gen_cdf, gen_percentiles

    Examples
    --------
    >>> from pphelper.racemodel import gen_cdf, gen_percentiles, get_percentiles_from_cdf
    >>> import numpy as np
    >>> RTs = np.array([234, 238, 240, 240, 243, 243, 245, 251, 254, 256, 259, 270, 280])
    >>> cdf = gen_cdf(RTs)
    >>> percentiles = gen_percentiles(5)
    >>> get_percentiles_from_cdf(cdf, percentiles)
    p
    0.1    237.20
    0.3    241.35
    0.5    245.00
    0.7    255.20
    0.9    272.00
    dtype: float64

    """

    try:
        p = np.array(p).flatten()
        n_percentiles = p.shape[0]
    except TypeError:
        raise TypeError('Please supply an array-like object with '
                        'percentile values to get_percentiles_from_cdf().')

    try:
        timeline = cdf.index
    except AttributeError:
        raise TypeError('Please supply a pandas Series with cumulative '
                        'distribution function values to '
                        'get_percentiles_from_cdf().')

    percentile_boundaries = np.zeros(len(p))

    i = 0
    for t in timeline:
        # The '< cdf.iloc[t+1]' part is here so the last one of subsequent
        # identical values is picked for inclusion in the current
        # percentile before moving to the next one.
        if (i < n_percentiles) and (cdf.iloc[t] <= p[i] < cdf.iloc[t+1]):
            percentile_boundaries[i] = (p[i] - cdf.iloc[t]) * (t+1 - t) / \
                                       (cdf.iloc[t+1] - cdf.iloc[t]) + t
            i += 1

    return pd.Series(percentile_boundaries, index=pd.Index(p, name='p'))


def gen_step_fun(rts):
    """
    Generate a step function from an observed response time distribution.

    Parameters
    ----------
    rts : array_like
        The input data (usually response times) to generate a step function
        from. Does not have to be ordered and may contain duplicates.

    Returns
    -------
    Series
        A Series of the ordered response times (smallest to largest),
        indexed by their respective percentiles.

    Examples
    --------
    >>> from pphelper.racemodel import gen_step_fun
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> RTs = np.array([234, 238, 240, 240, 243, 243, 245, 251, 254, 256, 259, 270, 280])
    >>> sf = gen_step_fun(RTs)
    >>> plt.step(sf, sf.index, where='post'); plt.show()

    """

    # Drop duplicate values and sort in ascending order
    rts_sorted = np.unique(rts)
    p = np.arange(1, len(rts_sorted)+1) / len(rts_sorted)

    return pd.Series(rts_sorted, pd.Index(p, name='p'))


def plot_cdfs(data, percentile_index='p', colors=None, outfile=None):
    # TODO rework this function
    """
    Plot the response time distributions.

    The distributions are usually acquired via
    ``get_percentiles`` or or ``get_percentiles_from_list``.

    Parameters
    ----------
    data : DataFrame
        The response time data, usually generated by
        ``get_percentiles_from_raw_rts`` or ``get_percentiles_from_dataframe``.
    percentile_index : string, optional
        The name of the the DataFrame index in ``data`` to use when
        plotting. This is only required when ``data`` is a MultiIndex
        DataFrame.
    colors : list, optional
        Desired colors of the elements to plot. The first element of the
        list corresponds to the first column of response times in ``data``,
        the second item to the second column, etc.
    outfile : string, optional
        The output filename to save the plot to. If ``None``, display the
        plots, but do not save them.

    Returns
    -------
    fig
        The matplotlib figure object.

    Notes
    -----
    If ``outfile`` is not supplied, plots will be displayed, but not saved
    to disk.

    See also
    --------
    get_percentiles_from_raw_rts : Generate data in the correct input
        format for this function.

    """

    import matplotlib
    # matplotlib.use() has to be called before importing pyplot.
    if outfile:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    # Larger fonts in plots.
    matplotlib.rcParams.update({'font.size': 22})

    if colors is None:
        color_set = ['#7fc97f', '#beaed4', '#fdc086', '#686665']
        colors = dict()
        for i, modality in enumerate(data.columns):
            colors[modality] = color_set[i]

    if data.index.nlevels == 1:
        index = data.index
    else:
        index = data.index.levels[data.index.names.index(percentile_index)]

    fig = plt.figure(figsize=[12, 8])
    plt.hold(True)
    for modality in data.columns:
        plt.plot(data[modality],
                 index,
                 '--o', label=modality, color=colors[modality],
                 linewidth=3, markersize=10, alpha=0.7)

    plt.yticks(index)
    plt.grid(True)
    plt.title('Response Time Distributions', weight='bold')
    plt.xlabel('RT', weight='bold')
    plt.ylabel('Proportion of Responses', weight='bold')
    plt.legend(loc='lower right')
    plt.tight_layout()

    if outfile:
        try:
            fig.savefig(outfile)
        except IOError:
            raise IOError('Could not save the figure. Please check the '
                          'supplied path.')

    return fig


def ttest(data, left='A', right='B', group_by=None, test_type='t-test'):
    """
    Parameters
    ----------
    data : DataFrame
        The input data.
    left : string
        The name of the column to use as the 'left' side of the test.
    right : string
        The name of the column to use as the 'right' side of the test.
    group_by : string or list of strings, optional
        The names of index or data columns to split the data by before
        running the statistical tests.
        If ``None``, the data will not be split before testing.
    test_type : string, optional
        The statistical test to perform. Currently, valid values are
        ``t-test`` for a pairwise t-test, and ``wilcoxon`` for a Wilcoxon
        signed-rank test.

    Returns
    -------
    results : Series or DataFrame
        A DataFrame containing the test statistic and ``p`` value for
        every percentile.

    Notes
    -----
    A positive test statistic indicates that the 'left' mean is greater
    than the right mean, and vice versa.

    """

    test_types = ['t-test', 'wilcoxon']
    if test_type not in test_types:
        raise TypeError('Please specify a valid test: '
                        't-test, wilcoxon.')

    if (left not in data.columns) or (right not in data.columns):
        raise IndexError('The columns specified for comparison could'
                         'not be found.')

    if test_type == 't-test':
        test_fun = ttest_rel
    elif test_type == 'wilcoxon':
        test_fun = wilcoxon

    if group_by is None:
        statistic, p = test_fun(data[left], data[right])
        results = pd.Series([statistic, p],
                            index=pd.Index(['statistic', 'p-value']))
    else:
        results = data.reset_index().groupby(group_by).apply(
            lambda x: pd.Series(test_fun(x[left], x[right]),
                                index=pd.Index(['statistic',
                                                'p-value']))
        )

    return results
