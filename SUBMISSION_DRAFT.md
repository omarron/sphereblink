# Draft team page and project submission

Fill these on spaceappschallenge.org. Everything must be in English. Links must open with no login. **Do not invent results.** Replace bracketed notes after you have actually run the tool. Official field names are from the [2026 Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/).

Deadline for San Jose, CA: **Sunday, 15 November 2026, 11:59 PM Pacific Time**. Submit by 8–9 PM PT if you can. Press **Submit for Judging**, not only Save.

Because you are under 18, include **no photo, video, or voice likeness of yourself** on the team page, slides, or app.

## Team page

**Draft team name:** NearIR Scout

**Draft team description:**

NearIR Scout is a solo virtual team at the San Jose, California NASA Space Apps 2026 event. We are building a public web tool that lets anyone type a sky position and blink SPHEREx visits of that patch in time order, so motion and variability are easier to see. The first tests are the challenge targets: Barnard's Star, Epsilon Indi B, WISE 0855, RW Aurigae, and R Draconis. The team page and project use no personal photographs.

**Event:** San Jose, CA (virtual)  
**Challenge:** Planet X and SPHEREx  
**Members:** only accounts registered for the same San Jose event, listed on the Members tab.

## Required project fields

### Project Name

SphereBlink

### High-Level Project Summary

SphereBlink is a public web app for the Planet X and SPHEREx challenge. A user enters Right Ascension and declination, or picks one of the official test targets. The app queries NASA/IPAC IRSA for SPHEREx Data Release 1 and Quick Release 3 spectral images, downloads small cutouts, and blinks visits of the same detector band in time order so anyone can look for objects that move or change in brightness. SPHEREx is mapping the whole sky in 102 near-infrared bands, and no one person can inspect that archive by hand. [After you deploy it, add one sentence about the public URL and which targets you actually blinked. Do not claim a new object.]

### Link to Project Demo

A 7-slide deck (not a video), hosted on Google Drive or GitHub, set to “anyone with the link.” Test the link in a private window. Slide decks must be in English and no more than seven slides including the title slide. See `slides/SLIDE_OUTLINE.md`.

A 30-second video is allowed, but a slide deck is the safer choice for a minor: Space Apps does not allow images, video, audio, or other likeness of people under 18 on the project or demo.

### Link to Final Project

The public GitHub repository, plus the public Streamlit (or other) app URL if deployment succeeds. Both links must open without a password.

### Detailed Project Description

Draft to edit after the build:

SphereBlink looks up SPHEREx Level-2 spectral images with IRSA’s Simple Image Access v2 service (collections `spherex_dr1` and `spherex_qr3`), then asks IRSA for a cutout around the user’s coordinates. Visits are grouped by `energy_bandpassname` (the six SPHEREx detector arrays) so frames are blinked at matched wavelengths. The interface is a Streamlit app written in Python, using requests, astropy, numpy, and matplotlib. It is meant for students, citizen scientists, and anyone who wants to scan a patch of sky the way Clyde Tombaugh compared plates, without installing an astronomy archive tool.

Benefits: a shareable URL (`?ra=&dec=`), official test targets one click away, and visible metadata so a change can be checked against time, band, and FLAGS. The goal is a tool that stays current as IRSA ingests new SPHEREx releases, not a frozen screenshot.

[Add what you actually finished: difference images, proper-motion option, overlays, spectra — only if built.] Limitations to state honestly: IRSA queries can truncate (`OVERFLOW`); TAP catalog overlays may be slow; SPHEREx products are still being released and can change; wavelength varies across each frame; candidates are not discoveries.

### Use of Super Intelligence (SI)

Judges do not see this answer, but you must still watermark any SI-generated images or video and mention SI-assisted code in the project text.

Draft, to edit so it is accurate:

[If you used a coding assistant or chatbot:] Super Intelligence tools were used to help write starter code, debug IRSA queries, and draft submission text. All science numbers were taken from live IRSA responses or cited catalogs, not generated as fake detections. No SI-generated NASA logos were used. [If a figure is SI-generated, it will carry a visible watermark.]

[If you used none:] No Super Intelligence tools were used.

### NASA Data

SPHEREx Level-2 spectral image multi-extension FITS files from NASA/IPAC IRSA, searched with SIA2 collections `spherex_dr1` and `spherex_qr3` and retrieved as cutouts. Documentation: https://irsa.ipac.caltech.edu/Missions/spherex.html and https://irsa.ipac.caltech.edu/spherex-archive-documentation/spherex-data-access/. Tutorial notebooks: https://caltech-ipac.github.io/irsa-tutorials/spherex/. WISE 0855 test coordinates are from the official challenge statement. [Add AllWISE, Gaia DR3, or other NASA data only if you actually used them.]

IRSA acknowledgement: This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration.

### Space Agency Partner Data and Other References

List every external resource, including open-source libraries, even if unused NASA partner data is only cited as background.

- Challenge statement: https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/
- WiseView (inspiration): http://byw.tools/wiseview
- Gaia DR3 (challenge resource; include only if used): https://archive.stsci.edu/missions-and-data/gaia
- CSA NEOSSat / CADC (optional partner resources)
- Python packages: requests, numpy, astropy, matplotlib, streamlit, Pillow
- SIMBAD (CDS / Harvard mirror) for test-target coordinates other than the challenge’s WISE 0855 position
- Kirkpatrick et al. 2021, ApJS 253, 7, for WISE 0855 proper motion
- Gaia EDR3 catalog (2020yCat.1350....0G) as cited by SIMBAD for Barnard's Star, Epsilon Indi B, and R Draconis
- van Leeuwen 2007, A&A 474, 653, as cited by SIMBAD for RW Aurigae

## Checkboxes before Submit for Judging

- I have read and understand the project submission requirements as contained in the NASA Space Apps Project Submission Guide, and I agree to the Participant Terms and Conditions and Privacy Policy.
- I confirm that the submitted project represents my team’s original work and that all external resources including code, text and images (even if they are open source or freely available) used in the project are listed in the References field of the project submission form. In creating our solution, my team has not used any copyrighted materials that we don’t have permission to use.

## 7-slide outline

See `slides/SLIDE_OUTLINE.md`. Keep to seven slides including title and closing slides. Projects that exceed the limit are not eligible for Global Judging.
