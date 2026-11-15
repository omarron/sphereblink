# SphereBlink

**Status (15 Nov 2026): finished build.** The full pipeline works end to end on live IRSA data. Results for all five test targets are in `outputs/` (see `outputs/RESULTS.md`), a static demo page that needs no server is in `demo/`, the 7-slide deck is `slides/SphereBlink_slides.pdf`, and the submission text is in `SUBMISSION_FINAL.md`.

## Finished tool — quick start

```bash
python3 -m pip install -r requirements.txt
python3 sphereblink.py --target "Barnard's Star"          # or WISE 0855, Epsilon Indi B, RW Aurigae, R Draconis
python3 sphereblink.py --ra 269.4463 --dec 4.7676 --band SPHEREx-D5 [--pm-ra -801.6 --pm-dec 10362.4]
python3 sphereblink.py --all                               # all five targets -> outputs/
python3 make_demo.py                                       # rebuild demo/index.html from outputs/
python3 slides/make_slides.py                              # rebuild the 7-slide PDF
streamlit run app.py                                       # interactive app (?target= or ?ra=&dec=&band=)
```

New modules: `spherex/pipeline.py` (SIA query + cache, parallel cached cutouts, zodi subtraction, FLAGS masking that keeps SOURCE pixels, per-pixel wavelength from WCS-WAVE, re-projection to a common grid, centroids, aperture flux, proper-motion prediction, GIF/MP4) and `spherex/blink.py` (one-call run that writes all outputs plus a JSON summary). Note: the starter masked every nonzero FLAGS pixel, which hides the stars themselves (bit 21 = SOURCE); that is fixed.

---

*Original starter notes follow.*

Public SPHEREx image-time-series tool for the [NASA Space Apps Challenge 2026](https://www.spaceappschallenge.org/2026/) challenge [Planet X and SPHEREx](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/).

This is a starter you can finish during the hackathon. It does **not** contain results, detections, or a submitted project. Do not invent motion or discoveries when you write the submission.

## What the challenge asks for

A public web tool where someone enters a sky position (Right Ascension and declination) and sees a series of SPHEREx images of that patch, like a short video, so moving objects are easier to spot. Test it on Barnard's Star, Epsilon Indi B, WISE 0855 (challenge coordinates `08h55m10.831s`, `-7d14m42.53s`), RW Aurigae, and R Draconis.

SPHEREx data are released through [NASA/IPAC IRSA](https://irsa.ipac.caltech.edu/Missions/spherex.html) and will change; design the tool to query the live archive (DR1 and QR3), not a one-off download.

## Architecture

- **Language:** Python 3
- **Search:** IRSA Simple Image Access v2 (`https://irsa.ipac.caltech.edu/SIA`, collections `spherex_dr1` and `spherex_qr3`, plus `_deep` if you want deep fields)
- **Pixels:** IRSA on-premises cutout service (`access_url?center=RA,Dec&size=DEG`)
- **App:** Streamlit, deployable to Streamlit Community Cloud from a public GitHub repo
- **Why this stack:** it matches a solo Python workflow, needs no login, and can be a public URL by Sunday night. Optional later: AllWISE/Gaia overlays (IRSA TAP; TAP timed out from the environment that built this starter), difference images, a one-click spectrum from `WCS-WAVE`.

## Data access, as checked on 2026-11-14 (Pacific Time)

| Service | Result |
| --- | --- |
| SIA2 `spherex_dr1` cone 0.05 deg around the challenge WISE 0855 position | Worked (HTTP 200). A `MAXREC=200` query returned 200 rows and `OVERFLOW`, with unique times from 2025-05-05 through 2026-04-26 (MJD 60800.700028–61156.085511), across detectors D1–D6. |
| SIA2 `spherex_qr3` at the same WISE 0855 0.02 deg cone | HTTP 200, 0 rows (real empty result, `QUERY_STATUS=OK`). |
| SIA2 `spherex_qr3` at IRSA's documented example `127.69444, -39.17760` | Worked (HTTP 200). |
| Cutout of a DR1 Level-2 MEF, `center=133.795129,-7.245147&size=0.05` | Worked (HTTP 200, 4,049,280 bytes, valid FITS `SIMPLE` file). |
| TAP `spherex.obscore` and TAP `allwise_p3as_psd` | Timed out (90 s and 40 s, 0 bytes). Do not depend on TAP for the MVP. |
| SIMBAD at CDS / Sesame / NED | Unreachable from that environment (TLS errors or CDS downtime). Coordinates for the four non-WISE targets were taken from the [Harvard SIMBAD mirror](https://simbad.harvard.edu/simbad/) the same evening. |

Re-run `python3 verify_access.py` on your machine before you demo. Coverage and releases change.

## Quick start

```bash
cd spherex_starter
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 verify_access.py
python3 query_visits.py --target "WISE 0855" --maxrec 200
python3 fetch_cutouts.py --target "WISE 0855" --band SPHEREx-D2 --limit 6
streamlit run app.py
```

Then open the other four test targets. For Barnard's Star, Epsilon Indi B, and WISE 0855, keep the cone at least 0.05–0.10 deg and use `--year 2026.3` where proper motion is stored.

## Important science constraints (do not skip)

- **Match the band before you blink.** SPHEREx uses linear variable filters, so wavelength changes across the detector. A brightness change at mismatched wavelengths can just be the spectrum.
- **Use a large enough MAXREC.** A cap of 5–30 around WISE 0855 returned only 2025 May 5–6 dithers. Raising it to 200 revealed later months. If the VOTable says `OVERFLOW`, you are still missing rows.
- **Mask FLAGS.** Cosmic rays and bad pixels can look like a flash.
- **Propagate proper motion** for nearby movers, then call anything you see a *candidate*, not a discovery.
- **SPHEREx acknowledgement** (required by IRSA if you publish): “This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration.”

## Repo layout

- `verify_access.py` — live check of SIA2, one cutout, optional TAP
- `query_visits.py` — list visits for a target
- `fetch_cutouts.py` — download same-band cutouts and PNG previews
- `app.py` — Streamlit blinker with `?ra=&dec=` URL sharing
- `spherex/` — targets, SIA/cutout client, FITS preview
- `BUILD_PLAN.md` — realistic ~24-hour solo plan
- `SUBMISSION_DRAFT.md` — team name, project fields, 7-slide outline
- `slides/SLIDE_OUTLINE.md` — slide-by-slide notes (no personal photos)

## Official resources

- Challenge: https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/
- IRSA SPHEREx: https://irsa.ipac.caltech.edu/Missions/spherex.html
- Data access guide (SIA2, cutouts, astroquery/pyvo): https://irsa.ipac.caltech.edu/spherex-archive-documentation/spherex-data-access/
- Tutorial notebooks: https://caltech-ipac.github.io/irsa-tutorials/spherex/
- WiseView (inspiration, not a code dependency): http://byw.tools/wiseview
- Gaia DR3: https://archive.stsci.edu/missions-and-data/gaia
- CSA NEOSSat and CADC (optional partner data)
- Project Submission Guide: https://www.spaceappschallenge.org/resources/project-submission-guide/
