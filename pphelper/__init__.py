# -*- coding: utf-8 -*-

"""
    pphelper is a collection of tools that can be used for the analysis of
    psychophysical data.

"""

from .version import __version__
from . import racemodel, hardware

__all__ = ['racemodel', 'hardware', 'utils']
