# ~24-hour solo build plan (Pacific Time)

Hackathon window for San Jose, CA: work must be created during the event. Project submission opened Saturday 14 November 2026 at 9:00 AM PT and **closes Sunday 15 November 2026 at 11:59 PM PT**. Local-event teams may be a single person. Because you are 15, **do not put your photo, video, or voice on the project or demo** (Space Apps terms: no likeness of anyone under 18). Use a 7-slide deck, not a talking-head video.

This plan assumes a Saturday evening start (~7 PM PT) and a full Sunday, with sleep. Elapsed time is about 29 hours; planned working time is about 16–18 hours. Cut scope before you cut sleep or the submission.

## Concept to ship

**SphereBlink** — a public Streamlit app: enter RA/Dec (or pick one official test target), query IRSA SIA2 for SPHEREx DR1/QR3 visits, download same-band cutouts, and blink them in time order. URL query parameters share a view. Metadata (time, detector, collection) is visible. No CNN in the MVP.

## Saturday evening (hours 0–5) — about 7–11 PM PT

**Hour 0 (create the team first, before coding).** On spaceappschallenge.org, create the team, set the draft name and description from `SUBMISSION_DRAFT.md`, choose San Jose, CA, and select the challenge Planet X and SPHEREx. Confirm you appear on the Members tab.

**Hour 0.5–1.** Skim the challenge Objectives and Potential Considerations again. Create a public GitHub repo and push this starter. Create a Python venv, install `requirements.txt`, run `python3 verify_access.py`. If SIA or cutouts fail, wait and retry; do not switch to a fake local dataset.

**Hours 1–3.** Run `query_visits.py` on WISE 0855 with `--maxrec 200`. Pick one band that has several unique times months apart (not just one night of dithers). Run `fetch_cutouts.py` for that band. Confirm PNGs exist and FLAGS masking does not empty the image.

**Hours 3–5.** Run `streamlit run app.py`. Get WISE 0855 blinking in one band, with dates visible. Commit. Stop for sleep even if the UI is plain.

## Sunday morning (hours 6–10)

**Hours 6–8.** Add the other four official targets. For Barnard's Star and Epsilon Indi B, propagate proper motion (`--year 2026.3`) and use a 0.05–0.10 deg cone. Confirm each target returns at least two same-band visits, or write down honestly if coverage is missing.

**Hours 8–10.** If time: a simple difference image between the first and last aligned visit of the same band; show FLAGS on the caption; honor `?ra=&dec=` already in the app. Skip AllWISE/Gaia overlays if IRSA TAP is still slow. A working blinker beats an unfinished overlay.

## Sunday afternoon (hours 10–14)

**Hours 10–12.** Polish only what judges will see: a short on-screen disclaimer, stable defaults, and a README that says how to run the app. Deploy Streamlit Community Cloud from the public repo (or `streamlit run` plus screenshots if deploy lags). Request a FortiGuard classification only if you have a custom domain.

**Hours 12–14.** Build the 7-slide deck from `slides/SLIDE_OUTLINE.md`. Use only screenshots of the sky tool, NASA/IRSA credit, and text. No personal photos. Host the deck on Google Drive or GitHub Pages with “anyone with the link.” Test the link in a private window.

## Sunday evening (hours 14–16+), submit by 8–9 PM PT

Fill every required project field from `SUBMISSION_DRAFT.md`, replacing placeholders with what you actually built. Disclose any Super Intelligence / AI use. List NASA data and every library. Check both legal boxes. Click **Submit for Judging**. Confirm the banner. You may edit and resubmit until 11:59 PM PT; only the last submission is judged. Leave a one-hour buffer.

## If you fall behind

Ship, in this order: (1) public repo + running blinker for WISE 0855 in one band, (2) the other official targets or a clear note that a target had no coverage, (3) 7-slide deck, (4) submitted form. Cut spectra, mosaics of all 102 bands, machine learning, and AllWISE overlays first.

## Stretch only after the submission draft is filled

- Coadd visits of one detector to raise signal-to-noise, as the challenge suggests.
- On-the-fly spectrum from the `WCS-WAVE` extension at a clicked pixel.
- AllWISE or Gaia overlay if TAP or another catalog path is working.
- Optional CSA NEOSSat lookup for a field that has it.
- JPL Small-Body / SkyBoT labels for known asteroids — still as names, not “discoveries.”
