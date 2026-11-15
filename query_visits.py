#!/usr/bin/env python3
"""List SPHEREx visits that cover a test target or an arbitrary RA/Dec.

Examples:
  python3 query_visits.py
  python3 query_visits.py --target "Barnard's Star" --year 2026.3
  python3 query_visits.py --ra 133.795129 --dec -7.245147 --radius 0.05
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from spherex.irsa import ALL_COLLECTIONS, WIDE_COLLECTIONS, query_sia
from spherex.targets import TARGETS, get_target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="WISE 0855", choices=list(TARGETS))
    parser.add_argument("--ra", type=float, help="RA in degrees; overrides --target")
    parser.add_argument("--dec", type=float, help="Dec in degrees; overrides --target")
    parser.add_argument("--radius", type=float, default=0.05, help="Search cone in degrees")
    parser.add_argument("--year", type=float, help="Propagate catalog proper motion to this year")
    parser.add_argument("--deep", action="store_true", help="Include SPHEREx deep-field collections")
    parser.add_argument("--maxrec", type=int, default=200)
    parser.add_argument("--csv", type=Path, help="Optional output table")
    args = parser.parse_args()

    if args.ra is not None and args.dec is not None:
        ra, dec = args.ra, args.dec
        label = f"custom {ra} {dec}"
    else:
        info = get_target(args.target)
        pos = info["position"]
        if args.year:
            pos = pos.propagate(args.year)
        ra, dec = pos.ra_deg, pos.dec_deg
        label = args.target
        print(f"# {label}")
        print(f"# {info['source']}")
        if info.get("note"):
            print(f"# {info['note']}")

    collections = ALL_COLLECTIONS if args.deep else WIDE_COLLECTIONS
    print(f"# RA={ra:.6f} deg  Dec={dec:.6f} deg  radius={args.radius} deg")
    rows = query_sia(ra, dec, radius_deg=args.radius, collections=collections, maxrec=args.maxrec)
    overflow = any(r.get("overflow") for r in rows)
    print(f"# rows={len(rows)}  overflow={overflow}")
    if overflow:
        print("# WARNING: MAXREC truncated the list; raise --maxrec or you may miss later epochs.")

    cols = ["t_min", "energy_bandpassname", "obs_id", "obs_collection", "access_url"]
    print("\t".join(cols))
    for row in rows:
        print("\t".join(str(row.get(c) or "") for c in cols))

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({c: row.get(c) for c in cols})
        print(f"# wrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
