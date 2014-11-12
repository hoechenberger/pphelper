# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import numpy as np
import pandas as pd
from pphelper.utils import add_zero_padding, get_max_from_list


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
