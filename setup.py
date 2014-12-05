#!/usr/bin/env python
# encoding: utf-8

import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    raise sys.exit('Could not import setuptools.')

# Ger version info.
# This basically imports __version__ from version.py.
exec(open('pphelper/version.py').read())

setup(
    name='pphelper',
    version=__version__,
    author='Richard Höchenberger',
    author_email='richard.hoechenberger@gmail.com',
    url='https://github.com/hoechenberger/pphelper',
    packages=find_packages(),
    license='GPL v3',
    description='Different helper modules for analysis of psychophysics '
                'experiments.',
    long_description=open('README.rst').read(),
    install_requires=['sphinxcontrib-napoleon', 'psychopy',
                      'pandas >= 0.14.1', 'matplotlib', 'scipy',
                      'numpy >= 1.7.2'],
    classifiers=['Intended Audience :: Science/Research',
                 'Programming Language :: Python',
                 'Topic :: Scientific/Engineering :: Bio-Informatics',
                 'Topic :: Scientific/Engineering :: Information Analysis',
                 'Topic :: Scientific/Engineering :: Medical Science Apps.',
                 'Operating System :: POSIX',
                 'Operating System :: Unix',
                 'Operating System :: MacOS',
                 'Operating System :: Microsoft :: Windows',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4'],
)
