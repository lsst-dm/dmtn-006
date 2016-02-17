#!/bin/env python
from __future__ import print_function, division

import os
import numpy as np
import argparse

from astroquery.vizier import Vizier
import astropy.coordinates as coord
import astropy.units as u

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker


Base = declarative_base()
class SourceDetectionCorrelation(Base):
    __tablename__ = "SourceDetectionCorrelations"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    visit = sqlalchemy.Column(sqlalchemy.Integer)
    ccdnum = sqlalchemy.Column(sqlalchemy.Integer)
    source_mag = sqlalchemy.Column(sqlalchemy.Float)
    detection_dists = relationship("DetectionDist")

    def dist_array(self):
        """Returns all of the values of `detection_dists` as an numpy array (in arcseconds).
        """
        return np.array([det.dist for det in self.detection_dists])

    def SNR_array(self):
        return np.array([det.SNR for det in self.detection_dists])

    def __repr__(self):
        fmt_string =  "<SourceDetectionCorrelation(visit='{:d}', ccdnum='{:d}', source_mag='{:.2f}')>"
        return(fmt_string.format(self.visit,
                                 self.ccdnum,
                                 self.source_mag))

class DetectionDist(Base):
    __tablename__ = "DetectionDists"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    source_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('SourceDetectionCorrelations.id'))
    dist = sqlalchemy.Column(sqlalchemy.Float)
    SNR = sqlalchemy.Column(sqlalchemy.Float)

    def __repr__(self):
        return "<DetectionDist(dist={:.4f},SNR={:.2f}')>".format(self.dist)


def compute_shift(catalog_sources, image_sources):
    """Computes a small shift between two input catalogs

    Returns
    -------
    delta_ra : float
        Shift in RA between the catalogs.
    delta_dec : float
        Shift in Dec between the catalogs.
    """

    idx, d2, _ = catalog_sources.match_to_catalog_sky(image_sources)

    all_delta_ra = image_sources[idx].ra - catalog_sources.ra
    all_delta_dec = image_sources[idx].dec - catalog_sources.dec

    delta_ra = np.median(all_delta_ra)
    delta_dec = np.median(all_delta_dec)

    print("Delta ra: {:.2f}".format(delta_ra.to(u.arcsec)))
    print("Delta dec: {:.2f}".format(delta_dec.to(u.arcsec)))

    return delta_ra, delta_dec

def is_edge_object(catalog_sources, image_sources, image_xs, image_ys):
    """Returns True for each catalog source if it is near the edge of a chip

    Since we don't have access to the image WCS without downloading all of the
    images themselves, this instead finds the closest source star (which has
    its pixel coordinates in the catalog entry) to estimate the catalog star's
    position.

    Parameters
    ----------
    catalog_sources : SkyCoord
        The sources to evaluate if they are near the CCD edge.

    image_sources : SkyCoord
        Catalog of sources from the image. Must correspond with `image_xs` and `image_ys`.

    image_xs: array
        Pixel x-coordinate for sources in `image_sources`.

    image_ys: array
        Pixel y-coordinate for sources in `image_sources`.

    """

    idx, d2, _ = catalog_sources.match_to_catalog_sky(image_sources)

    # Objects that are close to the edge of the chip
    # pixelsize is 0.2632 arcsec
    buffer_size = 60/0.2632
    edge_object = (image_xs[idx] < buffer_size) | \
                  (image_xs[idx] > 2025 - buffer_size) | \
                  (image_ys[idx] < buffer_size) | \
                  (image_ys[idx] > 4070 - buffer_size)
    return edge_object

def star_diffim_correlation(visit, ccdnum, butler, sql_session=None, debug=False):
    """Find bright stars in the field and their diffim sources.

    This pulls the UCAC4 catalog from Vizier, centered on the chip center. It
    then selects only UCAC4 stars that are on the chip and away from chip
    edges.

    Since the UCAC4 sources don't quite line up with their corresponding stars
    on the decam images, it finds the nearest source to each UCAC4 star,
    computes the median shift in RA and Dec, then applies that shift to all
    sources. This will fail for any major shift, but accomodates the few
    arcsecond shift that I've seen.

    The shift might be due to processing the images without TPV support.

    After shifting the UCAC sources, it loops through them and finds all
    diffim sources within one arcminute, then if `sql_session` is supplied, it
    adds these distance between the source star and the diffim detection to
    the database.

    """


    try:
        src = butler.get("src", visit=visit, ccdnum=ccdnum, immediate=True)
        diff_src = butler.get("deepDiff_diaSrc", visit=visit, ccdnum=ccdnum, immediate=True)
        diff_force_src = butler.get("forced_src", visit=visit, ccdnum=ccdnum, immediate=True)
    except RuntimeError:
        # It would be nice if we had something more specific than "RuntimeError", but this at least
        # stops us from catching some mapper problems.
        print("Could not load data for visit={:d}, ccdnum={:d}, skipping.".format(visit, ccdnum))
        return

    center_ra = np.degrees(np.median(src.get('coord_ra')))
    center_dec = np.degrees(np.median(src.get('coord_dec')))
    print("Field center: {:.3f}, {:.3f}".format(center_ra, center_dec))


    # I/322A = UCAC4
    columns = ['RAJ2000', 'DEJ2000', 'f.mag', 'a.mag']
    vz = Vizier(columns=columns, row_limit=2000)
    ucac_results = vz.query_region(coord.SkyCoord(ra=center_ra, dec=center_dec,
                                                    unit=(u.deg, u.deg), frame='icrs'),
                                     radius=coord.Angle(0.3, "deg"),
                                     catalog='I/322A')

    ucac_catalog = coord.SkyCoord(ra=ucac_results[0]['RAJ2000'],
                                  dec=ucac_results[0]['DEJ2000'],
                                  unit=(u.deg, u.deg), frame="icrs")

    diff_ra = np.degrees(diff_src.get('coord_ra'))
    diff_dec = np.degrees(diff_src.get('coord_dec'))

    forced_src_SNR = (diff_force_src['base_PsfFlux_flux'] - diff_force_src['template_base_PsfFlux_flux']) /  \
                    np.sqrt(diff_force_src['base_PsfFlux_fluxSigma']**2 + diff_force_src['template_base_PsfFlux_fluxSigma']**2)
    sel_filtered_diasources, = np.where((np.abs(forced_src_SNR) > 5.0) & (diff_src['classification_dipole'] == 0))
    filtered_SNRs = forced_src_SNR[sel_filtered_diasources]

    diasource_catalog = coord.SkyCoord(ra=diff_ra[sel_filtered_diasources], dec=diff_dec[sel_filtered_diasources],
                                       unit=(u.deg, u.deg), frame="icrs")

    assert len(diasource_catalog) == len(filtered_SNRs), "SNR array and DIA catalog lengths must match."

    sources_x = src.get("base_SdssCentroid_x")
    sources_y = src.get("base_SdssCentroid_y")
    source_catalog = coord.SkyCoord(ra=src.get('coord_ra'),
                                    dec=src.get('coord_dec'),
                                    unit=(u.rad, u.rad), frame="icrs")

    ucac_edge_object = is_edge_object(ucac_catalog, source_catalog,
                                      sources_x, sources_y)


    print("Total UCAC obj {:d}, ok obj {:d}".format(len(ucac_edge_object),
                                                    np.sum(~ucac_edge_object)))

    ok_ucac =np.argwhere(~ucac_edge_object)
    ok_ucac_mags = ucac_results[0]['f.mag'][ok_ucac]

    #
    # There's some shift between our image and the UCAC catalog. It is small,
    # so I find the median shift to the nearest decam object, then apply that to the
    # all the UCAC sources. Pretty sure this is because I'm not using the TPV headers.
    #
    delta_ra, delta_dec = compute_shift(ucac_catalog[ok_ucac], source_catalog)

    shifted_ucac = coord.SkyCoord(ra=ucac_catalog.ra[ok_ucac] + np.median(delta_ra),
                                  dec=ucac_catalog.dec[ok_ucac] + np.median(delta_dec),
                                  frame='icrs')


    bright_star_file = open("bright_star_file", mode="a")
    print(len(sources_x), len(diasource_catalog), len(diff_src))
    for ucac_coord,ucac_mag in zip(shifted_ucac, ok_ucac_mags):
        dists = ucac_coord.separation(diasource_catalog)
        sel, = np.where(dists < 1*u.arcmin)
        #print(ucac_mag, np.sort(dists[sel].to(u.arcsec)))
        if ucac_mag < 9:
            print("{},{},{},{},{}".format(ucac_coord.ra.deg, ucac_coord.dec.deg, ucac_mag, visit, ccdnum), file=bright_star_file)

        if sql_session:
            det_dists = [DetectionDist(dist=d.to(u.arcsec).value, SNR=SNR) for d,SNR in zip(dists[sel], filtered_SNRs[sel])]
            sql_entry = SourceDetectionCorrelation(visit=visit, ccdnum=ccdnum, source_mag=ucac_mag,
                                                   detection_dists=det_dists)
            sql_session.add(sql_entry)
    bright_star_file.close()

def run_debug(session):
    """This function saves example sources and diffim source distances to the database, then retrieves them.
    """

    dists = [0.01, 0.02, 0.03]
    test_meas = SourceDetectionCorrelation(visit=1234, ccdnum=10, source_mag=16.0,
                                           detection_dists=[DetectionDist(dist=x) for x in dists])
    session.add(test_meas)

    dists2 = [0.11, 0.12, 0.13]
    test_meas2 = SourceDetectionCorrelation(visit=1234, ccdnum=11, source_mag=17.0,
                                            detection_dists=[DetectionDist(dist=x) for x in dists2])
    session.add(test_meas2)

    print(session.query(SourceDetectionCorrelation).first())
    print(session.query(SourceDetectionCorrelation).first().detection_dists)
    print(session.query(SourceDetectionCorrelation).first().dist_array())

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action='store_true', help="Enable debugging")
    parser.add_argument("repo", help="Repository for images")
    parser.add_argument("visits", help="VisitIDs to process", type=int, nargs="+")
    parser.add_argument("--nccds", help="Maximum number of CCDS to process (for debugging, by default 62)",
                        type=int, action="store", default=62)
    args = parser.parse_args()

    if args.debug:
        engine = sqlalchemy.create_engine('sqlite://')
    else:
        engine = sqlalchemy.create_engine('sqlite:///star_diffim.sqlite3')

    SessionFactory = sessionmaker()
    SessionFactory.configure(bind=engine)
    session = SessionFactory()
    Base.metadata.create_all(engine)

    if args.debug:
        run_debug(session)
    else:
        import lsst.daf.persistence as dafPersist
        butler = dafPersist.Butler(args.repo)
        for visit in args.visits:
            for ccdnum in range(1,args.nccds + 1):
                print("------------")
                print("visit {:d} ccdnum: {:d}".format(visit, ccdnum))
                star_diffim_correlation(visit, ccdnum, butler, sql_session=session)
                session.commit()

