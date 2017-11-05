# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import numpy as np
import pandas as pd
from pphelper.utils import (add_zero_padding, get_max_from_list,
                            join_multi_level_index, find_nearest)


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


def test_join_multi_level_index():
    idx = pd.MultiIndex.from_arrays(
        [['foo_1', 'bar_1', 'baz_1'],
         ['foo_2', 'bar_2', 'baz_2'],
         ['foo_3', 'bar_3', 'baz_3']],
        names=['idx_1', 'idx_2', 'idx_3']
    )

    result_expected = ['foo_1-foo_2-foo_3',
                       'bar_1-bar_2-bar_3',
                       'baz_1-baz_2-baz_3']

    result = join_multi_level_index(idx, sep='-')

    assert result == result_expected


def test_find_nearest():
    a = np.array([1, 2, 3])

    x = 2
    result_expected = 2
    result = find_nearest(a, x)
    assert result == result_expected

    x = 1.3
    result_expected = 1
    result = find_nearest(a, x)
    assert result == result_expected

    x = 2.5
    result_expected = 2
    result = find_nearest(a, x)
    assert result == result_expected


def test_find_nearest_return_index():
    a = np.array([1, 2, 3])

    x = 2
    result_expected = (1, 2)
    result = find_nearest(a, x, return_index=True)
    assert result == result_expected

    x = 1.3
    result_expected = (0, 1)
    result = find_nearest(a, x, return_index=True)
    assert result == result_expected

    x = 2.5
    result_expected = (1, 2)
    result = find_nearest(a, x, return_index=True)
    assert result == result_expected


if __name__ == '__main__':
    import pytest
    pytest.main()
