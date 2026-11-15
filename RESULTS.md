# SphereBlink results — run 15 Nov 2026 (PT) on live IRSA SPHEREx DR1 + QR3

Command: `python3 sphereblink.py --all` (+ `--target "WISE 0855" --band SPHEREx-D5` as a cross-check).
Each folder holds: `*_blink_all_visits.gif/.mp4` (every visit), `*_blink_epochs.gif` (median stack per survey pass),
`*_motion.png`, `*_lightcurve.png`, `*_first_last_diff.png`, `*_summary.json` (all numbers + per-visit metadata), `frames/`, `epochs/`.

Band choice came from a probe of 3 visits per band per target: Barnard's Star and R Dra saturate in every band; D5/D1 had the least saturation; WISE 0855 is only well detected at 4–5 µm.

| Target | Band | Visits | First→last epoch shift | Predicted | Verdict |
|---|---|---|---|---|---|
| Barnard's Star | D5 | 48 (Aug 2025–Sep 2026) | 10.22″ / 0.99 yr | 10.30″ | Moves north, clearly visible. Dec rate 9.99±0.42″/yr (cat. 10.36); RA −2.66±0.56 (cat. −0.80) is biased by saturation. |
| Epsilon Indi B | D5 | 42 (Apr 2025–Oct 2026) | 6.52″ / 1.43 yr | 6.68″ | Moves SE, visible. PM 3.56±0.31, −2.84±0.30″/yr (cat. 3.98, −2.47). Flux steady within ~5% at matched λ. |
| WISE 0855 | D6 | 45 (May 2025–May 2026) | 8.39″ (first epoch unreliable) | 7.97″ | Faint. Between the two reliable epochs (S/N≈30): 3.3″ W vs 3.6″ predicted. Half a pixel: measured, not obvious by eye. D5 cross-check disagrees (6.1″ vs 8.1″) → not trusted. |
| RW Aurigae | D1 | 48 (Sep 2025–Sep 2026) | 0.21″ | 0.02″ | No motion. 32/48 saturated. Unsaturated ~0.75 µm flux ≈74–89 → 116–125 → 181–193 mJy: candidate ~2× brightening, unconfirmed. |
| R Draconis | D1 | 48 (Jun 2025–Jul 2026) | 0.54″ | 0.02″ | No motion. Saturated in all bands → no valid photometry. |

Note: the WISE 0855 coordinates printed on the challenge page (08h55m10.831s −07°14′42.53″) are an ~2010 position. Propagating SIMBAD J2000 + Kirkpatrick et al. 2021 proper motion puts it ≈126″ W, 11″ N of that point in late 2025, outside a small cutout. SphereBlink uses the propagated position.
