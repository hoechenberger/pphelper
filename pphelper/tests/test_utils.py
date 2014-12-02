# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import numpy as np
import pandas as pd
from pphelper.utils import (add_zero_padding, get_max_from_list,
                            bootstrap_ci)

def test_add_zero_padding_no_args():
    participants = range(1, 6)
    expected_result = pd.Series(['001', '002', '003', '004', '005'])
    result = add_zero_padding(participants)
    assert result.equals(expected_result)
    assert result.index.equals(expected_result.index)


def test_add_zero_padding_no_series():
    participants = range(1, 6)
    expected_result = pd.Series(['001', '002', '003', '004', '005'])
    result = add_zero_padding(participants, return_series=False)
    assert np.array_equal(result, expected_result)


def test_add_zero_padding_length_arg():
    participants = range(1, 6)
    expected_result = pd.Series(['01', '02', '03', '04', '05'])
    result = add_zero_padding(participants, length=2)
    assert result.equals(expected_result)
    assert result.index.equals(expected_result.index)


def test_add_zero_padding_length_too_short():
    participants = range(100, 106)
    expected_result = pd.Series(['100', '101', '102', '103', '104', '105'])
    result = add_zero_padding(participants, length=2)
    assert result.equals(expected_result)
    assert result.index.equals(expected_result.index)


def test_get_max_from_list():
    data = [range(10),
            range(1, 50),
            range(3, 5)]

    result_expected = 49
    result = get_max_from_list(data)

    assert result == result_expected


def test_bootstrap():
    np.random.seed(12345)
    data = np.concatenate(
        [np.random.normal(3, 1, 100),
         np.random.normal(6, 2, 200)]
    )

    ci_low_expected, ci_high_expected = 4.6, 5.1
    ci_low, ci_high = bootstrap_ci(
        data, n_samples=100000, alpha=0.05
    )

    assert np.round(ci_low, decimals=1) == ci_low_expected
    assert np.round(ci_high, decimals=1) == ci_high_expected


if __name__ == '__main__':
    import pytest
    pytest.main()
