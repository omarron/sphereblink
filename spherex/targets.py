"""Official Planet X and SPHEREx test targets.

WISE 0855 uses the coordinates printed on the challenge page. The other four
positions are ICRS J2000 values retrieved from SIMBAD (Harvard mirror) on
2026-11-14 PT, with the catalog reference SIMBAD printed. Re-resolve them
yourself if you can reach SIMBAD, and propagate proper motion before a tight
cutout. Barnard's Star, Epsilon Indi B, and WISE 0855 move arcseconds to
arcminutes per year.
"""

from __future__ import annotations

from .coords import SkyPosition, dms_to_deg, hms_to_deg

# WISE 0855 coordinates below are taken from the official challenge statement.
# SIMBAD's J2000 position differs because this object has a very large proper
# motion (Kirkpatrick et al. 2021, ApJS 253, 7). Use a cone of 0.05-0.10 deg.

TARGETS = {
    "WISE 0855": {
        # Challenge-page position (08h55m10.831s -7d14m42.53s) is an early-WISE-epoch
        # position (~2010.5). At 8.1"/yr the object is ~2 arcmin west of it by 2025-26,
        # i.e. outside a small cutout. We therefore use SIMBAD's ICRS J2000 position
        # with the Kirkpatrick et al. 2021 proper motion and propagate it per visit.
        "position": SkyPosition(
            ra_deg=hms_to_deg(8, 55, 16.53798),
            dec_deg=dms_to_deg(-7, 14, 49.3728),
            epoch_year=2000.0,
            pm_ra_cosdec_mas_yr=-8123.7,
            pm_dec_mas_yr=673.2,
        ),
        "challenge_position": SkyPosition(
            ra_deg=hms_to_deg(8, 55, 10.831),
            dec_deg=dms_to_deg(-7, 14, 42.53),
        ),
        "aliases": ["wise 0855", "wise0855", "wise 0855-0714", "wise j085510.83-071442.5"],
        "band": "SPHEREx-D6",
        "why": "Fast-moving brown dwarf named in the challenge statement.",
        "source": "NASA Space Apps 2026 challenge page: 08h55m10.831s, -7d14m42.53s.",
        "note": (
            "SIMBAD J2000 (2021ApJS..253....7K) is 08h55m16.53798s, -07d14m49.3728s "
            "with pmRA*=-8123.7 mas/yr, pmDec=+673.2 mas/yr. The challenge position "
            "is the one to use first; keep the search cone wide."
        ),
    },
    "Barnard's Star": {
        "position": SkyPosition(
            ra_deg=hms_to_deg(17, 57, 48.4984700685),
            dec_deg=dms_to_deg(4, 41, 36.113879676),
            epoch_year=2000.0,
            pm_ra_cosdec_mas_yr=-801.551,
            pm_dec_mas_yr=10362.394,
        ),
        "aliases": ["barnard's star", "barnards star", "barnard", "gj 699"],
        "band": "SPHEREx-D5",  # saturated in every band; D5/D6 have the smallest saturated core
        "why": "Nearby star with the largest known proper motion; a motion test target.",
        "source": "SIMBAD (Harvard mirror), 2026-11-14 PT; ICRS J2000 from Gaia EDR3 (2020yCat.1350....0G).",
        "note": "By mid-2026 the J2000 position is off by several arcminutes. Propagate PM.",
    },
    "Epsilon Indi B": {
        "position": SkyPosition(
            ra_deg=hms_to_deg(22, 4, 10.5951812451),
            dec_deg=dms_to_deg(-56, 46, 58.239102418),
            epoch_year=2000.0,
            pm_ra_cosdec_mas_yr=3981.977,
            pm_dec_mas_yr=-2466.832,
        ),
        "aliases": ["epsilon indi b", "eps ind b", "eps indi b", "epsilon indi ba"],
        "band": "SPHEREx-D5",  # T dwarfs are bright at 3.8-4.4 um and unsaturated here
        "why": "A pair of brown dwarfs orbiting Epsilon Indi, named in the challenge.",
        "source": "SIMBAD object '* eps Ind B', 2026-11-14 PT; ICRS J2000 from Gaia EDR3 (2020yCat.1350....0G).",
        "note": "Also high proper motion. This is the B component, not star A.",
    },
    "RW Aurigae": {
        "position": SkyPosition(
            ra_deg=hms_to_deg(5, 7, 49.5662483),
            dec_deg=dms_to_deg(30, 24, 5.177426),
            epoch_year=2000.0,
            pm_ra_cosdec_mas_yr=7.23,
            pm_dec_mas_yr=-20.33,
        ),
        "aliases": ["rw aurigae", "rw aur"],
        "band": "SPHEREx-D1",  # least saturated band for this star
        "why": "Variable-star test target from the challenge (brightness change, little motion).",
        "source": "SIMBAD object 'V* RW Aur', 2026-11-14 PT; ICRS J2000 from van Leeuwen 2007 (2007A&A...474..653V).",
        "note": "Proper motion is small; a 0.05 deg cone is plenty. A and B are ~1.4 arcsec apart.",
    },
    "R Draconis": {
        "position": SkyPosition(
            ra_deg=hms_to_deg(16, 32, 40.2265999080),
            dec_deg=dms_to_deg(66, 45, 17.925901992),
            epoch_year=2000.0,
            pm_ra_cosdec_mas_yr=-20.643,
            pm_dec_mas_yr=6.149,
        ),
        "aliases": ["r draconis", "r dra"],
        "band": "SPHEREx-D1",  # saturated in all six bands (bright Mira); photometry not valid
        "why": "Variable-star test target from the challenge.",
        "source": "SIMBAD object 'V* R Dra', 2026-11-14 PT; ICRS J2000 from Gaia EDR3 (2020yCat.1350....0G).",
        "note": "Proper motion is small. Contrast with the moving brown dwarfs when you blink.",
    },
}


def list_targets():
    return TARGETS


def get_target(name: str) -> dict:
    if name not in TARGETS:
        raise KeyError(f"Unknown target {name!r}. Choose one of: {', '.join(TARGETS)}")
    return TARGETS[name]
