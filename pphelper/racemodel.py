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
 - ``gen_cdfs_from_raw_rts`` : Assess cumulative distribution functions from response time data and calculate the race model assumptions.
 - ``gen_cdfs_from_dataframe`` : Assess cumulative distribution functions from response time data and calculate the race model assumptions.
 - ``gen_cdf`` : Estimate the cumulative distribution function from response time data.
 - ``gen_percentiles`` : Calculate equally spaced percentiles values.
 - ``gen_step_fun`` : Generate a step function from a set of observed response times.
 - ``get_percentiles_from_cdf`` : Get the values (response times) of a cumulative distribution function at the specified percentiles.
 - ``calculate_statistics`` : Perform statistical tests.

"""

from __future__ import division, unicode_literals
import pandas as pd
import numpy as np
from scipy.stats import ttest_rel, wilcoxon


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
    # n == n_sorted
    # k == n_unique
    # N == rt_count
    # s == rt_cumsum

    rts_sorted = rts.order()
    rts_unique = rts_sorted.unique()

    n_sorted = rts_sorted.size
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
            result[t] = 1/n_sorted * \
                (rt_cumsum[i-1] + rt_count[i]/2 +
                 (rt_count[i] + rt_count[i+1]) / 2 *
                 (t - rts_unique[i]) /
                 (rts_unique[i+1] - rts_unique[i]))

            if t+1 == rts_unique[i+1]:
                i += 1

    return pd.Series(result, index=pd.Index(timeline, name='t'))


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


def gen_cdfs_from_raw_rts(rt_a, rt_b, rt_ab, num_percentiles=10,
                          percentiles=None, names=None):
    """
    Create cumulative distribution functions (CDFs) for response time data
    and calculate the race model assumptions.

    Parameters
    ----------

    rt_a : array_like
           Raw response time data from the first (usually unimodal)
           condition.
    rt_b : array_like
           Raw response time data from the second (usually unimodal)
           condition.
    rt_ab : array_like
            Raw response time data from the third (usually bimodal)
            condition.
    num_percentiles : scalar, optional
        The number of percentiles to generate from the response time CDFs.
        Will be ignored if ``percentiles`` is supplied.
    percentiles : array_like, optional
        The percentiles for which to get values from the response time
        CDFs. If this argument is supplied, ``num_percentiles`` will be
        ignored.
    names : list, optional
        A list of length 4, supplying the column names which should be
        used in the output data frame. The first element corresponds to
        ``rt_a``, the second to ``rt_b``, the third to ``rt_ab``, and the
        fourth to the calculated hypothetical sum of the CDFs of ``rt_a``
        and ``rt_b``. If this argument is not supplied, a default list
        ``['A', 'B', 'AB', 'A+B']`` will be used.

    Returns
    -------
    results : DataFrame
        A DataFrame containing the response times extracted from every CDF
        at the specified (or generated) percentiles. The DataFrame contains
        four columns. The column names are either those supplied via the
        ``names`` argument, or the default values ``A``, ``B``, ``AB``,
        and ``AB``.
        The first three columns correspond to the input data ``rt_a``,
        ``rt_b``, and ``rt_ab``, respectively). The fourth column contains
        the sum of the CDFs generated from ``rt_a`` and ``rt_b``, i.e. the
        hypothetically fastest no-integration case.
        If, at any percentile, a value in the third column is less than the
        corresponding value value in the fourth, the race model is
        violated.

    Examples
    --------
    >>> from pphelper import racemodel
    >>> import numpy as np
    >>> C = {'x': np.array([244, 249, 257, 260, 264, 268, 271, 274, 277, 291]),
    ... 'y': np.array([245, 246, 248, 250, 251, 252, 253, 254, 255, 259, 263, 265, 279, 282, 284, 319]),
    ... 'z': np.array([234, 238, 240, 240, 243, 243, 245, 251, 254, 256, 259, 270, 280])}
    >>> racemodel.gen_cdfs_from_raw_rts(C['x'], C['y'], C['z'])
                A      B          AB         A+B
    p
    0.05  244.000  245.3  234.600000  244.000000
    0.15  249.000  247.8  238.600000  245.590909
    0.25  257.000  250.5  240.375000  247.292683
    0.35  260.000  252.1  242.325000  249.285714
    0.45  264.000  253.7  244.133333  250.916667
    0.55  268.000  256.2  248.900000  252.250000
    0.65  271.000  262.6  253.850000  253.583333
    0.75  274.000  272.0  256.750000  254.916667
    0.85  277.000  282.2  265.050000  257.765957
    0.95  290.125  308.5  278.500000  259.808511

    Notes
    -----
    If the ``names`` argument is not supplied, a default list
    ``['A', 'B', 'AB', 'A+B']`` will be used.

    """

    # If no percentile object was supplied, generate a set of percentiles
    # for which to assess the RTs from
    # the CDFs.
    if percentiles is None:
        percentiles = gen_percentiles(num_percentiles)
    # If however we got a percentile object, try to convert it into a
    # Numpy array.
    else:
        try:
            percentiles = np.array(percentiles)
        except ValueError:
            raise ValueError('Please supply an array-like  percentile '
                             'object.')

    if names is None:
        names = ['A', 'B', 'AB', 'A+B']
    else:
        try:
            names = list(names)
        except ValueError:
            raise ValueError('Please supply the column names as a list '
                             'in gen_cdfs_from_raw_rts().')

    # Find the maximum response time
    rt_max = np.nanmax(np.concatenate([rt_a, rt_b, rt_ab]))
    assert rt_max > 0

    # Generate DataFrames from the raw RT input and drop NaN values.
    rt = {names[0]: pd.Series(rt_a).dropna(),
          names[1]: pd.Series(rt_b).dropna(),
          names[2]: pd.Series(rt_ab).dropna()}

    # Generate the cumulative distribution functions.
    cdf = dict()
    for name in rt.keys():
        cdf[name] = gen_cdf(rt[name], t_max=rt_max)

    # Generate the hypothetical CDF for the no-integration case.
    cdf[names[3]] = cdf[names[0]] + cdf[names[1]]

    # Now fetch the corresponding values from the CDFs.
    results = pd.DataFrame()
    for name in cdf.keys():
        results[name] = get_percentiles_from_cdf(cdf[name], percentiles)

    # Order columns
    results = results[names]

    return results


def plot_cdfs(data, percentile_index='p', colors=None, outfile=None):
    """
    Plot the response time distributions.

    The distributions are usually acquired via
    ``gen_cdfs_from_raw_rts`` or or ``gen_cdfs_from_dataframe``.

    Parameters
    ----------
    data : DataFrame
        The response time data, usually generated by
        ``gen_cdfs_from_raw_rts`` or ``gen_cdfs_from_dataframe``.
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
    gen_cdfs_from_raw_rts : Generate data in the correct input
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


def gen_cdfs_from_dataframe(data, rt_column='RT',
                            modality_column='Modality',
                            num_percentiles=10, percentiles=None,
                            names=None):
    """
    Create cumulative distribution functions (CDFs) for response time data
    and calculate the race model assumptions.

    Parameters
    ----------

    data : DataFrame
        A DataFrame with containing at least two columns: one with response
        times, and another one specifying the corresponding modalities.
    rt_column : string, optional
        The name of the column containing the response times. Defaults
        to ``RT``.
    modality_column : string, optional
        The name of the column containing the modalities corresponding
        to the response times. Defaults to ``Modality``.
    num_percentiles : scalar, optional
        The number of percentiles to generate from the response time CDFs.
        Will be ignored if ``percentiles`` is supplied.
    percentiles : array_like, optional
        The percentiles for which to get values from the response time
        CDFs. If this argument is supplied, ``num_percentiles`` will be
        ignored.
    names : list, optional
        A list of length 4, supplying the names of the modalities. The
        first three elements specify the modalities in the input data to
        consider. These three and the fourth argument are also used to
        label the columns in the returned DataFrame.
        If this argument is not supplied, a default list
        ``['A', 'B', 'AB', 'A+B']`` will be used.

    Returns
    -------
    results : DataFrame
        A DataFrame containing the response times extracted from every CDF
        at the specified (or generated) percentiles. The DataFrame contains
        four columns. The column names are either those supplied via the
        ``names`` argument, or the default values ``A``, ``B``, ``AB``,
        and ``AB``.
        The first three columns correspond to the input data ``rt_a``,
        ``rt_b``, and ``rt_ab``, respectively). The fourth column contains
        the sum of the CDFs generated from ``rt_a`` and ``rt_b``, i.e. the
        hypothetically fastest no-integration case.
        If, at any percentile, a value in the third column is less than the
        corresponding value value in the fourth, the race model is
        violated.

    Notes
    -----
    This function internally calls ``gen_cdfs_from_raw_rts``. Please
    see this function to find out about additional optional keyword
    arguments.

    See Also
    --------
    gen_cdfs_from_raw_rts

    """

    # If no percentile object was supplied, generate a set of percentiles
    # for which to assess the RTs from
    # the CDFs.
    if percentiles is None:
        percentiles = gen_percentiles(num_percentiles)
    # If however we got a percentile object, try to convert it into a
    # Numpy array.
    else:
        try:
            percentiles = np.array(percentiles)
        except ValueError:
            raise ValueError('Please supply an array-like  percentile '
                             'object.')

    if names is None:
        names = ['A', 'B', 'AB', 'A+B']

    # FIXME
    # Actually we should:
    #   o filter the DataFrame so that the modality_colum only
    #     contains elements supplied in the names array
    #   o then check if all names are can actually be found in
    #     that column
    #   o only if that fails, raise the 'Could not find specified data'
    #     error.
    #
    # Right now, the user cannot use this function if it is supposed to
    # operate only on a subset of the data.
    #
    # When implementing this, also check whether the data object needs to
    # be copied first -- we don't want to cause side-effects!
    if not data[modality_column].isin(names[:-1]).all():
        raise AssertionError('Could not find specified data.')

    rt_a = data.loc[data[modality_column] == names[0], rt_column]
    rt_b = data.loc[data[modality_column] == names[1], rt_column]
    rt_ab = data.loc[data[modality_column] == names[2], rt_column]

    result = gen_cdfs_from_raw_rts(rt_a, rt_b, rt_ab,
                                   num_percentiles=num_percentiles,
                                   percentiles=percentiles,
                                   names=names)

    return result[names]


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
