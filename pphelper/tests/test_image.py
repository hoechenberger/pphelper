# -*- coding: utf-8 -*-

from pphelper.image import lowpass_filter_image, fft_image
import numpy as np


def test_lowpass_filter_image():
    result = lowpass_filter_image(filename='data/tux.png', flatten=True)
    result_expected = np.load('data/tux_flattened_lowpass_filtered_sigma_3.npy')

    assert np.array_equal(result, result_expected)


def test_fft_image():
    image = np.load('data/tux_flattened.npy')
    fft, amplitude, phase = fft_image(image)

    fft_expected = np.load('data/tux_flattened_fft.npy')
    amplitude_expected = np.load('data/tux_flattened_amplitude.npy')
    phase_expected = np.load('data/tux_flattened_phase.npy')

    # assert np.array_equal(fft, fft_expected)
    assert np.array_equal(amplitude, amplitude_expected)
    assert np.array_equal(phase, phase_expected)

