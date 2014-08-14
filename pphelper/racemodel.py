from __future__ import division
import numpy as np
import pandas as pd


def gen_cdf(responseTimes, tMax=None):
    """
    Estimate the cumulative frequency polygon from response time data.

    Parameters
    ----------
    responseTimes : array_like
        The raw response time data. Data does not need to be ordered and may
        contain duplicate values.
    tMax : int, optional
        Up to which time point (in milliseconds) the model should be calculated.
        If not specified, the maximum value of the supplied input data will be used.

    Returns
    -------
    Series
        A Series containing the estimated cumulative frequency polygon, indexed by
        the time points in ms.

    Examples
    --------
    >> from analysis.racemodel import gen_cdf
    >> import numpy as np
    >> RTs = np.array([234, 238, 240, 240, 243, 243, 245, 251, 254, 256, 259, 270, 280])
    >>> gen_cdf(RTs, tMax=RTs.max())
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

    C = pd.Series(responseTimes)

    if tMax is None:
        tMax = C.max()

    C_sorted = C.order()
    C_unique = C_sorted.unique()

    n = C_sorted.size
    k = C_unique.size

    # Number of occurrences of each element.
    N = C_sorted.value_counts().sort_index()
    s = N.cumsum()

    # Add leading 0 element because our algorithm
    # starts iteration at index 1.
    # This is done to maintain close similarity to the published algorithm.
    C_unique = np.append(0, C_unique)
    s = np.append(0, s)
    N = np.append(0, N)

    result = np.zeros(tMax+1)
    timeline = np.arange(tMax+1)
    i = 1
    for t in timeline:
        if t < C_unique[1]:
            result[t] = 0
        elif t >= C_unique[-1]:
            result[t] = 1
        elif i < k:
            result[t] = 1/n * (s[i-1] + N[i]/2 + (N[i]+N[i+1]) / 2 *
                               (t-C_unique[i]) / (C_unique[i+1]-C_unique[i]))
            if t+1 == C_unique[i+1]:
                i += 1

    return pd.Series(result, index=pd.Index(timeline, name='t'))


def gen_percentiles(n=10):
    """
    Calculate n equally spaced percentiles.

    Parameters
    ----------
    n : int
        The number of percentiles to generate. Defaults to 10.

    Returns
    -------
    p : ndarray
        1-dimensional array of the calculated percentiles.

    """
    p = np.zeros(n)
    for i in range(1, n+1):
        p[i-1] = (i-0.5) / n

    return p


def get_percentiles_from_cdf(G, p):
    """
    Interpolate the percentile boundaries.

    Parameters
    ----------
    G : Series
        The cumulative distribution polygon. Usually generated by `gen_cdf()`.

    p : array_like
        The percentiles for which to get values from the polygon.
        Usually generated by `gen_percentiles()`.

    Returns
    -------
    Series
        Returns a Series of interpolated percentile boundaries (fictive response times).

    """
    p = np.array(p).flatten()
    nPercentiles = p.shape[0]
    CDF = G
    timeline = CDF.index

    percentileBoundaries = np.zeros(len(p))

    i = 0
    for t in timeline:
        # The '< CDF.iloc[t+1]' part is here so the last one of subsequent identical values
        # is picked for inclusion in the current percentile before moving to the next one.
        if (i < nPercentiles) and (CDF.iloc[t] <= p[i] < CDF.iloc[t+1]):
            percentileBoundaries[i] = (p[i] - CDF.iloc[t]) * (t+1 - t) / (CDF.iloc[t+1] - CDF.iloc[t]) + t
            i += 1

    return pd.Series(percentileBoundaries, index=pd.Index(p, name='p'))


def gen_step_fun(C):
    """
    Generate a step function of an observed response time distribution..

    Parameters
    ----------
    C : array_like
        The input data (usually respone times) to generate a step function from.
        Does not have to be ordered and may contain duplicates.

    Returns
    -------
    p : ndarray
        1-dimensional array storing the percentiles, sorted from smallest to largest.
    C_sorted : ndarray
        1-dimensional array storing the corresponding response times.

    """

    # Drop duplicate values
    C_sorted = np.unique(C)
    p = np.arange(1, len(C)+1) / len(C)

    return p, C_sorted


def compare_cdfs_from_raw_rts(RtA, RtB, RtAB, num_percentiles=10):
    """
    Create cumulative distribution functions for response time data and calculate the race model assumptions.

    Parameters
    ----------

    RtA : array_like
        Raw response time data from the first (usually unimodal) condition.
    RtB : array_like
        Raw response time data from the second (usually unimodal) condition.
    RtAB : array_like
        Raw response time data from the third (usually bimodal) condition.
    num_percentiles : scalar
        The number of percentiles to generate from the RT CDFs.

    Returns
    ------
    results : DataFrame
        Returns a DataFrame containing the RTs of every CDF at the generated percentiles.
        The DataFrame contains four columns: 'A', 'B', 'AB' (which correspond to the input
        RtA, RtB, and RtAB, respectively), and 'A+B', which is the hypothetical sum of
        the CDFs generated from RtA and RtB. If 'AB' < 'A+B' at any percentile, the race
        model is violated.

    """

    # Find the maximum response time
    RtMax = np.concatenate([RtA, RtB, RtAB]).max()
    assert RtMax > 0

    # Generate DataFrames from the raw RT input.
    Rt = {'A': pd.Series(RtA),
          'B': pd.Series(RtB),
          'AB': pd.Series(RtAB)}


    # Generate the cumulative distribution functions.
    CDF = dict()
    for key in Rt.keys():
        CDF[key] = gen_cdf(Rt[key], tMax=RtMax)

    # Generate the hypothetical CDF for the no-integration case.
    CDF['A+B'] = CDF['A'] + CDF['B']

    # Generate a set of percentiles for which to assess the RTs from
    # the CDFs.
    percentiles = gen_percentiles(num_percentiles)

    # Now fetch the corresponding values from the CDFs.
    results = pd.DataFrame()
    for key in CDF.keys():
        results[key] = get_percentiles_from_cdf(CDF[key], percentiles)

    # Order DataFrame columns
    results = results[['A', 'B', 'AB', 'A+B']]

    return results