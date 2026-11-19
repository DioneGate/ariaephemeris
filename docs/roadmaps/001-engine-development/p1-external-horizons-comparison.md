# RM-001/005 — WP5.2 independent Horizons numerical comparison

**Measured on:** 19 November 2026 · **Profile:** `planet-centres-v1` · **Reference:** [WP5.1 immutable NASA/JPL Horizons fixtures](../../../data/fixtures/horizons/horizons-reference-v1.json) · **Detailed evidence:** [full per-fixture machine report](../../validation/wp5-2-horizons-comparison.json)

**Status:** completed external comparison with **source-model reconciliation outstanding**. The comparison is a new scientific measurement, **not** an independently model-matched physical ephemeris accuracy certification. A versioned source/model-difference review is required before approving production numerical tolerances.

## Observed results

The comparator loaded **all six original, SHA-256-pinned physical-centre SPKs** along with the verified Aria DE442s base and evaluated **300 frozen independent Horizons reference cases**, comprising 150 Earth-centred **geometric vectors at TDB** and 150 Earth-centred **inertial apparent RA/Dec directions at TT**. All records and source identities were complete and finite.

| Body | Horizons physical-centre source | Aria centre-offset source | Max geometric position difference (km) | Max geometric velocity difference (m/s) | Max apparent angular separation (arcsec) | Above provisional 1″ diagnostic threshold |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Mars | `mar099` | `mar099.bsp` | 3.831022 | 4.022e-4 | 4.418e-3 | 0/25 |
| Jupiter | `jup365_merged` | `jup349.bsp` | 14.816885 | 2.515e-4 | 4.789e-3 | 0/25 |
| Saturn | `sat441l` | `sat456.bsp` | 1.128083 | 6.682e-6 | 1.607e-4 | 0/25 |
| Uranus | `ura184_merged` | `ura184_part-3.bsp` | 1.751e-5 | 2.898e-9 | 4.520e-6 | 0/25 |
| Neptune | `nep098_merged` | `nep105.bsp` | 0.325495 | 6.379e-3 | 1.369e-5 | 0/25 |
| Pluto | `plu060_merged` | `plu060.bsp` | 40.913480 | 2.784e-5 | 1.157e-3 | 0/25 |

Across the entire 150-case apparent-direction sample, **0/150** exceeded the provisional 1-arcsecond *diagnostic* threshold. The largest observed apparent separation was **4.789e-3 arcseconds** (Jupiter); the largest geometric displacement difference was **40.913480 km** (Pluto). The greatest geometric velocity difference was **6.379e-3 m/s** (Neptune). The machine report includes per-planet RMS and p95 as well as every individual difference, original reference values, evaluated Aria states, source labels and original reference URLs/SHA in the frozen dataset.

These position/velocity differences are **differences between two ephemeris outputs**; they do not establish that Aria is inaccurate by the listed amount, nor do they establish a full physical uncertainty budget. The values are measured sample maxima over 25 dates per body, not a continuous bound over 1900–2100.

## Why a reference disagreement is not automatically an engine defect

Horizons uses source solutions selected by its own production service; Aria composes **DE442s** planetary barycentres with individually qualified original satellite SPKs. The reference target solutions are `mar099`, `jup365_merged`, `sat441l`, `ura184_merged`, `nep098_merged` and `plu060_merged`. Multiple Horizons reference headers also identify **DE441**, which differs from Aria's DE442s base. A shared target-family name alone is not proof of a fully matched source model.

The results are therefore classified **MEASURED_WITH_UNRECONCILED_SOURCE_MODELS**. Do **not** artificially widen an accuracy tolerance, infer an implementation bug from a raw mismatch, or record a physical-centre production-accuracy **Pass** from the 0/150 diagnostic threshold. There is no evidence yet of an independently matched dynamical source/observer combination or complete correction-model equivalence.

## Comparison methodology

- **Geometric TDB:** physical planet-centre SSB state minus Earth (399) SSB state, both from Aria at the **same TDB JD**; compare Horizons' ICRF 3D vectors in kilometres and convert Aria's km/day velocity to **km/s** before reporting m/s residuals.
- **Apparent TT:** request geocentric, `frame="icrs"`, `position_mode="apparent"`, physical profile at the Horizons **TT JD**; compare Aria's ICRF **longitude/latitude** as inertial RA/Dec against Horizons OBSERVER quantity 45. **Do not compare Aria's separate true-of-date RA/Dec output** to this inertial reference.
- **Angular separation:** unit-vector great-circle angular separation, robust at RA 0/360 and poles. Wrapped RA/Dec components, geometric Cartesian components and provenance stored per fixture.
- **Integrity:** revalidates all 12 raw Horizons responses and 300 source rows against frozen SHA-256s; verifies all six original source kernel hashes before evaluation. No network access to Horizons during comparison; no substitutions or regenerated expected values.

## Test and acceptance boundary

The six-source numerical workflow produces [machine-readable evidence](../../validation/wp5-2-horizons-comparison.json) and archives it in GitHub Actions. The project fast checks, synthetic boundary/false-certification unit tests, offline original-response integrity gate, real-kernel comparison and baseline qualification workflow form separate execution gates. See [RM-001/005 implementation prompt](prompts/005-independent-horizons-numerical-comparison.md) and [progress](progress.md) for observed run IDs and merge evidence.

**Bounded WP5.2 deliverable:** independent reference residuals measured and retained, with unresolved model attribution explicitly declared. **Not delivered:** independent physical-model accuracy acceptance, true-ecliptic zodiac error certificate, event/station timing validation, long-period guarantees, Aria Galaxy provider migration, release or deployment.

**Recommended next scientific work:** reconcile the Horizons source/observer model differences for the largest outliers (Pluto/Jupiter geometric positions and Neptune velocity), then repeat the same comparison under explicitly matched source and correction conventions or an approved external uncertainty budget. Only after that can per-body numerical pass/fail limits be approved. WP5.3 motion and events remain separately planned.
