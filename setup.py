#!/usr/bin/env python
# encoding: utf-8

import sys

try:
    from setuptools import setup
except ImportError:
    raise sys.exit('Could not import setuptools.')

# Ger version info.
exec(open('pphelper/version.py').read())

setup(
    name='pphelper',
    version=__version__,
    author='Richard Höchenberger',
    author_email='richard.hoechenberger@gmail.com',
    url='https://github.com/hoechenberger/pphelper',
    packages=['pphelper', 'pphelper.tests'],
    license='GPL v3',
    description='Different helper modules for analysis of psychophysics experiments.',
    long_description=open('README.rst').read(),
    install_requires=['pandas >= 0.14.1', 'numpy >= 1.7.2'],
)
