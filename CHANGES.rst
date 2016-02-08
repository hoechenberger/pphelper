=========
Changelog
=========
****************
v0.6, 2015-xx-xx
****************
- Replace `onset_delay` parameter of `hardware` components with
  `trigger_time`.
- Add gustometer support.
- Add support for trigger generation.
- MultiIndex support in `racemodel.get_percentiles_from_cdf()`
- Switch to Travis-CI container-based infrastructure.
- Fix readthedocs.org documentation creation.

****************
v0.5, 2015-08-17
****************
- ``compare_*`` functions renamed to ``gen_*``.
- ``get_cdf*`` functions renamed to ``get_percentiles*``.
- Add raw data comparison from a DataFrame (``get_percentiles_from_dataframe``).
- Add ``utils`` module.
- Add sum_cdfs() to calculate the sum of an arbitrary number of CDFs.
- Remove plotting functionality.
- gen_cdf() completely reworked to be more readable and faster (>2x).
- Add ``image`` module.
- Add ``sdt`` module with simple d' and criterion calculation.

******************
v0.3.1, 2014-09-01
******************
- Remove ``save`` argument to ``plot_cdfs()``.
- Adapt tests to ``lowercase_underscore`` naming.

****************
v0.3, 2014-08-29
****************
- Add functionality to plot CDFs.
- Improve documentation.
- Switch naming scheme to ``lowercase_underscore``.
- Misc. Refactoring.
- Prepare for PyPI release.

****************
v0.2, 2014-08-15
****************
- Extend documentation.
- Build documentation using Sphinx.
- Various cleanups and small bugfixes.

****************
v0.1, 2014-08-14
****************
- Initial release.
