..
  See http://docs.lsst.codes/en/latest/development/docs/rst_styleguide.html
  for a guide to reStructuredText writing.

  To add images, add the image file (png, svg or jpeg preferred) to the
  _static/ directory. The reST syntax for adding the image is

  .. figure:: /_static/filename.ext
     :name: fig-label
     :target: http://target.link/url

     Caption text.

   Run: ``make html`` and ``open _build/html/index.html`` to preview your work.
   See the README at https://github.com/lsst-sqre/lsst-report-bootstrap or
   this repo's README for more info.


:tocdepth: 1

Introduction
============

Detections of image and processing artifacts in image differencing present a
significant challenge to LSST's recovery of faint moving objects. To identify
solar system objects, the moving objects pipeline must be able to link
multiple detections of the same object over a time baseline of (XXX how long?)
to measure a candidate orbit. This process involves a computationally-
intensive testing many plausible combinations of sources in the difference
images (referred to as "DIA sources" for "Difference Image Analysis") to
distinguish which sets of detections ("tracks", or "tracklets") describe a
physical orbit.

The longer this baseline grows between repeat detections of an object, the
larger the area that must be searched grows. This may remain computationally
tractable if the number of candidate detections that must be tested is small,
but can quickly become infeasible if the density of candidates is large.
Previous searches for solar system objects have found that the vast majority
of their candidate detections are caused by imaging or processing artifacts,
rather than real solar system objects. In the case of Pan-STARRS, the cadence
had to be modified to include repeat visits of a field within a single night,
shrinking the time baseline and thus the search space (CITE). The Dark Energy
Survey, while mainly searching for transients rather than moving solar system
objects, employed machine learning algorithms to exclude detections that were
unlikely to be physical (CITE Kessler).

The goal of this study is to quantify the expected rate of false positive
detections in LSST, using the LSST image differencing pipeline run on
observations taken with Decam. This false positive rate can then be used in
subsequent works to assess the recovery rates of solar system objects under
differing candidate observing cadences. The Decam CCDs are reasonable analogs
of the sensors that will be used in LSST, significantly more so than the Pan-
STARRS orthogonal transfer arrays. Producing clean difference images is a
serious software challenge. As described in several LSST reports (Becker et
al. Winter 2013 report, CITES) and published works (Alard & Lupton, Zackay,
etc), the convolution process required to match the point spread functions of
the two images (PSFs) introduces correlated noise which complicates detection.
Improved algorithms for image subtraction are still an active area of research
(Zackay 2015). Our objective is to characterize the performance of the current
pipeline with the understanding that it may be improved in the time leading up
to the start of operations.

XXX: Need to be quantitative about time baselines for recovery.


Data and Pipeline Processing
============================

The observations used in this work were part of a near earth object (NEO)
search program conducted in 2013 (Program 2013A-724, PI: L. Allen). The data
are publicly available in the NOAO archive, and a table of the individual
exposures used can be found in :ref:`Appendix A <appendix-a>`. These exposures
are a small subset of the full observing program. The full set of exposures
was divided into five bands in absolute Galactic latitude, a single field in
each range was randomly chosen and all observations of that field were
downloaded. The input to the LSST pipeline were "InstCal" files for which
instrumental signature removal (ISR) had been applied by the NOAO Community
Pipeline. This stage of processing is very instrument-specific and the LSST
pipeline had only a limited ability to apply ISR to Decam images at the time.

The LSST pipeline was used to background subtract the images, compute the PSF,
and perform photometry (all conducted by ``processCcdDecam.py``). Astrometric
calibration was provided by the Community Pipeline values; we did not re-fit
the astrometry [#TPV]_. In each field one image was selected to serve as the
"template" against which all other observations in that field would be
differenced. This was done by ``imageDifference.py``, which computed the
matching kernel, convolved and warped the template to match the non-template
exposure and performed the subtraction. Existing default settings were used
throughout. Source detection was performed at the :math:`5.0\sigma` level.
Dipole fitting and PSF photometry was performed on all detections.

A set of postage stamps showing Dia source detections are shown in
:numref:`fig-diasource-mosaic`. The appearance of these is quite varied. Some are
clearly the result of poorly subtracted stars, and show both positive and
negative artifacts. The dipole fitting code in the LSST pipeline attempts to
fit both negative and positive components to a detection, and then flags
sources as dipoles if the the absolute value of the flux in both components is
similar (neither component holds more than 65% of the total flux). Detections
where this flag is set have been marked "Dipole" on the left side of the
postage stamps, and one can see that this successfully identifies many of the
bright stars with failed subtractions.

Many of the other detections show no apparent source at all in the original
images, and the presence of a flux overdensity or underdensity is barely
perceptible by eye. Some of these detections could simply be noise excursions
that happen to exceed the :math:`5.0\sigma` detection threshold. However they
could also be real detections of particularly faint objects, and thus it is
critical to understand the origin of these detections.

.. figure:: /_static/diasource_mosaic_visit197367_ccd10_5.png
    :name: fig-diasource-mosaic

    Example postage stamps of Dia sources in visit 197367. For each triplet of
    images, the left image is the template, the center image is the science
    exposure, and the right image is the difference. Many of these result from
    poor subtractions of bright stars, but many are in areas that appear
    empty.




.. figure:: /_static/sec4_dia_density.png
    :name: dia_density

    Density of dipole and non-dipole Dia sources. The low latitude fields have
    Dia counts greatly above the top of the plot due to the noise issue
    described in (XXX WHERE). The high latitude fields are much more
    consistent.

.. [#TPV] We tested the processing both with and without the astrometric
    distortion terms provided by the Community Pipeline and did not see a significant
    difference in the numbers of Dia source detections.


..
  Image Noise Analysis
  ====================

Direct Image Noise Analysis
========================================

One check on the pipeline noise estimates can be made by taking two overlapping
exposures, crossmatching the detected sources in each, and comparing the
difference in the fluxes measured each time with the reported uncertainties on
those fluxes. This test is independent of any of image differencing. The
reported uncertainties are derived from each exposure's variance plane, which
is also used for computing the uncertainties on the difference images.

:numref:`fig-source-err-v197367` shows this analysis performed for a pair of
well-behaved fields at high latitude. The scatter in the measured fluxes is
about 15% wider than the pipeline uncertainties report. While this is enough
to account for ~300 detections at :math:`5.5\sigma` per square degree, that
still falls fall short of the actual detection numbers we see in the high
latitude images.

.. figure:: /_static/sec4_source_err_v197367.png
    :name: fig-source-err-v197367

    Difference in measured flux between exposures 197367 and 197371,
    normalized by the reported uncertainty on each measurement. If the
    reported uncertainties are correct, this should form a unit Gaussian,
    however it is better fit by a Gaussian that is 15% wider.

The same analysis for one of the low-latitude fields, visit 197662, is shown
in :numref:`source_err_v197662`. In this image the variance plane
underestimates the scatter in the photometry by approximately 60%. This will
certainly lead to an order of magnitude excess of detections, and we do not
investigate these fields further.

.. figure:: /_static/sec4_source_err_v197662.png
    :name: source_err_v197662

    Difference in measured flux between the low latitude exposures 197662 and
    198668, normalized by the reported uncertainty on each measurement. In
    this comparison the reported uncertainties are significantly smaller than
    the observed scatter in observed fluxes, differing by about 60%.


.. figure:: /_static/sec4_force_random_phot_v197367.png
    :name: fig-force-random-phot

    Force photometry on random locations in the difference image. This
    measures the noise on the same size scale as the PSF. The reported
    uncertainties are about 15% smaller than the observed scatter. This is
    consistent with propagating the variance plane provided by the Community
    Pipeline.



Noise in Difference Images
===========================

After fixing the initial mis-estimates of the noise in the direct images, we
can make a closer examination of the remaining difference image detections. A
particularly useful tool for isolating the effects of the differencing
pipeline from effects in the original direct images is to perform force
photometry (fitting a PSF source amplitude at a fixed position) in the direct
images at the location of all DIA sources. A diagram showing the results from
this for a single CCD is shown in :numref:`forcephot_sci_template_v197367`,
and a schematic explanation of some of the features in this diagram is shown
in :numref:`forcephot_conceptual`. :numref:`forcephot_table` lists the number
of sources in each category for a single field (visit 197367).

The majority of all DIA sources in this field are detections that do not
exceed :math:`5\sigma` in either the science image or the template image, but
are the sum of a weak negative fluctuation in the template plus a weak
positive fluctuation in the science image (or vice-versa, for negative
detections). We believe that these are almost entirely noise effects; real
detections in one image should not depend on the flux in the other image.


.. figure:: /_static/forcephot_sci_template_v197367.png
    :name: forcephot_sci_template_v197367

    PSF photometry in the template and science exposures, forced on the
    positions of DIA source detections. A schematic illustration of this plot
    is also shown in :numref:`forcephot_conceptual`. The parallel diagonal
    lines denote :math:`\rm{science} - \rm{template} > 5\sigma` and
    :math:`\rm{science} - \rm{template} < -5 \sigma`, which are the effective
    criteria for detection. Sources inside those lines are incidental
    photometry failures.  Sources inside the square box do not exceed
    :math:`5\sigma` in either direct image, and are primarily noise.
    Detections of true moving objects are expected to appear above
    :math:`5\sigma` in one image but close to zero flux in the other image.
    Stars which are present in both images but vary in flux will appear in the
    top right.

.. figure:: /_static/forcephot_conceptual.png
    :name: forcephot_conceptual

    Conceptual sketch of the different regions of the force photometry diagram
    (:numref:`forcephot_sci_template_v197367`). Most "noise" detections
    are less than :math:`5\sigma` detections in both science and template
    images, but their combined flux after differencing exceeds
    :math:`5\sigma`. Most true moving objects should instead be
    :math:`>5\sigma` detections in either the science or template image, and
    the flux in the other image should be close to zero. Additionally, stars
    with a flux difference greater than :math:`5\sigma` between the two images
    (labeled "Variables" as a shorthand) will appear in the top right, since
    they have significant flux in both images. The diagonal region crossing
    the center of the image should be unpopulated, but incidental photometry
    failures may appear there.


.. table:: Source counts for visit 197367
  :name: forcephot_table

  +-----------------+------------------------------+--------------------------+
  | Source type     | Counts per Decam focal plane | Counts per square degree |
  +=================+==============================+==========================+
  | Positive noise  |  6572                        |  2590                    |
  +-----------------+------------------------------+--------------------------+
  | Negative noise  |  7519                        |  2963                    |
  +-----------------+------------------------------+--------------------------+
  | Positive real   |  850                         |  335                     |
  +-----------------+------------------------------+--------------------------+
  | Negative real   |  968                         |  381                     |
  +-----------------+------------------------------+--------------------------+
  | "Variables"     |  2791                        |  1100                    |
  +-----------------+------------------------------+--------------------------+
  | Dipoles         |  2764                        |  1189                    |
  +-----------------+------------------------------+--------------------------+


Detection Threshold Estimation
---------------------------------

If we look at only the numbers of "noise" sources, where the DIA source has
less than :math:`5\sigma` significance in either science or template images,
the number of detections per square degree are several orders of magnitude
greater than expected from Gaussian noise. For an image with PSF width
:math:`\sigma_g`, the density of detections above a threshold :math:`\nu` is

.. math::
  n(> \nu) = \frac{1}{2^{5/2} \pi^{3/2}} \nu e^{-\nu^2/2},

where the total number per image is

.. math::
  N_{\rm total}(> \nu) = n(> \nu) \times \rm{nrows} \times \rm{ncol} / \sigma_g.

This expectation is described in Kaiser (2004) and Becker et al. (2013). For
the Decam images with seeing of :math:`\sigma_g = 1.8` pixels and 2k by 4k
pixel sensor, we expect 1.5 noise detections per sensor  at :math:`5\sigma` or
33 detections per square degree (twice that if counting both positive and
negative detections). The current rate we measure is 100 times this. This
suggests that some substantial quantity of artifact (either in the original
images or introduced by the LSST software) are present, or that the pipeline's
estimate of the threshold for detection is incorrect.

There is some evidence to suggest that the latter is the dominant effect. If
the pipeline underestimates the variance in the difference images, then what
we call ":math:`5\sigma`" will not correspond to our actual intended detection
threshold. This true for the direct images as well, but for the difference
images the problem of tracking the variance becomes much more difficult due to
the convolution steps (Price & Magnier 2004, Becker et al. 2013).
:numref:`forcephot_hists` illustrates this error estimation problem. The panel
on the left shows a histogram of the the signal to noise ratio from force
photometry on the two input images. This uncertainty estimate involves no
image differencing code and should be accurate. The panel on the right shows
the pipeline's reported signal to noise ratio as measured on the difference
image, where the difference image variance plane is used to estimate the
uncertainty. It is clear that the pipeline reports that its detections are
substantially more significant than our direct image estimates. This is
entirely due to differences in the reported uncertainties. The ratio of the
difference image uncertainty to the sum of the direct image uncertainties is
between 0.8 and 0.85 for nearly all sources in this image, as seen in
:numref:`forcephot_sigma_ratio`.


.. figure:: /_static/forcephot_hists.png
    :name: forcephot_hists

.. figure:: /_static/forcephot_sigma_ratio.png
    :name: forcephot_sigma_ratio




Detections near Bright Stars
=============================

XXX: This section has not been updated to account for the updated analysis in the previous sections.

.. figure:: /_static/sec3_star_dia_correlation.png
    :name: star_dia_correlation

    Density of Dia sources near bright stars. (From star_diffim_correlation.ipynb).

.. math::
    \rho / \langle \rho \rangle = 1 + (r/r_{norm})^{-3.5},

.. math::
    r_{norm} = max(13.4 - 4(M - 12), 4) \,\rm{arcsec}

Conclusions
===========

.. _appendix-a:

Appendix A: Data used in this work
==================================

XXX: Instcals

XXX: Stack versions? Configuration settings.


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



