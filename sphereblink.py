#!/usr/bin/env python3
"""SphereBlink command line.

Examples
  python3 sphereblink.py --target "Barnard's Star"
  python3 sphereblink.py --ra 269.4463 --dec 4.7676 --band SPHEREx-D2
  python3 sphereblink.py --all            # the five challenge targets
"""
import argparse, json, sys, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from spherex.blink import run_target
from spherex.targets import TARGETS

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--target"); ap.add_argument("--ra", type=float); ap.add_argument("--dec", type=float)
ap.add_argument("--pm-ra", type=float, help="mas/yr (RA*cosDec), epoch J2000"); ap.add_argument("--pm-dec", type=float)
ap.add_argument("--band", help="SPHEREx-D1 … SPHEREx-D6 (default per target, else D2)")
ap.add_argument("--size", type=float, default=0.05, help="field of view in degrees")
ap.add_argument("--max-frames", type=int, default=48)
ap.add_argument("--out", default=str(HERE / "outputs"))
ap.add_argument("--all", action="store_true")
a = ap.parse_args()
jobs = [dict(target=t) for t in TARGETS] if a.all else [dict(target=a.target, ra=a.ra, dec=a.dec, pm_ra=a.pm_ra, pm_dec=a.pm_dec)]
status = 0
for j in jobs:
    try:
        s = run_target(**j, band=a.band, out_dir=a.out, size_deg=a.size, max_frames=a.max_frames)
        print(json.dumps({k: s[k] for k in ("target", "band", "n_frames_used", "date_range_utc", "motion", "matched_wavelength_brightness")}, indent=1))
    except Exception as exc:
        status = 1
        print(f"ERROR for {j}: {exc}", file=sys.stderr); traceback.print_exc()
sys.exit(status)
