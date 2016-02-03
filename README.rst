###########################################################################
DMTN-006 False Positive Rates in the LSST Image Differencing Pipeline
###########################################################################

An analysis of the false positives in Decam imaging data processed by the LSST pipeline.

View this technote at http://dmtn-006.lsst.io or see a preview of the
current version in `this repo`_

.. _this repo: ./index.rst



Contents
========

In addition to the technical note text, several components of the code used for this analysis are also included in this repository. They are

* ``python/diasource_mosaic.py`` - Creates a mosaic of postage stamp images (showing science, template, and difference images) for all DIA source detections.
* ``python/forcePhotDiaSources.py`` - This script is used to measure force photometry on the science and template images at the locations of all DIA sources detected by the stack's ``imageDifference.py``.
* ``notebooks/forced_photometry.ipynb`` - This notebook performs the analysis of the force photometry output.
* ``notebooks/forced_phot_sql.ipynb`` - This version of the analysis is better equipped for working on all of the fields at once.
* ``notebooks/noise_analysis.ipynb`` - Analysis of the per-pixel noise estimates in the direct (science and template) Decam images.

..
  Uncomment this section and modify the DOI strings to include a Zenodo DOI badge in the README
  .. image:: https://zenodo.org/badge/doi/10.5281/zenodo.#####.svg
     :target: http://dx.doi.org/10.5281/zenodo.#####

Build this technical note
=========================

You can clone this repository and build the technote locally with `Sphinx`_

.. code-block:: bash

   git clone https://github.com/lsst-dm/dmtn-006
   cd dmtn-006
   pip install -r requirements.txt
   make html

The built technote is located at ``_build/html/index.html``.

****

Copyright 2016 AURA/LSST

This work is licensed under the Creative Commons Attribution 4.0 International License. To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/.

.. _Sphinx: http://sphinx-doc.org
