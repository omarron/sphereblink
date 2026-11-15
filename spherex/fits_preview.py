"""Turn a SPHEREx cutout MEF into a stretched PNG preview.

Needs astropy and matplotlib. Masks FLAGS when that extension is present.
Does not measure or claim a detection.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def _find_hdu(hdulist, names: tuple[str, ...]):
    for hdu in hdulist:
        extname = str(hdu.name or "").strip().upper()
        if extname in names and getattr(hdu, "data", None) is not None:
            return hdu
    return None


def cutout_to_png(fits_path: Path, png_path: Path) -> dict:
    from astropy.io import fits
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    info = {"fits": str(fits_path), "png": str(png_path), "extensions": []}
    with fits.open(fits_path) as hdul:
        info["extensions"] = [hdu.name or "PRIMARY" for hdu in hdul]
        image_hdu = _find_hdu(hdul, ("IMAGE", "SCI", "PRIMARY"))
        if image_hdu is None:
            # Some cutouts store the science array in the first 2-D float HDU.
            for hdu in hdul:
                data = getattr(hdu, "data", None)
                if data is not None and getattr(data, "ndim", 0) == 2 and np.issubdtype(data.dtype, np.floating):
                    image_hdu = hdu
                    break
        if image_hdu is None or image_hdu.data is None:
            raise RuntimeError(f"No 2-D image array in {fits_path}. Extensions: {info['extensions']}")
        data = np.array(image_hdu.data, dtype=float)
        flags_hdu = _find_hdu(hdul, ("FLAGS", "FLAG", "DQ"))
        if flags_hdu is not None and flags_hdu.data is not None:
            flags = np.array(flags_hdu.data)
            if flags.shape == data.shape:
                # Mask only bad-pixel bits; SOURCE (bit 21) marks real stars and must stay.
                from .pipeline import BAD_MASK
                bad = (flags.astype(np.int64) & BAD_MASK) != 0
                data = np.where(bad, np.nan, data)
                info["flagged_pixels"] = int(np.sum(bad))
        info["extname"] = image_hdu.name
        info["shape"] = list(data.shape)

    finite = data[np.isfinite(data)]
    if finite.size == 0:
        raise RuntimeError("Image is all NaN after flag masking.")
    lo, hi = np.nanpercentile(finite, [5, 99.5])
    stretched = np.clip((data - lo) / (hi - lo + 1e-9), 0, 1)
    stretched = np.arcsinh(stretched * 3) / np.arcsinh(3)
    png_path = Path(png_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(4, 4), dpi=120)
    ax.imshow(stretched, origin="lower", cmap="gray")
    ax.set_xticks([])
    ax.set_yticks([])
    fig.tight_layout(pad=0)
    fig.savefig(png_path, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return info
