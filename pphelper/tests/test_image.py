# -*- coding: utf-8 -*-

from pphelper.image import lowpass_filter_image, fft_image
import numpy as np
import pyfftw
import pickle

data_directory = 'pphelper/tests/data/'


# def test_lowpass_filter_image():
#     result = lowpass_filter_image(filename=data_directory + 'tux.png',
#                                   flatten=True)
#     result_expected = np.load(
#         data_directory + 'tux_flattened_lowpass_filtered_sigma_3.npy'
#     )
#     assert np.array_equal(result, result_expected)
#
#
# def test_fft_image():
#     image = np.load(data_directory + 'tux_flattened.npy')
#
#     with open(data_directory + 'fftw3-wisdom.pickle', 'rb') as f:
#         pyfftw.import_wisdom(pickle.load(f))
#     fft, amplitude, phase = fft_image(image)
#
#     fft_expected = np.load(data_directory + 'tux_flattened_fft.npy')
#     amplitude_expected = np.load(
#         data_directory + 'tux_flattened_amplitude.npy'
#     )
#     phase_expected = np.load(data_directory + 'tux_flattened_phase.npy')
#
#     assert np.allclose(fft, fft_expected)
#     assert np.allclose(amplitude, amplitude_expected)
#     assert np.allclose(phase, phase_expected)
