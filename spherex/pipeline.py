"""SphereBlink pipeline: SPHEREx visits -> aligned, time-sorted cutouts -> blink + plots.

Everything here comes from live NASA/IPAC IRSA services (SIA2 + cutout service).
Nothing is simulated. Results are written with the metadata needed to check them.

Steps
  1. resolve a target name or RA/Dec (with optional proper motion)
  2. query SIA2 (spherex_dr1 + spherex_qr3), cached as JSON
  3. pick one detector band, de-duplicate exposures, download cutouts in parallel (cached)
  4. per frame: subtract ZODI model, mask bad-pixel FLAGS, read the per-pixel wavelength
     at the target (WCS-WAVE lookup), reproject onto one common sky grid
  5. measure a flux-weighted centroid and aperture flux near the target in every frame
     and in per-epoch median stacks
  6. write blink GIF/MP4, motion plot, light-curve plot, and a JSON summary
"""

from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import math
import re
import shutil
import subprocess
import warnings
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from astropy import log as _alog
_alog.setLevel("ERROR")

from .coords import SkyPosition
from .irsa import IrsaError, download_cutout, query_sia
from .targets import TARGETS

HERE = Path(__file__).resolve().parent.parent
CACHE = HERE / "cache"

# FLAGS bits treated as "do not use" for display and measurement.
# SOURCE (bit 21) is NOT masked: it marks pixels on known stars, i.e. our targets.
# OVERFLOW (1) and NONLINEAR (15) are reported but not masked, so bright stars keep
# their cores; check the saturation note in the summary before trusting a bright flux.
BAD_BITS = {0: "TRANSIENT", 2: "SUR_ERROR", 6: "NONFUNC", 9: "MISSING_DATA",
            10: "HOT", 11: "COLD", 19: "OUTLIER"}
WARN_BITS = {1: "OVERFLOW", 15: "NONLINEAR", 17: "PERSIST", 22: "GHOST", 25: "STREAK"}
BAD_MASK = sum(1 << b for b in BAD_BITS)
WARN_MASK = sum(1 << b for b in WARN_BITS)

NATIVE_PIX_ARCSEC = 6.15
GRID_PIX_ARCSEC = 3.075          # 2x oversampled common grid
SR_PER_ARCSEC2 = (math.pi / 180 / 3600) ** 2


# --------------------------------------------------------------------------- targets
def mjd_to_year(mjd: float) -> float:
    return 2000.0 + (mjd - 51544.5) / 365.25


def mjd_to_iso(mjd: float, fmt: str = "%Y-%m-%d") -> str:
    return (datetime(1858, 11, 17) + timedelta(days=float(mjd))).strftime(fmt)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "target"


@dataclass
class Target:
    name: str
    position: SkyPosition
    source: str = ""
    default_band: str = "SPHEREx-D2"


def resolve(target: str | None = None, ra: float | None = None, dec: float | None = None,
            pm_ra: float | None = None, pm_dec: float | None = None, epoch: float = 2000.0) -> Target:
    """Official test-target name, 'RA Dec' text (deg or sexagesimal), or explicit numbers."""
    if ra is not None and dec is not None:
        pos = SkyPosition(float(ra), float(dec), epoch, pm_ra, pm_dec)
        return Target(f"RA {ra:.5f} Dec {dec:+.5f}", pos, "user-supplied coordinates")
    if not target:
        raise ValueError("Give a target name or RA/Dec.")
    key = target.strip().lower().replace("’", "'")
    for name, info in TARGETS.items():
        aliases = [name.lower()] + [a.lower() for a in info.get("aliases", [])]
        if key in aliases:
            return Target(name, info["position"], info.get("source", ""), info.get("band", "SPHEREx-D2"))
    # coordinates typed as text
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    try:
        parts = target.replace(",", " ").split()
        if len(parts) == 2 and all(re.fullmatch(r"[-+]?\d+(\.\d*)?", p) for p in parts):
            c = SkyCoord(float(parts[0]) * u.deg, float(parts[1]) * u.deg)
        else:
            c = SkyCoord(target, unit=(u.hourangle, u.deg))
        return Target(f"RA {c.ra.deg:.5f} Dec {c.dec.deg:+.5f}", SkyPosition(c.ra.deg, c.dec.deg), "user-supplied coordinates")
    except Exception:
        pass
    # last resort: name resolver (needs CDS Sesame; may be unreachable)
    try:
        c = SkyCoord.from_name(target)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not resolve {target!r}. Use RA/Dec in degrees. ({exc})") from exc
    return Target(target, SkyPosition(c.ra.deg, c.dec.deg), "CDS Sesame name resolver (no proper motion applied)")


# --------------------------------------------------------------------------- archive
def visits(tgt: Target, radius_deg: float = 0.005, year: float = 2025.9,
           collections=("spherex_dr1", "spherex_qr3"), maxrec: int = 3000, refresh: bool = False) -> list[dict]:
    """SIA2 rows covering the target, cached on disk. De-duplicated by exposure+detector (DR1 preferred)."""
    p = tgt.position.propagate(year)
    key = hashlib.sha1(f"{p.ra_deg:.5f}{p.dec_deg:.5f}{radius_deg}{collections}{maxrec}".encode()).hexdigest()[:12]
    path = CACHE / "sia" / f"{slugify(tgt.name)}_{key}.json"
    if path.exists() and not refresh:
        rows = json.loads(path.read_text())
    else:
        rows = query_sia(p.ra_deg, p.dec_deg, radius_deg, collections=collections, maxrec=maxrec, timeout=180)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows))
    if any(r.get("overflow") for r in rows):
        warnings.warn("IRSA returned OVERFLOW: raise maxrec, some visits are missing.")
    best: dict[str, dict] = {}
    rank = {"spherex_dr1": 0, "spherex_qr3": 1}
    for r in rows:
        k = f"{r.get('obs_id')}|{r.get('energy_bandpassname')}"
        if k not in best or rank.get(r["query_collection"], 9) < rank.get(best[k]["query_collection"], 9):
            best[k] = r
    out = sorted(best.values(), key=lambda r: float(r["t_min"]))
    return out


def split_epochs(mjds: list[float], gap_days: float = 30.0) -> list[int]:
    """Label each time with an epoch index; a new epoch starts after a gap > gap_days."""
    order = np.argsort(mjds)
    labels = [0] * len(mjds)
    e, last = 0, None
    for i in order:
        if last is not None and mjds[i] - last > gap_days:
            e += 1
        labels[i] = e
        last = mjds[i]
    return labels


def choose_rows(rows: list[dict], band: str, max_frames: int = 48) -> list[dict]:
    rows = [r for r in rows if r.get("energy_bandpassname") == band]
    if len(rows) <= max_frames:
        return rows
    # keep frames spread evenly across epochs so the time baseline is preserved
    labels = split_epochs([float(r["t_min"]) for r in rows])
    groups: dict[int, list[dict]] = {}
    for r, l in zip(rows, labels):
        groups.setdefault(l, []).append(r)
    per = max(2, max_frames // len(groups))
    keep = []
    for g in groups.values():
        idx = np.linspace(0, len(g) - 1, min(per, len(g))).round().astype(int)
        keep += [g[i] for i in sorted(set(idx))]
    return sorted(keep, key=lambda r: float(r["t_min"]))


def fetch(rows: list[dict], ra: float, dec: float, size_deg: float, workers: int = 5,
          log=print) -> list[tuple[dict, Path | None, str | None]]:
    """Download cutouts in parallel; cached by exposure, band and cutout center."""
    def one(r):
        name = f"{r['obs_id']}_{r['energy_bandpassname'][-2:]}_{ra:.4f}_{dec:.4f}_{size_deg:.3f}.fits"
        dest = CACHE / "cutouts" / name
        if dest.exists() and dest.stat().st_size > 2880:
            return r, dest, None
        last = None
        for _ in range(3):
            try:
                tmp = dest.with_suffix(".part")
                download_cutout(r["access_url"], ra, dec, size_deg, dest=tmp, timeout=180)
                tmp.rename(dest)
                return r, dest, None
            except IrsaError as exc:  # retry, then give up on this frame only
                last = str(exc)
        return r, None, last
    out = []
    with cf.ThreadPoolExecutor(workers) as ex:
        for i, res in enumerate(ex.map(one, rows), 1):
            out.append(res)
            if i % 8 == 0 or i == len(rows):
                log(f"  cutouts {i}/{len(rows)}")
    return out


# --------------------------------------------------------------------------- frames
@dataclass
class Frame:
    mjd: float
    obs_id: str
    band: str
    collection: str
    wavelength_um: float
    bandwidth_um: float
    image: np.ndarray            # on common grid, MJy/sr, zodi-subtracted, NaN = masked/outside
    warn_at_target: list = field(default_factory=list)
    bad_fraction: float = 0.0


def make_grid(ra: float, dec: float, size_deg: float):
    from astropy.wcs import WCS
    n = int(round(size_deg * 3600 / GRID_PIX_ARCSEC)) | 1
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [ra, dec]
    w.wcs.crpix = [(n + 1) / 2, (n + 1) / 2]
    w.wcs.cdelt = [-GRID_PIX_ARCSEC / 3600, GRID_PIX_ARCSEC / 3600]
    return w, n


def load_frame(path: Path, row: dict, grid_wcs, n: int, tgt_ra: float, tgt_dec: float) -> Frame:
    from astropy.io import fits
    from astropy.wcs import WCS, FITSFixedWarning
    from scipy.ndimage import map_coordinates
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fits.open(path) as hdul:
            hdr = hdul["IMAGE"].header
            img = np.array(hdul["IMAGE"].data, dtype=float)
            if "ZODI" in hdul:
                img = img - np.array(hdul["ZODI"].data, dtype=float)
            flags = np.array(hdul["FLAGS"].data, dtype=np.int64) if "FLAGS" in hdul else np.zeros_like(img, dtype=np.int64)
            sky = WCS(hdr)
            try:
                ww = WCS(hdr, fobj=hdul, key="W")
                ww.sip = None
            except Exception:  # noqa: BLE001
                ww = None
            mjd = float(hdr.get("MJD-AVG") or row["t_min"])
            x0, y0 = sky.world_to_pixel_values(tgt_ra, tgt_dec)
            lam = bw = float("nan")
            if ww is not None:
                lv, bv = ww.pixel_to_world_values(float(x0), float(y0))
                lam, bw = float(lv), float(bv)
    # Saturated star cores: IMAGE is NaN (or flagged OVERFLOW/SUR_ERROR/NONLINEAR) on a
    # pixel marked SOURCE. Keep them as a bright plateau (local max) instead of a hole, so
    # the star is still visible and its centroid still measurable. Flux is then a lower limit.
    sat_bits = (1 << 1) | (1 << 2) | (1 << 15)
    sat = ((flags & sat_bits) != 0) & ((flags & (1 << 21)) != 0)
    sat |= ~np.isfinite(img) & ((flags & (1 << 21)) != 0)
    n_sat_target = 0
    if sat.any():
        from scipy.ndimage import maximum_filter
        fin = np.where(np.isfinite(img) & ~sat, img, -np.inf)
        cap = maximum_filter(fin, size=5)
        cap = np.where(np.isfinite(cap), cap, np.nanmax(np.where(np.isfinite(img), img, np.nan)))
        img = np.where(sat, np.maximum(np.where(np.isfinite(img), img, -np.inf), cap), img)
    bad = ((flags & BAD_MASK) != 0) & ~sat
    xi, yi = int(round(float(x0))), int(round(float(y0)))
    warn = []
    if 0 <= yi < flags.shape[0] and 0 <= xi < flags.shape[1]:
        f0 = int(np.bitwise_or.reduce(flags[max(0, yi - 1):yi + 2, max(0, xi - 1):xi + 2], axis=None))
        warn = [nm for b, nm in WARN_BITS.items() if f0 & (1 << b)]
        n_sat_target = int(sat[max(0, yi - 2):yi + 3, max(0, xi - 2):xi + 3].sum())
        if n_sat_target:
            warn.append(f"SATURATED({n_sat_target}px)")
    good = np.isfinite(img) & ~bad
    fill = np.nanmedian(img[good]) if good.any() else 0.0
    src = np.where(good, img, fill)
    # common grid -> sky -> input pixel
    yy, xx = np.mgrid[0:n, 0:n]
    gra, gdec = grid_wcs.pixel_to_world_values(xx, yy)
    px, py = sky.world_to_pixel_values(gra, gdec)
    out = map_coordinates(src, [py, px], order=1, mode="constant", cval=np.nan)
    m = map_coordinates((~good).astype(float), [py, px], order=1, mode="constant", cval=1.0)
    out[m > 0.5] = np.nan
    return Frame(mjd, row["obs_id"], row["energy_bandpassname"], row["query_collection"], lam, bw,
                 out, warn, float(np.mean(~good)))


# --------------------------------------------------------------------------- measurement
def centroid(img: np.ndarray, x0: float, y0: float, r_ap: float, r_in: float, r_out: float, iters: int = 3):
    """Background-subtracted flux-weighted centroid near (x0,y0) on the grid, plus aperture flux sum."""
    n = img.shape[0]
    yy, xx = np.mgrid[0:n, 0:n]
    cx, cy = x0, y0
    for _ in range(iters):
        d = np.hypot(xx - cx, yy - cy)
        ann = img[(d >= r_in) & (d < r_out)]
        ann = ann[np.isfinite(ann)]
        if ann.size < 10:
            return None
        bg = np.median(ann)
        sel = (d < r_ap) & np.isfinite(img)
        if sel.sum() < 0.7 * np.pi * r_ap ** 2:
            return None
        w = np.clip(img[sel] - bg, 0, None)
        if w.sum() <= 0:
            return None
        nx, ny = (xx[sel] * w).sum() / w.sum(), (yy[sel] * w).sum() / w.sum()
        # never wander more than the aperture radius from the starting guess
        if math.hypot(nx - x0, ny - y0) > r_ap:
            return None
        cx, cy = nx, ny
    d = np.hypot(xx - cx, yy - cy)
    sel = (d < r_ap) & np.isfinite(img)
    ann = img[(d >= r_in) & (d < r_out)]
    ann = ann[np.isfinite(ann)]
    bg = np.median(ann)
    noise = 1.4826 * np.median(np.abs(ann - bg))
    flux = float(np.nansum(img[sel] - bg))
    err = float(noise * math.sqrt(sel.sum()))
    return {"x": float(cx), "y": float(cy), "flux_sum": flux, "flux_err": err, "snr": flux / err if err > 0 else 0.0}


def predicted_offsets(pos: SkyPosition, center_ra: float, center_dec: float, mjd: float):
    p = pos.propagate(mjd_to_year(mjd))
    dra = (p.ra_deg - center_ra) * math.cos(math.radians(center_dec)) * 3600
    ddec = (p.dec_deg - center_dec) * 3600
    return dra, ddec, p


def fit_motion(t_yr, x_arcsec, w=None):
    """Weighted straight-line fit; returns slope (arcsec/yr) and its 1-sigma error."""
    t = np.asarray(t_yr); x = np.asarray(x_arcsec)
    w = np.ones_like(t) if w is None else np.asarray(w)
    if len(t) < 2 or np.ptp(t) == 0:
        return float("nan"), float("nan")
    A = np.vstack([t - t.mean(), np.ones_like(t)]).T
    W = np.diag(w)
    cov = np.linalg.pinv(A.T @ W @ A)
    beta = cov @ A.T @ W @ x
    res = x - A @ beta
    dof = max(1, len(t) - 2)
    s2 = float((w * res ** 2).sum() / dof)
    return float(beta[0]), float(math.sqrt(cov[0, 0] * s2))


# --------------------------------------------------------------------------- rendering
def _stretch(stack: np.ndarray):
    finite = stack[np.isfinite(stack)]
    lo, hi = np.percentile(finite, [2, 99.7])
    return lo, hi


def render_frames(frames, labels, out_png_dir: Path, center_ra, center_dec, pos, grid_n,
                  meas, title: str, scale_px: float = 8.0):
    """Render each aligned frame to a PNG with date/wavelength labels and markers."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    stack = np.array([f.image for f in frames])
    lo, hi = _stretch(stack)
    out_png_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    c = (grid_n - 1) / 2
    for i, (f, lab) in enumerate(zip(frames, labels)):
        fig = plt.figure(figsize=(4.2, 4.6), dpi=110)
        ax = fig.add_axes([0.02, 0.02, 0.96, 0.84])
        im = np.clip((f.image - lo) / (hi - lo + 1e-12), 0, 1)
        im = np.arcsinh(im * 8) / np.arcsinh(8)
        ax.imshow(np.where(np.isfinite(im), im, 0.0), origin="lower", cmap="gray", interpolation="bicubic")
        # sky orientation: grid has North up, East left (cdelt1 < 0)
        dra, ddec, _ = predicted_offsets(pos, center_ra, center_dec, f.mjd)
        px, py = c - dra / GRID_PIX_ARCSEC, c + ddec / GRID_PIX_ARCSEC
        if pos.pm_ra_cosdec_mas_yr:
            ax.add_patch(Circle((px, py), 12 / GRID_PIX_ARCSEC, fill=False, color="cyan", lw=1.2))
        m = meas[i]
        if m is not None:
            ax.plot(m["x"], m["y"], "+", color="orange", ms=10, mew=1.5)
        # fixed reticle at the mean-epoch position: movers drift relative to these ticks
        for (xa, ya, xb, yb) in ((c - 11, c, c - 6, c), (c + 6, c, c + 11, c), (c, c - 11, c, c - 6), (c, c + 6, c, c + 11)):
            ax.plot([xa, xb], [ya, yb], color="lime", lw=1.2)
        ax.set_xlim(-0.5, grid_n - 0.5); ax.set_ylim(-0.5, grid_n - 0.5)
        ax.set_xticks([]); ax.set_yticks([])
        bar = 30 / GRID_PIX_ARCSEC
        ax.plot([2, 2 + bar], [2.5, 2.5], color="yellow", lw=2)
        ax.text(2, 4, '30"', color="yellow", fontsize=8)
        ax.text(grid_n - 3, 3, "N up, E left", color="yellow", fontsize=7, ha="right")
        fig.text(0.5, 0.955, title, ha="center", fontsize=10, weight="bold")
        fig.text(0.5, 0.905, lab, ha="center", fontsize=8.5)
        p = out_png_dir / f"frame_{i:03d}.png"
        fig.savefig(p); plt.close(fig)
        paths.append(p)
    return paths


def write_gif(pngs, path: Path, fps: float = 3.0):
    from PIL import Image
    ims = [Image.open(p).convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for p in pngs]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=int(1000 / fps), loop=0, optimize=True)


def write_mp4(png_dir: Path, path: Path, fps: float = 3.0) -> bool:
    if not shutil.which("ffmpeg"):
        return False
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(png_dir / "frame_%03d.png"),
           "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-pix_fmt", "yuv420p", "-c:v", "libx264", str(path)]
    return subprocess.run(cmd).returncode == 0
