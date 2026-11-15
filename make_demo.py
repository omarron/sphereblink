#!/usr/bin/env python3
"""Build the static, no-server demo page (demo/index.html) from precomputed outputs/."""
import json, shutil, html
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT, DEMO = HERE / "outputs", HERE / "demo"
RUNS = [  # (output folder, verdict written after inspecting the real outputs)
 ("barnard_s_star_d5", "Moves — clearly visible.",
  "Barnard's Star visibly moves north between the three epoch stacks. Epoch 1 to epoch 3 shift: {shift}\" in {dt} yr; the Gaia catalog proper motion predicts {pred}\". "
  "Fitted rate from the stacks: Dec {sdec} ± {sdece}\"/yr (catalog {cdec}); RA {sra} ± {srae}\"/yr (catalog {cra}). The RA part is less accurate because the star is saturated in every SPHEREx frame, so its centroid jitters by about ±2\" visit to visit. Saturation also means no brightness measurement."),
 ("epsilon_indi_b_d5", "Moves — visible, matches catalog.",
  "Epsilon Indi B (an unresolved pair of brown dwarfs) moves south-east. First to last epoch: {shift}\" in {dt} yr vs {pred}\" predicted. Stack fit: RA {sra} ± {srae}\"/yr, Dec {sdec} ± {sdece}\"/yr (catalog {cra}, {cdec}). "
  "Brightness at matched wavelength (3.8–4.4 µm) stays the same within about 5% between epochs (ratios {vmin}–{vmax}), so no variability is claimed."),
 ("wise_0855_d6", "Faint; motion measured, hard to see by eye.",
  "WISE 0855 is faint and only shows up at the longest wavelengths (4.4–5.0 µm, band D6). It is detected in the Nov–Dec 2025 and Apr–May 2026 stacks (S/N ≈ 30); the May 2025 stack has only 3 frames and is not a reliable detection. "
  "Between the two good epochs it shifts about 3.3\" west vs 3.6\" predicted — about half a SPHEREx pixel, so the blink alone does not make it obvious; the centroid measurement does. Stack fit RA {sra} ± {srae}\"/yr (catalog {cra}) leans on the weak first epoch. "
  "In band D5 the measurement disagrees more (6.1\" vs 8.1\" predicted), probably blending/low signal — treated as unreliable. Note: the challenge-page coordinates are an old (≈2010) position; by 2025–26 the object is ≈2.1′ west of it, so SphereBlink propagates the proper motion."),
 ("rw_aurigae_d1", "Does not move; candidate brightening.",
  "RW Aurigae stays put ({shift}\" first-to-last vs {pred}\" expected; a nearby field star moved {ctrl}\"), as a non-moving test should. "
  "Its core saturates in {sat} of {nf} frames. Using only unsaturated frames at matched wavelength (~0.74–0.78 µm) the aperture flux rose from ≈74–89 mJy (Sep 2025) to ≈116–125 mJy (Mar 2026) to ≈181–193 mJy (Sep 2026): a candidate ~2× brightening. "
  "Caveats: few matched pairs, ±20–30% scatter between neighbouring wavelengths, no aperture correction, A+B blended. RW Aur is a known strongly variable young star, but this is not a confirmed measurement."),
 ("r_draconis_d1", "Does not move; too bright to measure brightness.",
  "R Draconis does not move ({shift}\" first-to-last, within the noise). It is saturated in all six SPHEREx bands in every frame we checked, so this simple aperture photometry cannot measure its (known) Mira variability. That would need PSF-wing photometry — listed as future work."),
]

NOTES = {"wise_0855_d6": " <span class='small'>(first epoch has only 3 frames and is unreliable; between the two reliable epochs: 3.3″ measured vs 3.6″ predicted)</span>"}

def fmt(s):
    m = s["motion"]
    var = [v["median_flux_ratio_later_over_earlier"] for v in s["matched_wavelength_brightness"] if v["n_matched_pairs"] >= 3]
    ctrl = m.get("control_star_first_to_last_shift_arcsec") or ["n/a"]
    return dict(shift=m.get("first_to_last_epoch_shift_arcsec"), dt=m.get("first_to_last_epoch_dt_yr"), pred=m.get("predicted_shift_arcsec"),
                sra=m.get("stack_pm_ra_cosdec_arcsec_yr"), srae=m.get("stack_pm_ra_err"), sdec=m.get("stack_pm_dec_arcsec_yr"), sdece=m.get("stack_pm_dec_err"),
                cra=m.get("catalog_pm_ra_cosdec_arcsec_yr"), cdec=m.get("catalog_pm_dec_arcsec_yr"), vmin=min(var) if var else "n/a", vmax=max(var) if var else "n/a",
                ctrl=ctrl[0], sat=s["saturated_frames"], nf=s["n_frames_used"])

def main():
    shutil.rmtree(DEMO / "assets", ignore_errors=True)
    (DEMO / "assets").mkdir(parents=True)
    cards, table = [], []
    for folder, verdict, text in RUNS:
        d = OUT / folder
        s = json.loads(next(d.glob("*_summary.json")).read_text())
        slug = next(d.glob("*_summary.json")).name.replace("_summary.json", "")
        dst = DEMO / "assets" / folder; dst.mkdir()
        for suffix in ("_blink_epochs.gif", "_blink_all_visits.gif", "_motion.png", "_lightcurve.png", "_first_last_diff.png", "_summary.json"):
            shutil.copy(d / f"{slug}{suffix}", dst / f"{slug}{suffix}")
        a = f"assets/{folder}/{slug}"
        body = html.escape(text.format(**fmt(s)))
        cards.append(f"""
<section class="card" id="{folder}">
 <h2>{html.escape(s['target'])} <span class="band">{s['band']}</span></h2>
 <p class="verdict">{html.escape(verdict)}</p>
 <p class="meta">{s['n_frames_used']} SPHEREx visits ({', '.join(c.replace('spherex_','').upper() for c in s['collections_used'])}), {s['date_range_utc'][0]} → {s['date_range_utc'][1]} UTC, {len(s['epochs'])} survey epochs. Field 0.05° (3′), north up, east left.</p>
 <div class="row">
  <figure><img src="{a}_blink_epochs.gif" alt="Blink of epoch median stacks for {html.escape(s['target'])}"><figcaption>Epoch stacks (median of each survey pass)</figcaption></figure>
  <figure><img src="{a}_blink_all_visits.gif" alt="Blink of every visit for {html.escape(s['target'])}"><figcaption>Every visit in time order (wavelength changes visit to visit)</figcaption></figure>
 </div>
 <p>{body}</p>
 <figure class="wide"><img src="{a}_motion.png" alt="Position versus time"><figcaption>Measured position vs time; cyan line = catalog proper-motion prediction.</figcaption></figure>
 <figure class="wide"><img src="{a}_lightcurve.png" alt="Brightness versus time and wavelength"><figcaption>Aperture flux vs time (colour = wavelength) and vs wavelength per epoch. Red × / open circles = saturated.</figcaption></figure>
 <figure class="wide"><img src="{a}_first_last_diff.png" alt="First and last epoch and difference"><figcaption>First vs last epoch and their difference: a mover leaves a red/blue pair.</figcaption></figure>
 <p class="small"><a href="{a}_summary.json">Full numbers and per-visit metadata (JSON)</a></p>
</section>""")
        table.append(f"<tr><td><a href='#{folder}'>{html.escape(s['target'])}</a></td><td>{s['band']}</td><td>{s['n_frames_used']}</td><td>{s['motion'].get('first_to_last_epoch_shift_arcsec')}\"</td><td>{s['motion'].get('predicted_shift_arcsec')}\"</td><td>{html.escape(verdict)}{NOTES.get(folder, '')}</td></tr>")
    page = TEMPLATE.replace("{{CARDS}}", "\n".join(cards)).replace("{{TABLE}}", "\n".join(table))
    (DEMO / "index.html").write_text(page)
    (DEMO / ".nojekyll").write_text("")
    print("wrote", DEMO / "index.html")

TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SphereBlink — blink SPHEREx visits to find things that move or change</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#0b1020;color:#e8ecf5;line-height:1.5}
header,main,footer{max-width:1050px;margin:auto;padding:0 18px}
header{padding-top:28px} h1{margin:0 0 4px;font-size:2.1em} .tag{color:#9fb3d9}
a{color:#7cc7ff} .card{background:#141b33;border-radius:12px;padding:16px 20px;margin:22px 0}
.band{font-size:.6em;background:#24305a;padding:2px 8px;border-radius:6px;vertical-align:middle}
.verdict{font-weight:600;color:#ffd479;margin:4px 0} .meta,.small{color:#9fb3d9;font-size:.9em}
.row{display:flex;flex-wrap:wrap;gap:16px} figure{margin:8px 0;flex:1 1 300px} figure img{width:100%;border-radius:6px;background:#fff}
.row figure img{max-width:420px} figcaption{font-size:.85em;color:#9fb3d9}
table{border-collapse:collapse;width:100%;font-size:.92em} td,th{border-bottom:1px solid #2a355e;padding:6px;text-align:left}
code{background:#24305a;padding:1px 5px;border-radius:4px} .note{border-left:4px solid #ffd479;padding-left:12px}
</style></head><body>
<header>
<h1>SphereBlink</h1>
<div class="tag">Blink NASA SPHEREx images of any patch of sky to spot things that move or change. NASA Space Apps 2026 · Challenge: <a href="https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/">Planet X and SPHEREx</a> · Team NearIR Scout (San Jose, CA)</div>
</header>
<main>
<section class="card">
<h2>What this is</h2>
<p>SPHEREx scans the whole sky every six months in 102 near-infrared colours. Like Clyde Tombaugh blinking photographic plates, SphereBlink puts the visits of one small patch of sky in time order and plays them as a short animation, so a star that moves (or changes brightness) stands out against the fixed background.</p>
<p>Given a target name or RA/Dec, the tool: (1) asks NASA/IPAC IRSA's Simple Image Access service for every SPHEREx DR1 and QR3 image covering it; (2) downloads small cutouts of one detector band; (3) subtracts the zodiacal-light model, masks bad pixels from the FLAGS plane (but keeps saturated star cores visible), and reads the exact wavelength at the target from each image's wavelength map; (4) re-projects every visit onto one common sky grid; (5) measures the target's position and brightness in each visit and in median stacks of each survey pass; (6) makes the blink animations and plots below, with the catalog proper-motion prediction overlaid.</p>
<p class="note">This page is a <b>static snapshot</b> of real results computed on 15 Nov 2026 from live IRSA data. The full tool (Python + Streamlit) queries the archive live for any RA/Dec. Anything that seems to move or change is a <i>candidate</i>, not a discovery.</p>
</section>
<section class="card"><h2>Results on the five challenge test targets</h2>
<table><tr><th>Target</th><th>Band</th><th>Visits</th><th>Measured shift (first→last epoch)</th><th>Predicted from catalog</th><th>Verdict</th></tr>
{{TABLE}}
</table>
<p class="small">Bands: D1 0.75–1.1 µm, D5 3.8–4.4 µm, D6 4.4–5.0 µm. One SPHEREx pixel = 6.15″. Shifts are from the median-stack centroids.</p>
</section>
{{CARDS}}
<section class="card"><h2>How to read the animations</h2>
<ul><li><b>Green ticks</b> mark a fixed point on the sky (the target's catalog position at the middle of the time span). A mover drifts relative to them.</li>
<li><b>Cyan circle</b>: where the catalog proper motion says the target should be on that date. <b>Orange +</b>: where SphereBlink measured it.</li>
<li>Each SPHEREx detector has a linear variable filter, so every visit sees the target at a slightly different wavelength (shown in the label). Brightness is only compared at matched wavelength.</li></ul>
</section>
<section class="card"><h2>Limits (honest list)</h2>
<ul><li>Bright stars (Barnard's Star, R Dra, most of RW Aur) saturate SPHEREx; their brightness cannot be measured by this simple method, and their centroids are noisier.</li>
<li>Motions of a fraction of a pixel (WISE 0855 over 6 months) are measurable but hard to see by eye.</li>
<li>Aperture fluxes are not aperture-corrected or colour-corrected; use them for relative changes only.</li>
<li>SPHEREx data releases are still being added (DR1 + QR3 as of Nov 2026); results will change as more visits arrive.</li></ul></section>
<section class="card"><h2>Data, code and credits</h2>
<p>Data: NASA SPHEREx Level-2 spectral images (collections <code>spherex_dr1</code>, <code>spherex_qr3</code>) from <a href="https://irsa.ipac.caltech.edu/Missions/spherex.html">NASA/IPAC Infrared Science Archive (IRSA)</a>, via <a href="https://irsa.ipac.caltech.edu/spherex-archive-documentation/spherex-data-access/">SIA2 and the cutout service</a>. Target positions and proper motions: SIMBAD (Gaia EDR3; Kirkpatrick et al. 2021 for WISE 0855; van Leeuwen 2007 for RW Aur).</p>
<p>This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration.</p>
<p>Code: Python, numpy, scipy, astropy, matplotlib, Pillow, requests, Streamlit, ffmpeg. AI disclosure: an AI assistant helped write code and text; the team member directed, reviewed and tested the work. All numbers on this page come from the real outputs. Not an official NASA product.</p>
</section>
</main>
<footer><p class="small">SphereBlink · Team NearIR Scout · NASA Space Apps Challenge 2026</p></footer>
</body></html>
"""

if __name__ == "__main__":
    main()
