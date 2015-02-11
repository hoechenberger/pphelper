# -*- coding: utf-8 -*-

"""
    pphelper is a collection of tools that can be used for the analysis of
    psychophysical data.

"""
from __future__ import print_function, unicode_literals

from .version import __version__
from . import racemodel, utils, image
try:
    import nidaqmx as _nidaqmx
except ImportError:
    print('Problem importing the hardware module, skipping.\n'
          'Please check if PyLibNIDAQmx is installed.')

__all__ = ['racemodel', 'sdt', 'hardware', 'utils', 'image']
