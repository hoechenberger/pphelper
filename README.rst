|travis-ci|_


========
pphelper
========

``pphelper`` is a collection of tools I use for acquisition and
analysis of psychophysical data in our laboratory.

*******
Modules
*******

racemodel
=========
Race model inequality analysis implementation,
based on Ulrich, Miller, and Schröter (2007):
Testing the race model inequality: An algorithm and computer programs.
*Behavior Research Methods* 39(2), pp. 291-302.

image
=====
FFT and lowpass filtering.

sdt
===
Calculate *d', A',* and *C*.

hardware
========
Interfaces for:

- Burghart GU002 gustometer
- ValveLink-controlled olfactometers,
- analog data acquisition.

All interfaces depend on a National Instruments data-acquisition board.

utils
=====
Some utilities that make data handling a bit easier.

.. |travis-ci| image:: https://secure.travis-ci.org/hoechenberger/pphelper.png?branch=master
.. _travis-ci: https://travis-ci.org/hoechenberger/pphelper
