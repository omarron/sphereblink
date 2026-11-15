"""IRSA SIA2 and cutout helpers for SPHEREx spectral images.

Verified from this environment on 2026-11-14 PT (see verify_access.py):
  - SIA2 COLLECTION=spherex_dr1 around WISE 0855 returned visits (HTTP 200).
  - SIA2 COLLECTION=spherex_qr3 worked for IRSA's documented example position
    (127.69444, -39.17760). A small cone on WISE 0855 returned 0 QR3 rows.
  - The on-premises cutout service returned a valid FITS MEF (~4 MB, HTTP 200).
  - TAP queries to https://irsa.ipac.caltech.edu/TAP/sync (spherex.obscore and
    allwise_p3as_psd) timed out with 0 bytes, so this starter uses SIA2 first.

Docs: https://irsa.ipac.caltech.edu/spherex-archive-documentation/spherex-data-access/
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SIA_URL = "https://irsa.ipac.caltech.edu/SIA"
TAP_URL = "https://irsa.ipac.caltech.edu/TAP/sync"

# DR1 + QR3 supersede QR2. QR2 is not searchable via SIA2.
WIDE_COLLECTIONS = ("spherex_dr1", "spherex_qr3")
DEEP_COLLECTIONS = ("spherex_dr1_deep", "spherex_qr3_deep")
ALL_COLLECTIONS = WIDE_COLLECTIONS + DEEP_COLLECTIONS


class IrsaError(RuntimeError):
    pass


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "SphereBlink-SpaceApps2026/0.1"})
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session


_SESSION = _session()


def _local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def query_sia(
    ra_deg: float,
    dec_deg: float,
    radius_deg: float = 0.05,
    collections: Iterable[str] = WIDE_COLLECTIONS,
    maxrec: int = 200,
    timeout: int = 60,
) -> list[dict]:
    """Return SPHEREx spectral images whose footprints cover this cone.

    Use a generous maxrec. A cap of 5-30 can return only one night of dithers
    even when later months of coverage exist (OVERFLOW).
    """
    rows: list[dict] = []
    for collection in collections:
        params = {
            "COLLECTION": collection,
            "POS": f"circle {ra_deg} {dec_deg} {radius_deg}",
            "RESPONSEFORMAT": "votable",
            "MAXREC": str(maxrec),
        }
        url = f"{SIA_URL}?{urlencode(params)}"
        try:
            response = _SESSION.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise IrsaError(f"SIA2 query failed for {collection}: {exc}") from exc
        chunk, overflow = _parse_votable(response.content)
        for row in chunk:
            row["query_collection"] = collection
            row["overflow"] = overflow
        rows.extend(chunk)
    rows.sort(key=lambda r: (float(r.get("t_min") or 0.0), r.get("energy_bandpassname") or ""))
    return rows


def _parse_votable(content: bytes) -> tuple[list[dict], bool]:
    root = ET.fromstring(content)
    overflow = any(
        (el.get("name") == "QUERY_STATUS" and el.get("value") == "OVERFLOW")
        for el in root.iter()
        if _local_tag(el.tag) == "INFO"
    )
    table = None
    for el in root.iter():
        # VOTABLE ends with "TABLE"; match the TABLE element only.
        if _local_tag(el.tag) == "TABLE":
            table = el
            break
    if table is None:
        return [], overflow
    fields = [child.get("name") for child in table.iter() if _local_tag(child.tag) == "FIELD"]
    rows = []
    for tr in table.iter():
        if _local_tag(tr.tag) != "TR":
            continue
        values = [td.text for td in list(tr) if _local_tag(td.tag) == "TD"]
        if len(values) != len(fields):
            continue
        rows.append(dict(zip(fields, values)))
    return rows, overflow


def cutout_url(access_url: str, ra_deg: float, dec_deg: float, size_deg: float = 0.05) -> str:
    """Append IRSA cutout parameters to an on-premises access_url."""
    if not access_url:
        raise IrsaError("Row has no access_url")
    joiner = "&" if "?" in access_url else "?"
    return f"{access_url}{joiner}center={ra_deg},{dec_deg}&size={size_deg}"


def download_cutout(
    access_url: str,
    ra_deg: float,
    dec_deg: float,
    size_deg: float = 0.05,
    dest: Path | None = None,
    timeout: int = 90,
) -> Path:
    url = cutout_url(access_url, ra_deg, dec_deg, size_deg)
    dest = Path(dest) if dest else Path("cache") / "cutout.fits"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        response = _SESSION.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise IrsaError(f"Cutout download failed: {exc}") from exc
    if not response.content.startswith(b"SIMPLE"):
        preview = response.content[:200].decode("ascii", "replace")
        raise IrsaError(f"Cutout response was not a FITS file: {preview!r}")
    dest.write_bytes(response.content)
    return dest
