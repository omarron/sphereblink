# SphereBlink — 7-slide outline

Make this deck during the hackathon, after the app runs. Use screenshots of the tool and public NASA/IRSA graphics only. **No personal photos, no video of the presenter.** Keep text short and readable.

## Slide 1 — Title

SphereBlink  
A public way to watch SPHEREx visits change over time  
Team NearIR Scout · NASA Space Apps 2026 · Planet X and SPHEREx  
San Jose, CA (virtual)

## Slide 2 — The problem

SPHEREx is mapping the whole sky every six months in 102 near-infrared bands. Movers such as brown dwarfs, asteroids, and comets show up when the same patch is compared across visits, but the archive is too large to inspect by hand. People need a simple public tool, in the spirit of plate blinking and WiseView.

## Slide 3 — The solution

Type a Right Ascension and declination, or pick an official test target. SphereBlink fetches SPHEREx cutouts from NASA/IPAC IRSA and blinks same-band visits in time order. A shareable `?ra=&dec=` link can be embedded elsewhere.

## Slide 4 — NASA data

SPHEREx DR1 and QR3 Level-2 spectral images at IRSA, via SIA2 and the cutout service. Visits are grouped by detector band because wavelength changes across the linear-variable-filter arrays. FLAGS can be masked so a cosmic ray is not mistaken for a flash. [Paste one real screenshot of the visit table or a FITS preview you generated.]

## Slide 5 — Demo

[Paste 2–3 real blink frames of one test target, labeled with UTC dates and the band, for example SPHEREx-D2. If a source appears to move or change brightness, call it a candidate and say what you have not yet ruled out. If nothing obvious moves, say that honestly — a working tool on real data is the result.]

## Slide 6 — Impact and next steps

Anyone can open a field and look, including students and citizen-science projects like Backyard Worlds. Next (only list items you have not finished): AllWISE/Gaia overlays, on-the-fly spectra, known-asteroid labels. Limits: archive truncation, changing quick-release products, and the need to match wavelength and proper motion.

## Slide 7 — Credits

Team NearIR Scout (solo).  
Data: NASA SPHEREx / JPL / Caltech, served by NASA/IPAC IRSA.  
Inspiration: WiseView and the challenge statement.  
Code: Python, Streamlit, astropy, numpy, matplotlib.  
[Add SI/AI credit if used.]  
IRSA acknowledgement (short): SPHEREx data are a joint project of JPL and Caltech, funded by NASA.
