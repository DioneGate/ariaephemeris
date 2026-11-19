# RM-001/007 — WP5.4 Astrological Coordinate Qualification

**Measured:** 19 November 2026 · **Profile:** `planet-centres-v1` (opt-in) · **Scope:** geocentric, airless apparent, **tropical true ecliptic/equinox of date, IAU 2006/2000A** at explicit TT · **Status:** sampled external-source coordinate agreement measured; **commercial physical accuracy NOT certified**.

**Source evidence:** [WP5.1 original 150 apparent directions](../../../data/fixtures/horizons/horizons-reference-v1.json), [WP5.4 780 additional inertial rays and their raw JPL responses](../../../data/fixtures/horizons/wp54-tropical/wp54-horizons-tropical-stencils-v1.json), [all 186 signed tropical coordinate/rate comparisons](../../validation/wp54-tropical-coordinate-comparison.json), [draft PR #12](https://github.com/DioneGate/ariaephemeris/pull/12).

## Executive result

**186 physical-centre astrological coordinate samples** (6 planets × 31 dates), including stationary and zodiac-sign ingress neighbourhoods, were compared against independently sourced JPL Horizons apparent inertial RA/Dec values. Each ray was independently transformed *in a separate code path* from ICRF to the IAU 2006/2000A **true tropical ecliptic of date**, using direct SOFA/ERFA functions; the reference angular rate comes from **five independent Horizons observations over ±0.025 TT days**, not from Aria's `longitude_rate_deg_day` or engine frame function.

All measured longitude/latitude residuals are below the proposed **0.05 arcsecond** external engineering diagnostic level; all signed longitude-rate residuals are below proposed **0.0001 degree/TT-day** diagnostic level. The recorded sample contains **zero motion-sign mismatches outside the near-station ambiguity band** and **zero sign-index mismatches away from zodiac boundaries**.

These are observed *JPL source-to-Aria model comparisons*. **Neither the candidate levels nor the 186 finite samples establish an absolute physical uncertainty bound or a formal commercial release pass**.

### Measured per-planet maximum absolute residual

| Physical body | Tropical longitude (arcsec) | Tropical latitude (arcsec) | Signed rate (degrees/TT day) | Motion-sign disagreements outside band | Sign disagreements away from cusps |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mars (499) | **0.00443295** | 0.00018673 | 6.2280 × 10⁻⁸ | 0 | 0 |
| Jupiter (599) | 0.00067521 | **0.00478592** | 4.1809 × 10⁻⁸ | 0 | 0 |
| Saturn (699) | 0.00016073 | 0.00004127 | 4.4469 × 10⁻⁸ | 0 | 0 |
| Uranus (799) | 0.00000444 | 0.00000191 | 4.8147 × 10⁻⁸ | 0 | 0 |
| Neptune (899) | 0.00001370 | 0.00000584 | 4.0627 × 10⁻⁸ | 0 | 0 |
| Pluto (999) | 0.00085748 | 0.00081508 | 3.1059 × 10⁻⁸ | 0 | 0 |

The full JSON report includes each body's **31 records, maximum, RMS and 95th-percentile residuals**, signed longitude/latitude/rate differences, motion classifications, zodiac sign indices and indicators for ambiguous boundary cases. No sampled value exceeded either provisional diagnostic threshold; this is a **sample-specific observation, not a claim about continuous 1900–2100 coverage**.

## Fixture design and independence

| Reference layer | Source and semantics | Scope |
| --- | --- | --- |
| Original external positions | Previously SHA-256-frozen NASA/JPL Horizons quantity **45** (ICRF inertial apparent RA/Dec, airless, Earth geocentre 399, TT) | **150 directions**: six planets × 25 predetermined dates |
| Additional reference epochs | Horizons at **t ± 0.0125** and **t ± 0.025 TT days** for baseline dates, plus the same five-point stencil at new critical dates; serial queries, archived original raw responses, source-model names, exact request URLs and SHA-256 | **780 new directions** across 18 JPL requests |
| Complete reference stencils | All existing and new independent JPL rays used exactly as stored, never replaced by Aria outputs | **930 directions** required for 186 five-point derivative cases |
| Stress test selectors | Aria's opt-in physical-centre engine nominated one geocentric **station** and one **30° zodiac ingress** per body in 2023–2025, then selected the estimated event time and ±0.25 TT days | Six additional chart cases per planet; **36 critical cases** |
| Main comparison | External ICRF direction → independent code-path IAU 2006/2000A ecliptic conversion, independent 0.0125-day five-point signed rate vs Aria's 0.001-day complete-pipeline derivative | 186 tropical longitude, latitude and rate records |

**Independence disclosure:** Horizons' source observations and Aria's calculation output are independently obtained, including physically distinct JPL planetary/observer source models. The frame transformation is implemented separately from Aria code, but **both rely on the same ERFA 2.0.1.5 IAU 2006/2000A precession/nutation primitives**. Thus this exercise checks Aria's pipeline and frame-convention wiring against an independent sky-position source; **it is not a fully independent reimplementation of precession/nutation, nor an observational truth-model accuracy certificate**.

**Critical-time selection:** Aria nominates the stress dates, NOT the expected positions, signed rates or independent event timing reference. This provides a meaningful nearby stress test but **does not qualify station or zodiac ingress root timing**; those are WP5.5 outcomes. A sign classification within **0.05 arcseconds** of a cusp and motion classification where either `|rate| <= 0.0002 degrees/day` are considered ambiguous, never automatically labelled a failure or a proof of an exact boundary.

## Method, integrity and regression gates

- Uses `PositionRequest(profile="planet-centres-v1", origin="geocentric", position_mode="apparent", frame="true_ecliptic_of_date", zodiac="tropical")` for each reference TT epoch; checks target ID (499/599/699/799/899/999), Earth centre 399, profile, time scale and frame.
- External independent conversion builds ICRF Cartesian unit ray from Horizons inertial RA/Dec, applies `PNM06A` and a closed-form rotation by `OBL06 + NUT06A` at **each individual TT instant**; spherical longitude/latitude extraction handles 0/360 wrapping.
- Independent rate uses `[f(-2h) - 8f(-h) + 8f(+h) - f(+2h)]/(12h)`, `h=0.0125 TT day`, with each longitude unwrapped relative to the central JPL observation. This explicitly includes the moving ecliptic frame; Aria uses `h=0.001 TT day`, full apparent pipeline.
- [Offline source integrity verifier](../../../tools/datasets/verify_wp54_tropical.py) reconstructs all 780 new RA/Dec values from their original JPL response bytes, checks raw SHA-256 and request/target/source-frame semantics, confirms all 150 WP5.1 original rays, verifies 930 required 5-point samples, and refuses missing/duplicated/mislabelled records.
- [Mathematical/unit tests](../../../tests/unit/test_wp54_tropical_qualification.py) exercise a true-to-inertial inverse projection, signed retrograde rate across Aries 0/360, motion induced by true-of-date frame rotation, station/ingress bracketing, missing-data failures and candidate diagnostic definitions.
- The one-time capture used the **original six SHA-256 verified satellite kernels and DE442s**, passed the numerical and integrity stages, then the generated external data was recovered from a retained GitHub Actions artefact after an unrelated concurrent Git push prevented the first branch update. The [artefact recovery run #44485106448](https://github.com/DioneGate/ariaephemeris/actions/runs/44485106448) **passed** original-response verification and unit tests before committing the frozen dataset; no duplicate Horizons request was needed.
- See [WP5.4 PR review workflow](../../../.github/workflows/wp54-review-validation.yml) for offline integrity and full real-kernel **byte-for-byte regenerated** comparison gates; see actual workflow run outcomes in [progress](progress.md). Acquisition is **manual-only**, ordinary tests are offline.

## What this qualifies — and what remains open

**Delivered:** Independent-source, externally anchored **tropical ecliptic coordinate and signed-rate comparison** for the opt-in physical Mars–Pluto centres at 31 strategically chosen epochs per body, with verifiable original sources, numerical statistics and edge-case coverage. Existing `reference` default computations and Aria Galaxy are untouched.

**Still not demonstrated:** Absolute physical ephemeris uncertainty, approved full-period continuous accuracy bounds, alternate IAU frame independent from ERFA, independent exact station/ingress event times, event search completeness, outer-body velocity error source-budget reconciliation for Mars/Saturn/Uranus/Neptune, inner planets/Sun/Moon chart parity, topocentric Earth rotation accuracy, commercial compact SPK pack size/performance, application provider switch or release.

### Suggested next bounded work

1. **WP5.5 — independent event-root timing:** freeze JPL-derived *time-of-event* fixtures from independently defined signed longitude and derivative functions; bracket/refine ingress/station roots in TT with independent horizons samples. Require separate timing/conditioning thresholds, especially nearly stationary or grazing event conditions.
2. **Four remaining planetary source-model uncertainty diagnoses:** prioritise Neptune's unusually prominent geometric velocity residual from WP5.2; quantify the DE441-vs-DE442s origin and physical-centre offset term for all four remaining planets before final scientific model acceptance.
3. **Commercial release gate:** approve product-defined error/operating intervals and accept samples, plus a distinct absolute physical source model uncertainty disclosure. Expand dense epoch sampling and qualifier automation before advertising continuous precision.

The measured result supports progress towards commercial reliability, **not permission to publish a numerical guarantee or deploy Aria Galaxy**.
