#!/usr/bin/env python3
"""Build slides/SphereBlink_slides.pdf (7 slides) from the real outputs. No photos of people."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
O = HERE / "outputs"
BG, FG, ACC, MUT = "#0b1020", "#e8ecf5", "#ffd479", "#9fb3d9"
S = {f.parent.name: json.loads(f.read_text()) for f in O.glob("*/*_summary.json")}

def slide(title, sub=None):
    fig = plt.figure(figsize=(13.333, 7.5), facecolor=BG)
    fig.text(0.04, 0.92, title, color=FG, fontsize=28, weight="bold", va="center")
    if sub:
        fig.text(0.04, 0.865, sub, color=MUT, fontsize=14, va="center")
    fig.text(0.96, 0.03, "SphereBlink · Team NearIR Scout · NASA Space Apps 2026", color=MUT, fontsize=9, ha="right")
    return fig

def img(fig, path, rect):
    ax = fig.add_axes(rect); ax.imshow(Image.open(path)); ax.axis("off"); return ax

def bullets(fig, items, x=0.04, y=0.78, size=15, dy=0.065, width=None):
    for it in items:
        col = ACC if it.startswith("!") else FG
        fig.text(x, y, "• " + it.lstrip("!"), color=col, fontsize=size, va="top", wrap=True)
        y -= dy * (1 + it.count("\n"))
    return y

def strip(paths):
    ims = [Image.open(p).convert("RGB") for p in paths]
    out = Image.new("RGB", (sum(i.width for i in ims), ims[0].height), "white")
    x = 0
    for i in ims:
        out.paste(i, (x, 0)); x += i.width
    tmp = Path("/tmp") / ("strip_" + Path(paths[0]).parent.parent.name + ".png")
    out.save(tmp); return tmp

with PdfPages(HERE / "slides" / "SphereBlink_slides.pdf") as pdf:
    # 1 title
    fig = slide("SphereBlink", "Blink NASA SPHEREx images of any patch of sky to spot things that move or change")
    fig.text(0.04, 0.78, "Team NearIR Scout (solo) · San Jose, CA (virtual) · Challenge: Planet X and SPHEREx", color=FG, fontsize=15)
    img(fig, strip(sorted((O / "barnard_s_star_d5" / "epochs").glob("frame_*.png"))), [0.04, 0.12, 0.92, 0.6])
    fig.text(0.04, 0.09, "Real SPHEREx data: Barnard's Star in three survey passes, Aug 2025 → Mar 2026 → Aug–Sep 2026. Green ticks stay fixed; the star moves north.", color=MUT, fontsize=12)
    pdf.savefig(fig, facecolor=BG); plt.close(fig)

    # 2 problem
    fig = slide("The problem", "SPHEREx maps the whole sky every ~6 months in 102 near-infrared colours")
    bullets(fig, [
        "Nearby brown dwarfs, fast stars and variable stars reveal themselves by changing between visits.",
        "But SPHEREx data come as millions of large multi-extension FITS files in an archive —\nhard to explore for students and citizen scientists.",
        "Each detector has a linear variable filter: wavelength changes across the image,\nso naive 'before vs after' comparisons can fake a brightness change.",
        "Bright stars saturate; cosmic rays and hot pixels look like flashes.",
        "!Goal: a public tool — type a sky position, watch that patch change over time (like plate blinking / WiseView).",
    ], y=0.76, size=17, dy=0.085)
    pdf.savefig(fig, facecolor=BG); plt.close(fig)

    # 3 solution
    fig = slide("The solution: SphereBlink", "Python + Streamlit web app, plus a no-server static demo page")
    steps = ["Name or RA/Dec", "IRSA SIA2 search\nDR1 + QR3", "Cutouts of one band\n(parallel, cached)", "Subtract zodi, mask\nFLAGS, read λ map", "Re-project to one\nsky grid, sort by time", "Measure position +\nflux, epoch stacks", "Blink GIF/MP4,\nmotion & light curve"]
    for i, s_ in enumerate(steps):
        x = 0.04 + i * 0.134
        fig.patches.append(matplotlib.patches.FancyBboxPatch((x, 0.56), 0.12, 0.17, boxstyle="round,pad=0.01", transform=fig.transFigure, fc="#24305a", ec=ACC))
        fig.text(x + 0.06, 0.645, s_, color=FG, fontsize=10, ha="center", va="center")
    bullets(fig, [
        "Catalog proper motion is propagated to every visit date and overlaid (cyan circle); measured centroid in orange.",
        "Brightness compared only at matched wavelength (per-pixel wavelength from the WCS-WAVE table).",
        "Saturated star cores kept visible but flagged; photometry there reported as lower limits.",
        "Shareable links (?target= or ?ra=&dec=&band=), CLI for batch runs, JSON with every visit's metadata.",
    ], y=0.46, size=15, dy=0.075)
    pdf.savefig(fig, facecolor=BG); plt.close(fig)

    # 4 NASA data
    fig = slide("NASA data and how it is used", "SPHEREx Level-2 spectral images · NASA/IPAC IRSA · queried live, no frozen download")
    order = [("barnard_s_star_d5", "Barnard's Star"), ("epsilon_indi_b_d5", "Epsilon Indi B"), ("wise_0855_d6", "WISE 0855"), ("rw_aurigae_d1", "RW Aurigae"), ("r_draconis_d1", "R Draconis")]
    rows = [[n, str(S[k]["n_images_all_bands"]), S[k]["band"].replace("SPHEREx-", ""), str(S[k]["n_frames_used"]), f"{S[k]['date_range_utc'][0]} → {S[k]['date_range_utc'][1]}", f"{S[k]['saturated_frames']}/{S[k]['n_frames_used']}"] for k, n in order]
    ax = fig.add_axes([0.04, 0.42, 0.92, 0.38]); ax.axis("off")
    t = ax.table(cellText=rows, colLabels=["Target", "Images, all bands", "Band used", "Visits blinked", "Dates (UTC)", "Saturated"], loc="center", cellLoc="center", colWidths=[0.15, 0.16, 0.1, 0.12, 0.33, 0.12])
    t.auto_set_font_size(False); t.set_fontsize(13); t.scale(1, 2.0)
    for (r, c), cell in t.get_celld().items():
        cell.set_facecolor("#24305a" if r == 0 else "#141b33"); cell.set_edgecolor("#3a4675"); cell.get_text().set_color(FG)
    bullets(fig, [
        "Search: IRSA Simple Image Access v2 (spherex_dr1 + spherex_qr3).\nPixels: IRSA cutout service (IMAGE, FLAGS, ZODI, WCS-WAVE extensions).",
        "!Lesson: the WISE 0855 challenge coordinates are an ~2010 position; by 2025-26\nit is ~2.1′ west, so proper motion must be applied.",
        "IRSA TAP timed out from our setup, so SphereBlink uses SIA2 + cutouts only.",
    ], y=0.37, size=13.5, dy=0.055)
    pdf.savefig(fig, facecolor=BG); plt.close(fig)

    # 5 results: movers
    b, e = S["barnard_s_star_d5"]["motion"], S["epsilon_indi_b_d5"]["motion"]
    fig = slide("Results: the movers move", "Measured from real SPHEREx frames vs catalog proper motion")
    img(fig, O / "barnard_s_star_d5" / "barnard_s_star_motion.png", [0.02, 0.43, 0.6, 0.38])
    img(fig, O / "epsilon_indi_b_d5" / "epsilon_indi_b_first_last_diff.png", [0.02, 0.06, 0.6, 0.36])
    fig.text(0.64, 0.78, "Barnard's Star (D5)", color=ACC, fontsize=16, weight="bold", va="top")
    fig.text(0.64, 0.73, f"Shift {b['first_to_last_epoch_shift_arcsec']}\" in {b['first_to_last_epoch_dt_yr']} yr\n(predicted {b['predicted_shift_arcsec']}\")\nDec rate {b['stack_pm_dec_arcsec_yr']} ± {b['stack_pm_dec_err']}\"/yr (catalog {b['catalog_pm_dec_arcsec_yr']})\nRA less precise: saturated core", color=FG, fontsize=13, va="top")
    fig.text(0.64, 0.45, "Epsilon Indi B (D5)", color=ACC, fontsize=16, weight="bold", va="top")
    fig.text(0.64, 0.40, f"Shift {e['first_to_last_epoch_shift_arcsec']}\" in {e['first_to_last_epoch_dt_yr']} yr\n(predicted {e['predicted_shift_arcsec']}\")\nPM {e['stack_pm_ra_cosdec_arcsec_yr']}, {e['stack_pm_dec_arcsec_yr']}\"/yr\n(catalog {e['catalog_pm_ra_cosdec_arcsec_yr']}, {e['catalog_pm_dec_arcsec_yr']})\nBrightness steady within ~5%", color=FG, fontsize=13, va="top")
    pdf.savefig(fig, facecolor=BG); plt.close(fig)

    # 6 results: faint + variables
    fig = slide("Results: faint movers and variable stars", "Honest outcomes, including what the tool cannot do yet")
    img(fig, strip(sorted((O / "wise_0855_d6" / "epochs").glob("frame_*.png"))), [0.02, 0.47, 0.56, 0.36])
    img(fig, O / "rw_aurigae_d1" / "rw_aurigae_lightcurve.png", [0.02, 0.05, 0.56, 0.38])
    fig.text(0.60, 0.80, "WISE 0855 (D6, 4.4–5.0 µm)", color=ACC, fontsize=15, weight="bold", va="top")
    fig.text(0.60, 0.755, "Detected in the Nov–Dec 2025 and Apr–May 2026\nstacks (S/N ≈ 30). Shift 3.3\" west vs 3.6\" predicted:\nhalf a pixel — measurable, hard to see by eye.\nThe May 2025 stack (3 frames) is unreliable.", color=FG, fontsize=12, va="top")
    fig.text(0.60, 0.50, "RW Aurigae (D1)", color=ACC, fontsize=15, weight="bold", va="top")
    fig.text(0.60, 0.455, "No motion (0.2\"). Unsaturated frames at ~0.75 µm:\n≈74–89 → 116–125 → 181–193 mJy\n(Sep 2025 → Mar 2026 → Sep 2026).\nCandidate ~2× brightening, not confirmed.", color=FG, fontsize=12, va="top")
    fig.text(0.60, 0.27, "R Draconis", color=ACC, fontsize=15, weight="bold", va="top")
    fig.text(0.60, 0.225, "No motion (0.5\"). Saturated in all 6 bands, so\nits Mira variability can't be measured this way yet.", color=FG, fontsize=12, va="top")
    pdf.savefig(fig, facecolor=BG); plt.close(fig)

    # 7 impact + credits
    fig = slide("Impact, next steps, credits")
    y = bullets(fig, [
        "Anyone can open a patch of sky and see SPHEREx change over time — students, Backyard Worlds-style citizen science.",
        "Validated on real data: known movers recovered at the catalog rate; non-movers stay still.",
        "Next: PSF-wing photometry for saturated stars, coadds across bands, Gaia/AllWISE overlays, known-asteroid labels.",
    ], y=0.82, size=15, dy=0.07)
    fig.text(0.04, y - 0.02, "Credits", color=ACC, fontsize=16, weight="bold", va="top")
    bullets(fig, [
        "Data: NASA SPHEREx (JPL/Caltech, funded by NASA) via NASA/IPAC IRSA. Positions/PMs: SIMBAD (Gaia EDR3; Kirkpatrick+2021; van Leeuwen 2007).",
        "Code: Python, numpy, scipy, astropy, matplotlib, Pillow, requests, Streamlit, ffmpeg. Inspiration: WiseView.",
        "AI use: an AI assistant helped write code and text; the team member directed, reviewed and tested it.\nAll results come from real IRSA data — no AI-generated images.",
        "This publication makes use of data products from SPHEREx, a joint project of JPL and Caltech, funded by NASA.",
    ], y=y - 0.08, size=12.5, dy=0.06)
    pdf.savefig(fig, facecolor=BG); plt.close(fig)
print("ok")
