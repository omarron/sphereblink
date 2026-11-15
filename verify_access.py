#!/usr/bin/env python3
"""Check that the IRSA endpoints this starter uses are reachable.

Prints what worked and what did not. Never invents visit counts you did not
just receive. Run:  python3 verify_access.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from spherex.irsa import (  # noqa: E402
    ALL_COLLECTIONS,
    SIA_URL,
    TAP_URL,
    WIDE_COLLECTIONS,
    cutout_url,
    query_sia,
)
from spherex.targets import get_target  # noqa: E402


def main() -> int:
    target = get_target("WISE 0855")
    pos = target["position"]
    print(f"Target: WISE 0855  RA={pos.ra_deg:.6f}  Dec={pos.dec_deg:.6f}")
    print(f"Source: {target['source']}")
    print()

    any_ok = False
    for collection in WIDE_COLLECTIONS:
        print(f"SIA2 {collection} ...")
        try:
            rows = query_sia(pos.ra_deg, pos.dec_deg, radius_deg=0.05, collections=[collection], maxrec=200)
        except Exception as exc:
            print(f"  FAILED: {exc}")
            continue
        overflow = any(r.get("overflow") for r in rows)
        times = sorted({r.get("t_min") for r in rows if r.get("t_min")})
        bands = sorted({r.get("energy_bandpassname") or "" for r in rows})
        print(f"  HTTP ok, rows={len(rows)}, unique t_min={len(times)}, overflow={overflow}")
        if times:
            print(f"  t_min range: {times[0]} -> {times[-1]}  bands: {', '.join(bands)}")
            any_ok = True
        else:
            print("  No rows. That can be real (no coverage) or a too-small cone.")

    if not any_ok:
        print("No SIA2 rows. Try IRSA's documented example position next.")
        try:
            demo = query_sia(127.69444, -39.17760, radius_deg=0.01, collections=["spherex_qr3"], maxrec=5)
            print(f"  Example QR3 cone rows={len(demo)}")
        except Exception as exc:
            print(f"  Example QR3 cone FAILED: {exc}")
            return 1

    print()
    print("Cutout of the first DR1 (or first available) row ...")
    rows = []
    for collection in WIDE_COLLECTIONS:
        try:
            rows = query_sia(pos.ra_deg, pos.dec_deg, radius_deg=0.05, collections=[collection], maxrec=5)
        except Exception:
            rows = []
        if rows:
            break
    if not rows:
        print("  No row to cut out.")
        return 1
    row = rows[0]
    dest = HERE / "cache" / "verify_cutout.fits"
    url = cutout_url(row["access_url"], pos.ra_deg, pos.dec_deg, 0.05)
    print(f"  GET {url}")
    try:
        response = requests.get(url, timeout=90)
        response.raise_for_status()
    except Exception as exc:
        print(f"  FAILED: {exc}")
        return 1
    ok = response.content.startswith(b"SIMPLE")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(response.content)
    print(f"  HTTP {response.status_code}, {len(response.content)} bytes, FITS={ok}, saved {dest}")

    print()
    print(f"TAP probe (optional; previously timed out): {TAP_URL}")
    query = (
        "SELECT TOP 1 obs_id FROM spherex.obscore "
        f"WHERE CONTAINS(POINT('ICRS', {pos.ra_deg}, {pos.dec_deg}), s_region) = 1"
    )
    try:
        response = requests.get(
            TAP_URL,
            params={"QUERY": query, "FORMAT": "csv"},
            timeout=20,
        )
        print(f"  HTTP {response.status_code}, {len(response.content)} bytes")
        print(f"  body starts: {response.text[:160]!r}")
    except Exception as exc:
        print(f"  FAILED or timed out: {exc}")
        print("  Use SIA2 instead; do not treat TAP as required for the MVP.")

    print()
    print(f"SIA endpoint: {SIA_URL}")
    print(f"Collections configured: {', '.join(ALL_COLLECTIONS)}")
    print("Done. Do not invent detections from this check.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
