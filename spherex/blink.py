"""End-to-end SphereBlink run for one target. Used by sphereblink.py (CLI) and app.py."""

from __future__ import annotations

import json
import math
import shutil
import time
from pathlib import Path

import numpy as np

from . import pipeline as P

ERROR_PREFIX = "SphereBlink:"


def _arcsec_offsets(x, y, n):
    c = (n - 1) / 2
    return -(x - c) * P.GRID_PIX_ARCSEC, (y - c) * P.GRID_PIX_ARCSEC   # (dRA*cosDec east+, dDec north+)


def _find_reference_stars(img, n, avoid_xy, k=6, min_sep_pix=8):
    """Brightest isolated local maxima, away from the target and the edges."""
    from scipy.ndimage import maximum_filter
    a = np.where(np.isfinite(img), img, np.nanmedian(img))
    peaks = (a == maximum_filter(a, size=7)) & np.isfinite(img)
    ys, xs = np.nonzero(peaks)
    vals = a[ys, xs]
    order = np.argsort(vals)[::-1]
    out = []
    for i in order:
        x, y = xs[i], ys[i]
        if min(x, y, n - 1 - x, n - 1 - y) < 11:
            continue
        if math.hypot(x - avoid_xy[0], y - avoid_xy[1]) < 2 * min_sep_pix:
            continue
        if any(math.hypot(x - ox, y - oy) < min_sep_pix for ox, oy in out):
            continue
        out.append((float(x), float(y)))
        if len(out) >= k:
            break
    return out


def run_target(target: str | None = None, ra: float | None = None, dec: float | None = None,
               band: str | None = None, out_dir: Path | str = "outputs", size_deg: float = 0.05,
               max_frames: int = 48, radius_deg: float = 0.005, fps: float = 3.0,
               pm_ra: float | None = None, pm_dec: float | None = None, log=print) -> dict:
    t0 = time.time()
    tgt = P.resolve(target, ra, dec, pm_ra=pm_ra, pm_dec=pm_dec)
    band = band or tgt.default_band
    slug = P.slugify(tgt.name)
    out = Path(out_dir) / f"{slug}_{band.split('-')[-1].lower()}"
    out.mkdir(parents=True, exist_ok=True)
    log(f"[{tgt.name}] querying IRSA SIA2 (spherex_dr1 + spherex_qr3)…")
    rows = P.visits(tgt, radius_deg=radius_deg)
    if not rows:
        raise RuntimeError(f"{ERROR_PREFIX} IRSA returned no SPHEREx images covering {tgt.name}.")
    bands_available = sorted({r["energy_bandpassname"] for r in rows})
    if band not in bands_available:
        raise RuntimeError(f"{ERROR_PREFIX} no {band} images; available: {bands_available}")
    sel = P.choose_rows(rows, band, max_frames=max_frames)
    mjds = [float(r["t_min"]) for r in sel]
    mean_year = P.mjd_to_year(float(np.mean(mjds)))
    center = tgt.position.propagate(mean_year)
    cra, cdec = center.ra_deg, center.dec_deg
    log(f"[{tgt.name}] {len(rows)} images in all bands; using {len(sel)} in {band}, "
        f"{P.mjd_to_iso(min(mjds))} to {P.mjd_to_iso(max(mjds))}; center at epoch {mean_year:.2f}")
    got = P.fetch(sel, cra, cdec, size_deg * 1.5, log=log)
    failed = [(r["obs_id"], e) for r, p, e in got if p is None]
    grid, n = P.make_grid(cra, cdec, size_deg)
    frames = []
    for r, p, e in got:
        if p is None:
            continue
        try:
            f = P.load_frame(p, r, grid, n, cra, cdec)
        except Exception as exc:  # noqa: BLE001
            failed.append((r["obs_id"], f"unreadable cutout: {exc}"))
            continue
        core = f.image[n // 2 - 8:n // 2 + 9, n // 2 - 8:n // 2 + 9]
        if np.mean(np.isfinite(core)) < 0.6:
            failed.append((r["obs_id"], "target region mostly masked or off-frame"))
            continue
        frames.append(f)
    frames.sort(key=lambda f: f.mjd)
    if len(frames) < 2:
        raise RuntimeError(f"{ERROR_PREFIX} fewer than two usable frames for {tgt.name} in {band}.")
    epochs = P.split_epochs([f.mjd for f in frames])
    n_ep = max(epochs) + 1
    c = (n - 1) / 2
    r_ap, r_in, r_out = 4.0, 7.0, 12.0          # grid pixels (3.075")

    # --- per-frame measurements at the mean-epoch position (independent of the PM prediction)
    meas = [P.centroid(f.image, c, c, r_ap, r_in, r_out) for f in frames]
    pix_sr = (P.GRID_PIX_ARCSEC ** 2) * P.SR_PER_ARCSEC2
    rows_out = []
    for f, m, e in zip(frames, meas, epochs):
        dra_p, ddec_p, _ = P.predicted_offsets(tgt.position, cra, cdec, f.mjd)
        row = {"mjd": round(f.mjd, 5), "date_utc": P.mjd_to_iso(f.mjd, "%Y-%m-%d %H:%M"), "epoch": e,
               "obs_id": f.obs_id, "collection": f.collection, "band": f.band,
               "wavelength_um": round(f.wavelength_um, 4), "bandwidth_um": round(f.bandwidth_um, 4),
               "warn_flags_at_target": f.warn_at_target,
               "pred_dra_arcsec": round(dra_p, 2) if tgt.position.pm_ra_cosdec_mas_yr else None,
               "pred_ddec_arcsec": round(ddec_p, 2) if tgt.position.pm_ra_cosdec_mas_yr else None}
        if m:
            dx, dy = _arcsec_offsets(m["x"], m["y"], n)
            row.update({"meas_dra_arcsec": round(dx, 2), "meas_ddec_arcsec": round(dy, 2),
                        "flux_mjy": round(m["flux_sum"] * pix_sr * 1e9, 3),
                        "flux_err_mjy": round(m["flux_err"] * pix_sr * 1e9, 3), "snr": round(m["snr"], 1)})
        rows_out.append(row)

    # --- per-epoch median stacks (better S/N for motion)
    stacks, stack_meta = [], []
    for e in range(n_ep):
        idx = [i for i, x in enumerate(epochs) if x == e]
        with np.errstate(all="ignore"):
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                img = np.nanmedian(np.array([frames[i].image for i in idx]), axis=0)
        mj = float(np.mean([frames[i].mjd for i in idx]))
        lam = [frames[i].wavelength_um for i in idx]
        stacks.append(P.Frame(mj, f"epoch{e}", band, "stack", float(np.nanmedian(lam)), float("nan"), img))
        stack_meta.append({"epoch": e, "n_frames": len(idx), "mjd_mean": round(mj, 3),
                           "date_range_utc": f"{P.mjd_to_iso(min(frames[i].mjd for i in idx))} to {P.mjd_to_iso(max(frames[i].mjd for i in idx))}",
                           "wavelength_range_um": [round(float(np.nanmin(lam)), 3), round(float(np.nanmax(lam)), 3)]})
    smeas = [P.centroid(s.image, c, c, r_ap, r_in, r_out) for s in stacks]
    smeas = [m if (m and m["snr"] >= 5) else None for m in smeas]   # no source -> no position
    for sm, m in zip(stack_meta, smeas):
        if m:
            dx, dy = _arcsec_offsets(m["x"], m["y"], n)
            sm.update({"meas_dra_arcsec": round(dx, 2), "meas_ddec_arcsec": round(dy, 2), "snr": round(m["snr"], 1)})
        if tgt.position.pm_ra_cosdec_mas_yr:
            pdx, pdy, _ = P.predicted_offsets(tgt.position, cra, cdec, sm["mjd_mean"])
            sm.update({"pred_dra_arcsec": round(pdx, 2), "pred_ddec_arcsec": round(pdy, 2)})

    # --- control stars: measure the same thing on field stars (should not move)
    refs = _find_reference_stars(stacks[0].image, n, (c, c))
    ctrl = []
    for (rx, ry) in refs:
        tr = []
        for s in stacks:
            m = P.centroid(s.image, rx, ry, 3.0, 6.0, 10.0)
            tr.append(_arcsec_offsets(m["x"], m["y"], n) if m and m["snr"] > 10 else None)
        if all(t is not None for t in tr):
            ctrl.append(tr)
    ctrl_shift = []
    if ctrl and n_ep >= 2:
        for tr in ctrl:
            ctrl_shift.append(math.hypot(tr[-1][0] - tr[0][0], tr[-1][1] - tr[0][1]))
    # zero-point: median control-star shift per epoch relative to epoch 0, removed from target
    zp = [(0.0, 0.0)] * n_ep
    if len(ctrl) >= 3:
        zp = [(float(np.median([tr[e][0] - tr[0][0] for tr in ctrl])), float(np.median([tr[e][1] - tr[0][1] for tr in ctrl]))) for e in range(n_ep)]

    # --- motion fit from good per-frame measurements
    good = [(r, P.mjd_to_year(r["mjd"])) for r in rows_out if r.get("snr", 0) >= 5]
    motion = {"n_frames_used": len(good)}
    if len(good) >= 3 and np.ptp([g[1] for g in good]) > 0.2:
        ty = [g[1] for g in good]
        wts = [min(g[0]["snr"], 50) ** 2 for g in good]
        sx, ex = P.fit_motion(ty, [g[0]["meas_dra_arcsec"] for g in good], wts)
        sy, ey = P.fit_motion(ty, [g[0]["meas_ddec_arcsec"] for g in good], wts)
        motion.update({"pm_ra_cosdec_arcsec_yr": round(sx, 2), "pm_ra_err": round(ex, 2),
                       "pm_dec_arcsec_yr": round(sy, 2), "pm_dec_err": round(ey, 2),
                       "baseline_yr": round(float(np.ptp(ty)), 2)})
    sm_ok = [m for m in stack_meta if "meas_dra_arcsec" in m]
    if len(sm_ok) >= 2:
        ty = [P.mjd_to_year(m["mjd_mean"]) for m in sm_ok]
        wts = [m["n_frames"] for m in sm_ok]
        if len(sm_ok) == 2:
            dt = ty[1] - ty[0]
            motion["stack_pm_ra_cosdec_arcsec_yr"] = round((sm_ok[1]["meas_dra_arcsec"] - sm_ok[0]["meas_dra_arcsec"]) / dt, 2)
            motion["stack_pm_dec_arcsec_yr"] = round((sm_ok[1]["meas_ddec_arcsec"] - sm_ok[0]["meas_ddec_arcsec"]) / dt, 2)
        else:
            sx, ex = P.fit_motion(ty, [m["meas_dra_arcsec"] for m in sm_ok], wts)
            sy, ey = P.fit_motion(ty, [m["meas_ddec_arcsec"] for m in sm_ok], wts)
            motion.update({"stack_pm_ra_cosdec_arcsec_yr": round(sx, 2), "stack_pm_ra_err": round(ex, 2),
                           "stack_pm_dec_arcsec_yr": round(sy, 2), "stack_pm_dec_err": round(ey, 2)})
    if tgt.position.pm_ra_cosdec_mas_yr:
        motion["catalog_pm_ra_cosdec_arcsec_yr"] = round(tgt.position.pm_ra_cosdec_mas_yr / 1000, 3)
        motion["catalog_pm_dec_arcsec_yr"] = round(tgt.position.pm_dec_mas_yr / 1000, 3)
    if n_ep >= 2 and smeas[0] and smeas[-1]:
        a, b = stack_meta[0], stack_meta[-1]
        dx = b["meas_dra_arcsec"] - a["meas_dra_arcsec"] - zp[-1][0]
        dy = b["meas_ddec_arcsec"] - a["meas_ddec_arcsec"] - zp[-1][1]
        motion["first_to_last_epoch_shift_arcsec"] = round(math.hypot(dx, dy), 2)
        motion["first_to_last_epoch_dt_yr"] = round((b["mjd_mean"] - a["mjd_mean"]) / 365.25, 3)
        if tgt.position.pm_ra_cosdec_mas_yr:
            motion["predicted_shift_arcsec"] = round(math.hypot(b["pred_dra_arcsec"] - a["pred_dra_arcsec"], b["pred_ddec_arcsec"] - a["pred_ddec_arcsec"]), 2)
    motion["control_star_first_to_last_shift_arcsec"] = [round(x, 2) for x in ctrl_shift]
    motion["control_zero_point_last_epoch_arcsec"] = [round(v, 2) for v in zp[-1]]

    # --- matched-wavelength brightness comparison between epochs
    var = []
    for e1 in range(n_ep):
        for e2 in range(e1 + 1, n_ep):
            okr = [r for r in rows_out if r.get("snr", 0) >= 5 and not any(w.startswith("SATURATED") or w == "OVERFLOW" for w in r["warn_flags_at_target"])]
            A = sorted([(r["wavelength_um"], r["flux_mjy"]) for r in okr if r["epoch"] == e1])
            B = [(r["wavelength_um"], r["flux_mjy"], r["bandwidth_um"]) for r in okr if r["epoch"] == e2]
            pairs = []
            for lb, fb, bw in B:
                cand = [(abs(la - lb), fa) for la, fa in A if abs(la - lb) <= max(bw, 0.01)]
                if cand and min(cand)[1] > 0:
                    pairs.append(fb / min(cand)[1])
            if pairs:
                var.append({"epochs": [e1, e2], "n_matched_pairs": len(pairs),
                            "median_flux_ratio_later_over_earlier": round(float(np.median(pairs)), 3),
                            "ratio_scatter_mad": round(float(1.4826 * np.median(np.abs(np.array(pairs) - np.median(pairs)))), 3)})

    # --- renders
    title = f"{tgt.name} · SPHEREx {band.split('-')[-1]}"
    labels = [f"{P.mjd_to_iso(f.mjd, '%Y-%m-%d %H:%M')} UTC · λ={f.wavelength_um:.2f} µm · {f.collection.replace('spherex_', '').upper()}" for f in frames]
    for d in ("frames", "epochs"):
        shutil.rmtree(out / d, ignore_errors=True)
    pf = P.render_frames(frames, labels, out / "frames", cra, cdec, tgt.position, n, meas, title)
    P.write_gif(pf, out / f"{slug}_blink_all_visits.gif", fps=fps)
    mp4 = P.write_mp4(out / "frames", out / f"{slug}_blink_all_visits.mp4", fps=fps)
    slabels = [f"Epoch {m['epoch'] + 1}: {m['date_range_utc']} · median of {m['n_frames']}" for m in stack_meta]
    pe = P.render_frames(stacks, slabels, out / "epochs", cra, cdec, tgt.position, n, smeas, title)
    P.write_gif(pe, out / f"{slug}_blink_epochs.gif", fps=1.2)
    _plots(out, slug, tgt, rows_out, stack_meta, stacks, n, band)

    summary = {
        "target": tgt.name, "input": {"target": target, "ra": ra, "dec": dec},
        "position_source": tgt.source, "band": band, "bands_available": bands_available,
        "n_images_all_bands": len(rows), "n_selected": len(sel), "n_frames_used": len(frames),
        "failed_or_skipped": failed, "center_ra_deg": round(cra, 6), "center_dec_deg": round(cdec, 6),
        "center_epoch_year": round(mean_year, 3), "cutout_size_deg": size_deg,
        "collections_used": sorted({f.collection for f in frames}),
        "date_range_utc": [P.mjd_to_iso(frames[0].mjd), P.mjd_to_iso(frames[-1].mjd)],
        "epochs": stack_meta, "motion": motion, "matched_wavelength_brightness": var,
        "saturation_or_artifact_flags_frames": sum(1 for f in frames if f.warn_at_target),
        "saturated_frames": sum(1 for f in frames if any(w.startswith("SATURATED") or w == "OVERFLOW" for w in f.warn_at_target)),
        "frames": rows_out, "runtime_s": round(time.time() - t0, 1), "mp4": mp4,
        "files": sorted(str(p.name) for p in out.iterdir() if p.is_file()),
    }
    (out / f"{slug}_summary.json").write_text(json.dumps(summary, indent=2))
    log(f"[{tgt.name}] done: {len(frames)} frames, {n_ep} epochs, {summary['runtime_s']} s")
    return summary


def _plots(out, slug, tgt, rows, stack_meta, stacks, n, band):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    good = [r for r in rows if r.get("snr", 0) >= 5]
    yrs = lambda rs: [P.mjd_to_year(r["mjd"]) for r in rs]  # noqa: E731
    # motion
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), dpi=120)
    for ax, key, lab in ((axs[0], "dra", "ΔRA·cosDec (arcsec, east +)"), (axs[1], "ddec", "ΔDec (arcsec, north +)")):
        ax.scatter(yrs(good), [r[f"meas_{key}_arcsec"] for r in good], s=12, c="tab:orange", label="measured, single visit (S/N≥5)")
        sm = [m for m in stack_meta if "meas_dra_arcsec" in m]
        ax.errorbar([P.mjd_to_year(m["mjd_mean"]) for m in sm], [m[f"meas_{key}_arcsec"] for m in sm], fmt="s", color="k", ms=6, label="measured, epoch stack")
        if tgt.position.pm_ra_cosdec_mas_yr:
            pv = [r[f"pred_{key}_arcsec"] for r in rows]
            ax.plot(yrs(rows), pv, "-", color="tab:cyan", lw=2, label="catalog proper motion (predicted)")
        ax.axhline(0, color="0.8", lw=0.8)
        ax.set_xlabel("year"); ax.set_ylabel(lab)
    axs[0].legend(fontsize=7, loc="best")
    fig.suptitle(f"{tgt.name}: position vs time in SPHEREx {band.split('-')[-1]} (offsets from mean-epoch catalog position)", fontsize=9)
    fig.tight_layout(); fig.savefig(out / f"{slug}_motion.png"); plt.close(fig)
    # light curve + spectrum-by-epoch
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), dpi=120)
    ok = [r for r in rows if "flux_mjy" in r]
    satd = [r for r in ok if any(w.startswith("SATURATED") or w == "OVERFLOW" for w in r["warn_flags_at_target"])]
    if satd:
        axs[0].scatter(yrs(satd), [r["flux_mjy"] for r in satd], marker="x", color="red", s=30, zorder=5, label="saturated/overflow at target (flux = lower limit)")
        axs[0].legend(fontsize=7)
    if ok:
        sc = axs[0].scatter(yrs(ok), [r["flux_mjy"] for r in ok], c=[r["wavelength_um"] for r in ok], cmap="viridis", s=14)
        axs[0].errorbar(yrs(ok), [r["flux_mjy"] for r in ok], yerr=[r["flux_err_mjy"] for r in ok], fmt="none", ecolor="0.7", lw=0.6, zorder=0)
        plt.colorbar(sc, ax=axs[0], label="wavelength at target (µm)")
        cols = plt.cm.tab10.colors
        for e in sorted({r["epoch"] for r in ok}):
            rs = sorted([r for r in ok if r["epoch"] == e], key=lambda r: r["wavelength_um"])
            clean = [r for r in rs if r not in satd]
            dirty = [r for r in rs if r in satd]
            if clean:
                axs[1].plot([r["wavelength_um"] for r in clean], [r["flux_mjy"] for r in clean], "o-", ms=4, lw=0.8, color=cols[e % 10], label=f"epoch {e + 1} ({P.mjd_to_iso(rs[0]['mjd'])[:7]})")
            if dirty:
                axs[1].plot([r["wavelength_um"] for r in dirty], [r["flux_mjy"] for r in dirty], "o", ms=5, mfc="none", color=cols[e % 10], label=None if clean else f"epoch {e + 1} (saturated only)")
        axs[1].legend(fontsize=7)
    axs[0].set_xlabel("year"); axs[0].set_ylabel("aperture flux (mJy, 12\" radius, no aperture corr.)")
    axs[1].set_xlabel("wavelength at target (µm); open circles = saturated (lower limits)"); axs[1].set_ylabel("aperture flux (mJy)")
    fig.suptitle(f"{tgt.name}: brightness vs time (left) and vs wavelength per epoch (right). Compare only at matched wavelength.", fontsize=9)
    fig.tight_layout(); fig.savefig(out / f"{slug}_lightcurve.png"); plt.close(fig)
    # first vs last epoch + difference
    if len(stacks) >= 2:
        a, b = stacks[0].image, stacks[-1].image
        fig, axs = plt.subplots(1, 3, figsize=(10, 3.6), dpi=120)
        lo, hi = np.nanpercentile(np.concatenate([a[np.isfinite(a)], b[np.isfinite(b)]]), [2, 99.7])
        for ax, im, t in ((axs[0], a, f"epoch 1 ({stack_meta[0]['date_range_utc'][:7]})"), (axs[1], b, f"epoch {len(stacks)} ({stack_meta[-1]['date_range_utc'][:7]})")):
            ax.imshow(np.clip((im - lo) / (hi - lo), 0, 1) ** 0.5, origin="lower", cmap="gray"); ax.set_title(t, fontsize=9)
        d = b - a
        v = np.nanpercentile(np.abs(d[np.isfinite(d)]), 99.5)
        axs[2].imshow(d, origin="lower", cmap="RdBu_r", vmin=-v, vmax=v); axs[2].set_title("last − first (red = brighter later)", fontsize=9)
        for ax in axs:
            ax.plot((n - 1) / 2, (n - 1) / 2, "+", color="orange", ms=12); ax.set_xticks([]); ax.set_yticks([])
        fig.suptitle(f"{tgt.name}, SPHEREx {band.split('-')[-1]} epoch stacks. N up, E left. + = mean-epoch catalog position", fontsize=9)
        fig.tight_layout(); fig.savefig(out / f"{slug}_first_last_diff.png"); plt.close(fig)

