# -*- coding: utf-8 -*-

from __future__ import division
import numpy as np
from pphelper.sdt import d_prime, criterion


def test_d_prime():
    hits = 20
    fas = 10
    n = 25

    result_expected = 1.094968336708714
    result = d_prime(hits, fas, n)
    assert np.allclose(result, result_expected)


def test_d_prime_hit_rate_1():
    hits = 25
    fas = 10
    n = 25

    result_expected = 2.3133060087056823
    result = d_prime(hits, fas, n)
    assert np.allclose(result, result_expected)


def test_d_prime_hit_rate_0():
    hits = 0
    fas = 10
    n = 25

    result_expected = -1.8264976530844206
    result = d_prime(hits, fas, n)
    assert np.allclose(result, result_expected)


def test_d_prime_fa_rate_1():
    hits = 20
    fas = 25
    n = 25

    result_expected = -1.2688073016131012
    result = d_prime(hits, fas, n)
    assert np.allclose(result, result_expected)


def test_d_prime_fa_rate_0():
    hits = 20
    fas = 0
    n = 25

    result_expected = 2.8709963601770019
    result = d_prime(hits, fas, n)
    assert np.allclose(result, result_expected)


def test_a_prime():
    hits = 20
    fas = 10
    n = 25

    result_expected = 0.79166666666666674
    result = d_prime(hits, fas, n)
    assert np.allclose(result, result_expected)


def test_criterion_loose():
    hits = 20
    fas = 10
    n = 25

    result_expected = -0.29413706521855731
    result = criterion(hits, fas, n)
    assert np.allclose(result, result_expected)


def test_criterion_strict():
    hits = 10
    fas = 2
    n = 25

    result_expected = 0.82920933172271627
    result = criterion(hits, fas, n)
    assert np.allclose(result, result_expected)


if __name__=='__main__':
    import pytest
    pytest.main()
