# SphereBlink — final text for the Space Apps Project tab

Team: **NearIR Scout** (solo) · Local event: San Jose, CA (virtual) · Challenge: **Planet X and SPHEREx**
Deadline: **Sun 15 Nov 2026, 11:59 PM PT**. Nothing here has been submitted. Omar reviews, edits, and clicks Submit himself.

> Field length limits: the official Project Submission Guide page could not be loaded from the build machine on 15 Nov 2026 (TLS/500 errors), so no limits were verified. The texts below are kept short (summary ≈ 900 characters, details ≈ 3,500). If the form shows a counter, trim from the end of each field.

---

## Project Name

SphereBlink

## High-Level Summary

SphereBlink is a free, public tool that lets anyone type a sky position (or pick a challenge test target) and watch NASA SPHEREx images of that patch of sky play in time order, like the plate blinking used to find Pluto. It searches the live NASA/IPAC IRSA archive (SPHEREx DR1 and QR3), downloads small cutouts, lines them up on one sky grid, and makes a blink animation plus position-vs-time and brightness plots, with the catalog proper motion drawn on top. On real data it recovers the motion of Barnard's Star (10.2″ in one year, 10.3″ predicted) and Epsilon Indi B (6.5″ vs 6.7″), measures the half-pixel shift of the faint brown dwarf WISE 0855, and shows that RW Aurigae and R Draconis stay still. It matters because SPHEREx re-scans the whole sky every six months, and a simple blinker turns that archive into something students and citizen scientists can explore.

## Project Demo (link)

`[DEMO LINK — 7-slide PDF: slides/SphereBlink_slides.pdf, uploaded to Google Drive or GitHub Pages with "anyone with the link" access]`

## Final Project (link)

`[FINAL PROJECT LINK — public GitHub repo with the code, plus the static demo page (GitHub Pages: https://<github-username>.github.io/sphereblink/) and, if deployed, the live Streamlit app URL]`

## Project Details

**What it does.** You give SphereBlink a target name (Barnard's Star, Epsilon Indi B, WISE 0855, RW Aurigae, R Draconis) or any RA/Dec. It then:
1. Queries IRSA's Simple Image Access v2 service for every SPHEREx Level-2 spectral image covering that point (collections `spherex_dr1` and `spherex_qr3`), with a large MAXREC and an OVERFLOW check so later visits aren't silently dropped.
2. Picks one detector band (D1–D6) and downloads small cutouts from IRSA's cutout service in parallel, caching them on disk.
3. For each visit: subtracts the ZODI (zodiacal light) model, masks bad pixels using the FLAGS plane (hot, cold, transient, missing, outlier) while keeping saturated star cores visible but flagged, and reads the exact wavelength at the target from the WCS-WAVE lookup table. SPHEREx uses linear variable filters, so every visit sees the target at a slightly different wavelength. Brightness is compared only at matched wavelength.
4. Re-projects every visit onto one common north-up sky grid with astropy WCS and sorts the visits by time.
5. Propagates the catalog proper motion to each visit date, then measures the target's centroid and aperture flux in every visit and in a median stack of each six-month survey pass. Field stars are measured as controls.
6. Writes a blink GIF/MP4 of every visit and of the epoch stacks, a position-vs-time plot against the prediction, a brightness-vs-time and brightness-vs-wavelength plot, a first-minus-last difference image, and a JSON file with every visit's metadata.

**Results on the five challenge targets (real data, 15 Nov 2026):**
- *Barnard's Star* (band D5, 48 visits, Aug 2025–Sep 2026): moves clearly north. 10.22″ in 0.99 yr vs 10.30″ predicted. Dec rate 9.99 ± 0.42″/yr vs 10.36 catalog. The RA rate is less accurate (−2.7 ± 0.6 vs −0.8″/yr) because the star saturates every frame.
- *Epsilon Indi B* (D5, 42 visits, Apr 2025–Oct 2026): moves south-east. 6.52″ in 1.43 yr vs 6.68″ predicted. Brightness at matched wavelength is steady to about 5%.
- *WISE 0855* (D6, 45 visits): faint, but detected in the Nov–Dec 2025 and Apr–May 2026 stacks (S/N ≈ 30). It shifts 3.3″ west vs 3.6″ predicted, about half a pixel, so it is measurable but hard to see by eye. The May 2025 stack has only 3 frames and is not reliable. We also found that the challenge-page coordinates are an old (~2010) position: by 2025–26 the object is about 2.1′ west of them, which is why the tool applies proper motion.
- *RW Aurigae* (D1): no motion (0.2″). Using only unsaturated frames at ~0.75 µm, its aperture flux went from ≈74–89 to ≈181–193 mJy between Sep 2025 and Sep 2026. That is a candidate brightening of about 2×, not a confirmed measurement.
- *R Draconis* (D1): no motion (0.5″). It is saturated in all six bands, so its variability cannot be measured with this method yet.

**Tools.** Python 3, requests, numpy, scipy, astropy, matplotlib, Pillow, Streamlit and ffmpeg. It runs as an interactive Streamlit app, as a command-line batch tool, and as a static web page with precomputed results that needs no server.

**Benefits and goals.** No login or archive expertise is needed, and a view can be shared with a link (`?target=` or `?ra=&dec=&band=`). Because the tool queries the archive live, it picks up new SPHEREx releases automatically. Anything that appears to change is labelled a candidate. Next steps: PSF-wing photometry for saturated stars, coadds across bands, Gaia/AllWISE overlays, and known-asteroid labels.

## Use of Artificial Intelligence

An AI assistant (Grok Bot, a general-purpose AI agent) helped write and debug the Python code (IRSA queries, image alignment, centroid and photometry measurements, plots, the Streamlit app, and the static demo page) and helped draft the slide text and this write-up. Omar Ron (team NearIR Scout) chose the project, directed the work, reviewed the code and text, and checked the results. All images, plots and numbers come from real SPHEREx data processed by the code; no AI-generated images, video or audio are used, and no results were invented.

## NASA Data

- SPHEREx Level-2 spectral image data (Data Release 1 and Quick Release 3), NASA/IPAC Infrared Science Archive (IRSA): https://irsa.ipac.caltech.edu/Missions/spherex.html
- SPHEREx data access (SIA2 collections `spherex_dr1`, `spherex_qr3`; cutout service): https://irsa.ipac.caltech.edu/spherex-archive-documentation/spherex-data-access/
- IRSA Simple Image Access v2 endpoint: https://irsa.ipac.caltech.edu/SIA
- IRSA SPHEREx tutorial notebooks (used as documentation): https://caltech-ipac.github.io/irsa-tutorials/spherex/
- Acknowledgement: This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration.

## Space Agency Partner Data

None used. (Gaia EDR3 positions and proper motions were used only as SIMBAD-quoted catalog values for the test targets; see References.)

## References

- Challenge statement: https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/
- WiseView (inspiration only, no code used): http://byw.tools/wiseview
- SIMBAD astronomical database (CDS; Harvard mirror used): https://simbad.u-strasbg.fr/simbad/ and https://simbad.harvard.edu/simbad/ (positions and proper motions of the test targets)
- Gaia Collaboration 2020, Gaia EDR3 (VizieR I/350), via SIMBAD: positions and proper motions of Barnard's Star, Epsilon Indi B, R Draconis
- Kirkpatrick, J. D. et al. 2021, ApJS 253, 7: position and proper motion of WISE 0855−0714
- van Leeuwen, F. 2007, A&A 474, 653 (Hipparcos new reduction), via SIMBAD: RW Aurigae
- Python libraries: requests, numpy, scipy, astropy (Astropy Collaboration 2013, 2018, 2022), matplotlib, Pillow, Streamlit; ffmpeg for MP4 encoding
- AI assistance: Grok Bot (see "Use of Artificial Intelligence")

## Checkboxes (Omar ticks these himself)

- [ ] I have read and understand the project submission requirements … and agree to the Participant Terms and Conditions and Privacy Policy.
- [ ] I confirm that the submitted project represents my team's original work and that all external resources … are listed in the References field.

## Before clicking "Submit for Judging"

1. Make the GitHub repo public, push this folder (without `cache/`), and turn on GitHub Pages for `demo/` (see `demo/HOSTING.md`).
2. Upload `slides/SphereBlink_slides.pdf` (7 slides, no photos of people) and set it to "anyone with the link". Open both links in a private window.
3. Paste the two links into the Demo and Final Project fields, re-read every field, tick both boxes, and submit before 11:59 PM PT. Resubmitting before the deadline is allowed.
