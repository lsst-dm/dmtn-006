..
  Content of technical report.

  See http://docs.lsst.codes/en/latest/development/docs/rst_styleguide.html
  for a guide to reStructuredText writing.

  Do not put the title, authors or other metadata in this document;
  those are automatically added.

  Use the following syntax for sections:

  Sections
  ========

  and

  Subsections
  -----------

  and

  Subsubsections
  ^^^^^^^^^^^^^^

  To add images, add the image file (png, svg or jpeg preferred) to the
  _static/ directory. The reST syntax for adding the image is

  .. figure:: /_static/filename.ext
     :name: fig-label
     :target: http://target.link/url

     Caption text.

   Run: ``make html`` and ``open _build/html/index.html`` to preview your work.
   See the README at https://github.com/lsst-sqre/lsst-report-bootstrap or
   this repo's README for more info.

   Feel free to delete this instructional comment.

:tocdepth: 1

Introduction
============

Detections of image and processing artifacts in image differencing present a
significant challenge to LSST's ability to recover faint moving objects.

Pan-STARRS.

Kessler Example.

Data and Pipeline Processing
============================


False Detections near Bright Stars
==============================

.. figure:: /_static/sec3_star_dia_correlation.png
    :name: star_dia_correlation

    Density of Dia sources near bright stars. (From star_diffim_correlation.ipynb).

.. math::
    \rho / \langle \rho \rangle = 1 + (r/r_{norm})^{-3.5},

.. math::
    r_{norm} = max(13.4 - 4(M - 12), 4) \,\rm{arcsec}

Image Noise Analysis
====================

.. figure:: /_static/sec4_dia_density.png
    :name: dia_density

    Density of dipole and non-dipole Dia sources. The low latitude fields have
    Dia counts greatly above the top of the plot due to the noise issue
    described in (XXX WHERE). The high latitude fields are much more
    consistent.

Comparison of Direct Image Fluxes
---------------------------------

One check on the pipeline noise estimates can be made by taking two overlaping
exposures, crossmatching the detected sources in each, and comparing the
difference in the fluxes measured each time with the reported uncertainties on
those fluxes. The reported uncertainties are derived from each exposure's
variance plane, which is also used for computing the uncertainties on the
difference images.

Figure :ref:`fig-source-err-v197367` shows this analysis performed for a pair of
well-behaved fields at high latitude.

.. figure:: /_static/sec4_source_err_v197367.png
    :name: fig-source-err-v197367

    Difference in measured flux between exposures 197367 and 197371,
    normalized by the reported uncertainity on each measurement. If the
    reported uncertainties are correct, this should form a unit Gaussian,
    however it is better fit by a Gaussian that is 15% wider.

.. figure:: /_static/sec4_source_err_v197662.png
    :name: source_err_v197662

    Difference in measured flux between the low latitude exposures 197662 and
    198668, normalized by the reported uncertainity on each measurement. In
    this comparison the reported uncertainties are significantly smaller than
    the observed scatter in observed fluxes, differing by about 60%.

Conclusions
===========

Appendix A: Data used in this work
==================================


.. table:: Decam visits used in this analysis.

  ======  ==============   =========   ============   ============
   Visit  Template Visit   CCDs        Galactic Lat   Galactic Lon
                           processed
  ======  ==============   =========   ============   ============
  197367          197371          59        56.3311       297.6941
  197375          197371          59        56.3355       298.0934
  197379          197371          59        56.3461       297.6202
  197388          197384          59        46.0518       308.6413
  197392          197384          59        46.0973       308.8498
  197400          197408          59        43.9119       312.3330
  197404          197408          59        43.9128       312.3235
  197412          197408          54        43.8827       312.2617
  197802          197790           7       -22.8796       211.1369
  198380          197790           7       -22.9299       211.1618
  198384          197790           7       -22.8802       211.1440
  198668          197662          47       -34.6799        39.8085
  199009          197662          37       -34.5272        39.9427
  199021          197662          37       -34.5853        40.0062
  199033          197662          23       -34.7855        40.1130
  ======  ==============   =========   ============   ============



