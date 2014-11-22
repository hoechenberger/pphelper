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
 - ``gen_cdfs_from_list`` : Convenience function: Applys ``gen_cdf`` to a list of data sets.
 - ``gen_percentiles`` : Calculate equally spaced percentiles values.
 - ``get_percentiles_from_cdf`` : Get the values (response times) of a cumulative distribution function at the specified percentiles.
 - ``gen_step_fun`` : Generate a step function from a set of observed response times.

"""

from __future__ import division, unicode_literals
import pandas as pd
import numpy as np
import warnings
from scipy.stats import rankdata
from scipy.interpolate import interp1d
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
    DataFrame or Series
        A Series containing the estimated cumulative frequency polygon,
        indexed by the time points in ms.

    See Also
    --------
    get_percentiles_from_cdf

    Notes
    -----
    Response times will be rounded to 1 millisecond.
    The algorithm is heavily adapted from the one described by Ulrich,
    Miller, and Schröter (2007):
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

    """

    # Convert input data to a Series, and round to 1 ms
    rts = pd.Series(rts).round().astype('int')

    if rts.loc[rts < 0].any():
        rts = rts[rts >= 0]
        warnings.warn('At least one supplied response time was '
                      'less than zero and removed before '
                      'estimating the empirical CDF.')

    if t_max is None:
        t_max = rts.max()
    else:
        t_max = int(round(t_max))

    timeline = np.arange(t_max+1)

    # We first sort the RTs from smallest to largest, rank them
    # with the 'maximum' method (i.e. in the case of ties, all ties
    # will receive the highest possible rank), select all unique ranks,
    # and use these to calculate the plotting positions.
    rts_sorted = rts.order()
    p = np.unique(rankdata(rts_sorted, method='max')) / len(rts_sorted)

    # rts_unique are the x values corresponding to our plotting positions.
    rts_unique = rts_sorted.unique()
    rt_min = rts_unique.min()
    rt_max = rts_unique.max()

    # We now calculate the midpoints of the initial plotting positions
    # to use as _new_ plotting positions.
    #
    # The very first midpoint is treated specially to make the following
    # for loop easier to read.
    p_mid = np.empty(rts_unique.shape)
    p_mid[0] = 1/2 * p[0]

    for i in range(len(rts_unique) - 1):
        dp = p[i+1] - p[i]
        p_mid[i+1] = p[i] + 1/2 * dp

    # Finally construct the CDF.
    # All values < min(rts) shall be 0,
    # all values >= max(rts) shall be 1,
    # and all values in-between shall be stepwise linearly interpolated.
    interpolate = interp1d(rts_unique, p_mid, bounds_error=False)

    cdf = np.empty(t_max+1)
    cdf[:rt_min] = 0
    cdf[rt_max:] = 1
    cdf[rt_min:rt_max] = interpolate(range(rt_min, rt_max))

    return pd.Series(cdf, index=pd.Index(timeline, name='t'))


def gen_cdfs_from_list(data, t_max=None, names=None,
                       return_type='dataframe'):
    """
    Estimate the empirical CDFs for a list of arrays.

    The is a convenience function that wraps ``gen_cdf``.

    Parameters
    ----------
    data : list of array_like objects
        A list of raw response time arrays. The RTs do not have to be
        ordered and may contain duplicate values.
    t_max : int, optional
        Up to which time point (in milliseconds) the model should be
        calculated. If not specified, the maximum value of the supplied
        input data will be used.
    return_type : {'dataframe', 'list'}
        The format of the returned object. `dataframe` returns a
        DataFrame, `list` returns a list of `Series`.

    Returns
    -------
    DataFrame or list of Series
        The estimated empirical CDFs as columns of a DataFrame (default)
        or as a list of Series (if `return_type='list'`).

    Raises
    ------
    ValueError
        If the `name` parameter does not have the same lengths as the
        data list.

    See Also
    --------
    gen_cdf, gen_step_fun

    Examples
    --------
    >>> from pphelper.racemodel import gen_cdfs_from_list
    >>> import numpy as np
    >>> RTs = [np.array([234, 238, 240, 240, 243, 243, 245, 251, 254, 256, 259, 270,
     280]), np.array([244, 249, 257, 260, 264, 268, 271, 274, 277, 291])]
    >>> gen_cdfs_from_list(RTs, names=['CondA', 'CondB'])
            CondA     CondB
    t
    0    0.000000  0.000000
    1    0.000000  0.000000
    2    0.000000  0.000000
    3    0.000000  0.000000
    4    0.000000  0.000000
    5    0.000000  0.000000
    6    0.000000  0.000000
    7    0.000000  0.000000
    8    0.000000  0.000000
    9    0.000000  0.000000
    10   0.000000  0.000000
    11   0.000000  0.000000
    12   0.000000  0.000000
    13   0.000000  0.000000
    14   0.000000  0.000000
    15   0.000000  0.000000
    16   0.000000  0.000000
    17   0.000000  0.000000
    18   0.000000  0.000000
    19   0.000000  0.000000
    20   0.000000  0.000000
    21   0.000000  0.000000
    22   0.000000  0.000000
    23   0.000000  0.000000
    24   0.000000  0.000000
    25   0.000000  0.000000
    26   0.000000  0.000000
    27   0.000000  0.000000
    28   0.000000  0.000000
    29   0.000000  0.000000
    ..        ...       ...
    262  0.828671  0.400000
    263  0.835664  0.425000
    264  0.842657  0.450000
    265  0.849650  0.475000
    266  0.856643  0.500000
    267  0.863636  0.525000
    268  0.870629  0.550000
    269  0.877622  0.583333
    270  0.884615  0.616667
    271  0.892308  0.650000
    272  0.900000  0.683333
    273  0.907692  0.716667
    274  0.915385  0.750000
    275  0.923077  0.783333
    276  0.930769  0.816667
    277  0.938462  0.850000
    278  0.946154  0.857143
    279  0.953846  0.864286
    280  1.000000  0.871429
    281  1.000000  0.878571
    282  1.000000  0.885714
    283  1.000000  0.892857
    284  1.000000  0.900000
    285  1.000000  0.907143
    286  1.000000  0.914286
    287  1.000000  0.921429
    288  1.000000  0.928571
    289  1.000000  0.935714
    290  1.000000  0.942857
    291  1.000000  1.000000

    [292 rows x 2 columns]

    """

    if t_max is None:
        t_max = utils.get_max_from_list(data)

    if (names is not None) and (len(data) != len(names)):
        raise ValueError('Please supply a name parameter with the same '
                         'number of elements as your data list.')

    # Contruct the CDFs and assign the correct names to the Series
    # objects. The names will serve as column names of the DataFrame
    # if `return_type='dataframe'`.
    cdfs = [gen_cdf(x, t_max=t_max) for x in data]
    if names is not None:
        for i, cdf in enumerate(cdfs):
            cdfs[i].name = names[i]

    if return_type == 'dataframe':
        results = pd.DataFrame(cdfs).T
    elif return_type == 'list':
        results = cdfs

    return results


def gen_cdfs_from_dataframe(data, rt_column='RT',
                            modality_column='Modality',
                            names=None):
    """
    Create cumulative distribution functions (CDFs) for response time data.

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
    names : list, optional
        A list of length 4, supplying the names of the modalities. The
        first three elements specify the modalities in the input data to
        consider. These three and the fourth argument are also used to
        label the columns in the returned DataFrame.
        If this argument is not supplied, a default list
        ``['A', 'B', 'AB']`` will be used.

    Returns
    -------
    results : DataFrame
        A DataFrame containing the empirical cumulative distribution
        functions generated from the input, one CDF per column. The number
        of columns depends on the number of unique values in the
        `modality_column` or on the `names` argument,

    See Also
    --------
    gen_cdf, gen_cdfs_from_list

    Notes
    -----
    This function internally calls ``gen_cdf``. Please
    see this function to find out about additional optional keyword
    arguments.

    Examples
    --------

    >>> from pphelper.racemodel import gen_cdfs_from_dataframe
    >>> import pandas as pd
    >>> import numpy as np
    >>> data = pd.DataFrame({'RT': np.array([244, 249, 257, 260, 264, 268, 271, 274, 277, 291,
    ... 245, 246, 248, 250, 251, 252, 253, 254, 255, 259, 263, 265, 279, 282, 284, 319,
    ... 234, 238, 240, 240, 243, 243, 245, 251, 254, 256, 259, 270, 280]),
    ... 'Modality': ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x',
    ... 'y', 'y', 'y', 'y', 'y', 'y', 'y', 'y', 'y', 'y', 'y', 'y', 'y', 'y', 'y', 'y',
    ... 'z', 'z', 'z', 'z', 'z', 'z', 'z', 'z', 'z', 'z', 'z', 'z', 'z', ]})
    >>> gen_cdfs_from_dataframe(data)
                x         y  z
    t
    0    0.000000  0.000000  0
    1    0.000000  0.000000  0
    2    0.000000  0.000000  0
    3    0.000000  0.000000  0
    4    0.000000  0.000000  0
    5    0.000000  0.000000  0
    6    0.000000  0.000000  0
    7    0.000000  0.000000  0
    8    0.000000  0.000000  0
    9    0.000000  0.000000  0
    10   0.000000  0.000000  0
    11   0.000000  0.000000  0
    12   0.000000  0.000000  0
    13   0.000000  0.000000  0
    14   0.000000  0.000000  0
    15   0.000000  0.000000  0
    16   0.000000  0.000000  0
    17   0.000000  0.000000  0
    18   0.000000  0.000000  0
    19   0.000000  0.000000  0
    20   0.000000  0.000000  0
    21   0.000000  0.000000  0
    22   0.000000  0.000000  0
    23   0.000000  0.000000  0
    24   0.000000  0.000000  0
    25   0.000000  0.000000  0
    26   0.000000  0.000000  0
    27   0.000000  0.000000  0
    28   0.000000  0.000000  0
    29   0.000000  0.000000  0
    ..        ...       ... ..
    290  0.942857  0.916964  1
    291  1.000000  0.918750  1
    292  1.000000  0.920536  1
    293  1.000000  0.922321  1
    294  1.000000  0.924107  1
    295  1.000000  0.925893  1
    296  1.000000  0.927679  1
    297  1.000000  0.929464  1
    298  1.000000  0.931250  1
    299  1.000000  0.933036  1
    300  1.000000  0.934821  1
    301  1.000000  0.936607  1
    302  1.000000  0.938393  1
    303  1.000000  0.940179  1
    304  1.000000  0.941964  1
    305  1.000000  0.943750  1
    306  1.000000  0.945536  1
    307  1.000000  0.947321  1
    308  1.000000  0.949107  1
    309  1.000000  0.950893  1
    310  1.000000  0.952679  1
    311  1.000000  0.954464  1
    312  1.000000  0.956250  1
    313  1.000000  0.958036  1
    314  1.000000  0.959821  1
    315  1.000000  0.961607  1
    316  1.000000  0.963393  1
    317  1.000000  0.965179  1
    318  1.000000  0.966964  1
    319  1.000000  1.000000  1

    [320 rows x 3 columns]

    """
    if names is None:
        names = data[modality_column].sort(inplace=False).unique()

    if not data[modality_column].isin(names).all():
        raise AssertionError('Could not find specified data.')

    # We construct a list of lists of RTs (one for each modality).
    rts = [data.loc[data[modality_column] == modality, rt_column]
           for modality in names]

    result = gen_cdfs_from_list(rts, names=names, return_type='dataframe')
    return result


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

    Raises
    ------
    TypeError
        If the supplied percentile number could not be converted to a
        rounded integer.

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

    p = np.linspace(0.5 * 1/n, 1 - 0.5*1/n, n)
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

    Raises
    ------
    TypeError
        If the supplied percentile object could not be cast into an array,
        or if the CDF object is not a Series.

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

    See Also
    --------
    gen_cdf, gen_cdfs_from_list

    Examples
    --------
    >>> from pphelper.racemodel import gen_step_fun
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> RTs = np.array([234, 238, 240, 240, 243, 243, 245, 251, 254, 256, 259, 270, 280])
    >>> sf = gen_step_fun(RTs)
    >>> plt.step(sf, sf.index, where='post'); plt.show()

    """
    rts_unique = np.unique(rts)
    rts_sorted = np.sort(rts)
    p = np.unique(rankdata(rts_sorted, method='max')) / len(rts_sorted)

    return pd.Series(rts_unique, pd.Index(p, name='p'))


def sum_cdfs(cdfs):
    """
    Calculate the sum of multiple cumulative distribution functions.

    Parameters
    ----------
    cdfs : list
        A list of CDFs generated with ``gen_cdf``, ``gen_cdfs_from_list``,
        or ``gen_cdfs_from_dataframe``.

    Returns
    -------
    Series
        The sum of the CDFs in the interval [0, 1], indexed by the time in
        milliseconds.

    Raises
    ------
    ValueError
        If the supplied CDFs have unequal lengths.
    IndexError
        If the indices of the supplied CDF Series objects do not match.

    Notes
    -----
    First calculates the sum of the CDFs, and returns the element-wise
    minima `min[(sum, 1)`.

    Examples
    --------
    >>> from pphelper.racemodel import gen_cdfs_from_list, sum_cdfs
    >>> import numpy as np
    >>> RTs = [np.array([234, 238, 240, 240, 243, 243, 245, 251, 254, 256, 259, 270, 280]), np.array([244, 249, 257, 260, 264, 268, 271, 274, 277, 291])]
    >>> cdfs = gen_cdfs_from_list(RTs, names=['A', 'B'])
    >>> sum_cdfs([cdfs['A'], cdfs['B']])
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
    277    1
    278    1
    279    1
    280    1
    281    1
    282    1
    283    1
    284    1
    285    1
    286    1
    287    1
    288    1
    289    1
    290    1
    291    1
    Length: 292, dtype: float64

    """
    cdf_lengths_equal = all([cdf.shape == cdfs[0].shape for cdf in cdfs])
    if not cdf_lengths_equal:
        raise ValueError('Please supply CDFs with equal lengths.')

    cdf_indices_equal = all([cdfs[0].index.equals(cdf.index)
                             for cdf in cdfs])
    if not cdf_indices_equal:
        raise IndexError('Please supply CDFs with equal indices.')

    return np.minimum(pd.DataFrame(cdfs).T.sum(axis=1), 1)
