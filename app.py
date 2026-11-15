#!/usr/bin/env python3
"""SphereBlink web app (Streamlit).

Type RA/Dec or pick a challenge test target -> live SPHEREx DR1/QR3 search at NASA/IPAC IRSA ->
aligned, time-sorted cutouts -> blink animation, position-vs-time and brightness plots.

Run:  python3 -m pip install -r requirements.txt && streamlit run app.py
Share a view with URL parameters: ?target=Barnard's%20Star  or  ?ra=269.446&dec=4.768&band=SPHEREx-D5
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import streamlit as st

from spherex.blink import run_target
from spherex.targets import TARGETS

BANDS = [f"SPHEREx-D{i}" for i in range(1, 7)]
BAND_HELP = {"SPHEREx-D1": "0.75–1.1 µm", "SPHEREx-D2": "1.1–1.6 µm", "SPHEREx-D3": "1.6–2.4 µm",
             "SPHEREx-D4": "2.4–3.8 µm", "SPHEREx-D5": "3.8–4.4 µm", "SPHEREx-D6": "4.4–5.0 µm"}

st.set_page_config(page_title="SphereBlink", layout="wide")
st.title("SphereBlink — blink SPHEREx visits of any patch of sky")
st.caption("Live data from NASA/IPAC IRSA (SPHEREx DR1 + QR3). Anything that seems to move or change is a "
           "candidate until checked against wavelength, FLAGS and known objects. Not affiliated with NASA.")

qp = st.query_params
names = list(TARGETS)
with st.sidebar:
    mode = st.radio("Look at", ["Challenge test target", "My own RA/Dec"],
                    index=1 if ("ra" in qp and "dec" in qp) else 0)
    if mode == "Challenge test target":
        default = qp.get("target", "Barnard's Star")
        name = st.selectbox("Target", names, index=names.index(default) if default in names else 0)
        info = TARGETS[name]
        st.caption(info["why"]); st.caption("Position: " + info["source"])
        band_default = info.get("band", "SPHEREx-D2")
        ra = dec = None
    else:
        name = None
        ra = st.number_input("RA (deg, ICRS)", value=float(qp.get("ra", 269.4463)), format="%.5f")
        dec = st.number_input("Dec (deg, ICRS)", value=float(qp.get("dec", 4.7676)), format="%.5f")
        band_default = qp.get("band", "SPHEREx-D2")
    band = st.selectbox("Detector band (blink only one band at a time)", BANDS, index=BANDS.index(band_default) if band_default in BANDS else 1,
                        format_func=lambda b: f"{b}  ({BAND_HELP[b]})")
    size = st.slider("Field of view (deg)", 0.03, 0.10, 0.05, 0.01)
    max_frames = st.slider("Max visits to download", 6, 60, 36, 6,
                           help="Each cutout is ~4 MB from IRSA; first run of a field takes a few minutes, then it is cached.")
    go = st.button("Search & blink", type="primary")

key = (name, ra, dec, band, size, max_frames)
if go:
    msgs = st.empty()
    log_lines: list[str] = []
    def log(m):
        log_lines.append(str(m)); msgs.code("\n".join(log_lines[-8:]))
    try:
        with st.spinner("Querying IRSA and downloading cutouts…"):
            summary = run_target(target=name, ra=ra, dec=dec, band=band, size_deg=size, max_frames=max_frames,
                                 out_dir=HERE / "outputs" / "app", log=log)
        st.session_state["result"] = (key, summary)
        st.query_params.clear()
        if name:
            st.query_params.update({"target": name, "band": band})
        else:
            st.query_params.update({"ra": f"{ra:.5f}", "dec": f"{dec:.5f}", "band": band})
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not finish: {exc}")
        st.stop()

res = st.session_state.get("result")
if not res:
    st.info("Pick a target (or type RA/Dec) and press **Search & blink**. Nothing is precomputed: every run queries IRSA live.")
    st.stop()

_, s = res
from spherex.pipeline import slugify
d = HERE / "outputs" / "app" / f"{slugify(s['target'])}_{s['band'].split('-')[-1].lower()}"
slug = slugify(s["target"])
st.subheader(f"{s['target']} — {s['band']} — {s['n_frames_used']} visits, {s['date_range_utc'][0]} to {s['date_range_utc'][1]}")
c1, c2 = st.columns(2)
with c1:
    st.image(str(d / f"{slug}_blink_all_visits.gif"), caption="Every visit in time order. Green ticks = fixed reference (mean-epoch position); cyan circle = catalog proper-motion prediction; orange + = measured centroid.")
with c2:
    st.image(str(d / f"{slug}_blink_epochs.gif"), caption="Median stack of each survey epoch (better signal-to-noise).")
st.image(str(d / f"{slug}_motion.png"))
st.image(str(d / f"{slug}_lightcurve.png"))
if (d / f"{slug}_first_last_diff.png").exists():
    st.image(str(d / f"{slug}_first_last_diff.png"))
m = s["motion"]
st.markdown("**Motion summary** (offsets measured from the frames, compared with the catalog):")
st.json(m)
if s.get("saturated_frames"):
    st.warning(f"{s['saturated_frames']} of {s['n_frames_used']} frames are saturated/overflowed at the target: fluxes there are lower limits.")
if s["matched_wavelength_brightness"]:
    st.markdown("**Brightness at matched wavelength between epochs** (ratio later/earlier):")
    st.json(s["matched_wavelength_brightness"])
with st.expander("All frames (metadata)"):
    st.dataframe(s["frames"])
st.download_button("Download summary JSON", json.dumps(s, indent=2), file_name=f"{slug}_summary.json")
st.caption("This publication makes use of data products from SPHEREx, a joint project of JPL and Caltech funded by NASA; data served by NASA/IPAC IRSA.")
