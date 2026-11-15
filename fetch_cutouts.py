#!/usr/bin/env python3
"""Download a few SPHEREx cutouts, grouped by detector/band, and make PNG previews.

Start with two visits of the same band. Blink those before you add more bands.
Example:
  python3 fetch_cutouts.py --target "WISE 0855" --band SPHEREx-D2 --limit 6
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from spherex.fits_preview import cutout_to_png
from spherex.irsa import WIDE_COLLECTIONS, download_cutout, query_sia
from spherex.targets import TARGETS, get_target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="WISE 0855", choices=list(TARGETS))
    parser.add_argument("--ra", type=float)
    parser.add_argument("--dec", type=float)
    parser.add_argument("--radius", type=float, default=0.05)
    parser.add_argument("--size", type=float, default=0.05, help="Cutout width in degrees")
    parser.add_argument("--band", default="SPHEREx-D2", help="SIA energy_bandpassname to keep")
    parser.add_argument("--limit", type=int, default=6, help="Max cutouts to download")
    parser.add_argument("--maxrec", type=int, default=200)
    parser.add_argument("--year", type=float)
    parser.add_argument("--out", type=Path, default=HERE / "cache")
    args = parser.parse_args()

    if args.ra is not None and args.dec is not None:
        ra, dec = args.ra, args.dec
        stem = "custom"
    else:
        info = get_target(args.target)
        pos = info["position"]
        if args.year:
            pos = pos.propagate(args.year)
        ra, dec = pos.ra_deg, pos.dec_deg
        stem = args.target.replace(" ", "_").replace("'", "")

    rows = query_sia(ra, dec, radius_deg=args.radius, collections=WIDE_COLLECTIONS, maxrec=args.maxrec)
    matched = [r for r in rows if (r.get("energy_bandpassname") or "") == args.band]
    # Keep one frame per t_min so dithers on the same visit don't dominate.
    unique = []
    seen = set()
    for row in matched:
        key = row.get("t_min")
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    print(f"SIA rows={len(rows)}  band {args.band}={len(matched)}  unique times={len(unique)}")
    if not unique:
        bands = sorted({r.get("energy_bandpassname") or "" for r in rows})
        print(f"No rows for {args.band}. Available bands: {bands}")
        return 1

    dest_dir = args.out / stem / args.band.replace("SPHEREx-", "")
    dest_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i, row in enumerate(unique[: args.limit], start=1):
        t_min = row.get("t_min") or f"{i}"
        fits_path = dest_dir / f"{i:02d}_{t_min}_{row.get('obs_id')}.fits"
        print(f"Downloading {fits_path.name} ...")
        download_cutout(row["access_url"], ra, dec, args.size, dest=fits_path)
        png_path = fits_path.with_suffix(".png")
        try:
            preview = cutout_to_png(fits_path, png_path)
            print(f"  preview {png_path.name} extensions={preview['extensions']}")
        except Exception as exc:
            print(f"  preview failed (install astropy/matplotlib?): {exc}")
            preview = {"error": str(exc)}
        manifest.append({"fits": str(fits_path), "png": str(png_path), "row": {k: row.get(k) for k in ("t_min", "obs_id", "energy_bandpassname", "obs_collection", "access_url")}, "preview": preview})

    manifest_path = dest_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {manifest_path}")
    print("Blink the PNGs in time order. Do not call a shift a discovery.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
