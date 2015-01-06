# -*- coding: utf-8 -*-

"""
pphelper.image
==================

Provides
--------
 - ``fft_image`` : Perform an FFT on the supplied image array.
 - ``lowpass_filter_image`` : Load an image from a file, and low-pass
                              filter via a Gaussian kernel.

"""

from __future__ import unicode_literals

from collections import namedtuple
import numpy as np
from scipy.misc import imread
from scipy import ndimage
import pyfftw
from pyfftw.interfaces.scipy_fftpack import fft2

# Enable cache for FFTW to speed up calculations
pyfftw.interfaces.cache.enable()
pyfftw.interfaces.cache.set_keepalive_time(60)


def fft_image(image):
    """
    Perform an FFT on the supplied image array.

    Parameters
    ----------
    image : ndarray
        An array of the image

    Returns
    -------
    namedtuple
        A namedtuple containing the the fast-fourier transform, the
        amplitude and phase.

    """
    image_fft = fft2(image)
    image_amplitude = np.abs(image_fft)
    image_phase = np.angle(image_fft)

    result = namedtuple('Image', 'FFT Amplitude Phase')
    return result(image_fft, image_amplitude, image_phase)


def lowpass_filter_image(image=None, filename=None, flatten=False,
                         sigma=3):
    """
    Load an image from a file, and low-pass filter via a Gaussian kernel.

    Parameters
    ----------
    image : ndarray, optional
        The image to be processed. This will usually have been created
        using `scipy.misc.imread` or a similar function.
        If this argument is present, `filename` will be ignored.

    filename : string, optional
        The name of the image file to load and process.
        Will be ignored is `image_array` is not `None`.

    flatten : bool, optional
        Whether to "flatten" the image before filtering,
        i.e. convert it to grayscale.

    sigma : scalar, optional
        The standard deviation for Gaussian kernel.
        See `scipy.ndimage.filters.gaussian_filter`.

    Returns
    -------
    ndarray
        The lowpass-filtered image.

    See Also
    --------
    scipy.ndimage.gaussian_filter

    """
    if (image is None) and (filename is None):
        raise AttributeError('Please supply either an image array or an'
                             'image filename in lowpass_filter_image().')

    if image is None:
        image = imread(filename, flatten=flatten)

    return ndimage.gaussian_filter(image, sigma)
