"""Sexagesimal conversions and a simple linear proper-motion shift."""

from __future__ import annotations

from dataclasses import dataclass


def hms_to_deg(h: float, m: float, s: float) -> float:
    return 15.0 * (abs(h) + m / 60.0 + s / 3600.0)


def dms_to_deg(d: float, m: float, s: float) -> float:
    sign = -1.0 if d < 0 else 1.0
    return sign * (abs(d) + m / 60.0 + s / 3600.0)


def deg_to_hms(ra_deg: float) -> str:
    ra = ra_deg % 360.0
    hours = ra / 15.0
    h = int(hours)
    minutes = (hours - h) * 60.0
    m = int(minutes)
    s = (minutes - m) * 60.0
    return f"{h:02d}h{m:02d}m{s:06.3f}s"


def deg_to_dms(dec_deg: float) -> str:
    sign = "-" if dec_deg < 0 else "+"
    dec = abs(dec_deg)
    d = int(dec)
    minutes = (dec - d) * 60.0
    m = int(minutes)
    s = (minutes - m) * 60.0
    return f"{sign}{d:02d}d{m:02d}m{s:05.2f}s"


@dataclass(frozen=True)
class SkyPosition:
    ra_deg: float
    dec_deg: float
    epoch_year: float = 2000.0
    pm_ra_cosdec_mas_yr: float | None = None
    pm_dec_mas_yr: float | None = None

    def propagate(self, year: float) -> "SkyPosition":
        """Linear proper-motion shift. Good enough for a search cone, not a precise orbit."""
        if self.pm_ra_cosdec_mas_yr is None or self.pm_dec_mas_yr is None:
            return self
        dt = year - self.epoch_year
        import math

        dec = self.dec_deg + self.pm_dec_mas_yr * dt / 3.6e6
        cos_dec = math.cos(math.radians(dec)) or 1e-6
        ra = self.ra_deg + (self.pm_ra_cosdec_mas_yr * dt / 3.6e6) / cos_dec
        return SkyPosition(
            ra_deg=ra % 360.0,
            dec_deg=dec,
            epoch_year=year,
            pm_ra_cosdec_mas_yr=self.pm_ra_cosdec_mas_yr,
            pm_dec_mas_yr=self.pm_dec_mas_yr,
        )
