# RM-001/005 — WP5.2 External geometric and apparent numerical comparison

| Field | Value |
| --- | --- |
| Roadmap | [RM-001 — Engine Development](../README.md), P3/P6 qualification evidence |
| Authorisation | 19 November 2026 — owner requested WP5.2 implementation, testing, merge and brief results |
| Main baseline | After WP5.1 [PR #7](https://github.com/DioneGate/ariaephemeris/pull/7) and roadmap [PR #8](https://github.com/DioneGate/ariaephemeris/pull/8) merged |
| Implementation branch | `feature/rm-001-005-horizons-numerical-comparison-20261119` |
| Review PR | [#9](https://github.com/DioneGate/ariaephemeris/pull/9) |
| Prompt status | **Done — bounded comparison implemented, verified and merged**; independent physical-model accuracy remains unqualified |

## Objective

Measure and publish the actual geometric vector and geocentric apparent-direction discrepancies between **Aria's `planet-centres-v1` profile** and the **300 immutable NASA/JPL Horizons references acquired in WP5.1**. The output is an independent measurement report with per-body extrema, RMS and p95 and complete per-fixture evidence, **not** a false claim that two distinct JPL dynamical source models are interchangeable.

The first WP5.2 increment is comparison and diagnosis. Source-model reconciliation, independent true-ecliptic chart fixtures, longitude rates, stations and event acceptance remain separate technical gates.

## Verified baseline, conventions and source differences

- [Frozen WP5.1 dataset](../../../../data/fixtures/horizons/horizons-reference-v1.json): six physical planet centres (499/599/699/799/899/999), 25 epochs each, two reference modes, **12 verbatim SHA-256-validated JPL responses**.
- **Geometric**: Horizons VECTORS, Earth geocentre (399), ICRF, **TDB** JDs, position km and velocity km/s. Compare Aria **physical centre minus Earth**, with both raw states independently evaluated at the same TDB epoch and velocity converted from km/day to km/s.
- **Apparent**: Horizons OBSERVER quantity 45, geocentre (399), **inertial apparent RA/Dec**, ICRF, **TT** JD, airless. Request Aria `PositionRequest(profile="planet-centres-v1", origin="geocentric", frame="icrs", position_mode="apparent")` using the same TT epoch; compare `BodyPosition.longitude_deg/latitude_deg` as ICRF RA/Dec. **Never compare `BodyPosition.right_ascension_deg` directly:** that field is true-of-date.
- Angular discrepancies use stable 3D unit-vector great-circle separation, not naive unwrapped RA subtraction; retain wrapped RA difference and Dec difference for diagnosis.
- Source models are **not fully matched**: Horizons reports DE441 in various reference headers, and Jupiter `jup365_merged`, Saturn `sat441l`, Uranus `ura184_merged`, Neptune `nep098_merged`; Aria uses DE442s and `jup349`, `sat456`, `ura184_part-3`, `nep105` offsets. Mars and Pluto may share a target-family label but no identical full two-body source model has been demonstrated.
- The same-source CSPICE WP3 tests already verified engine evaluation of its *own* JPL SPKs. Horizons differences must not automatically be assigned to either system as an implementation error.

## Included scope

1. Implement `tools/datasets/compare_horizons_fixtures.py` with explicit source/time/frame/target semantics, per-fixture 3D/vector residuals and apparent celestial angular residuals. No network access or live reference mutation in comparator.
2. Load **original DE442s and all six supplementary source kernels**, verify SHA-256 and sizes, and evaluate all 300 cases. Fail closed on missing/malformed source, target, metadata, non-finite result, wrong source time or incomplete sample.
3. Preserve full numeric evidence and a per-planet summary: geometric position km, geometric velocity m/s, apparent angular separation arcsec (maximum, RMS, p95), provenance and count above **provisional** 1 arcsecond comparison level. The level is **diagnostic, not independently approved tolerance**, because the models/corrections are not identical.
4. Frozen machine report in `docs/validation/wp5-2-horizons-comparison.json`, generated from real SPKs by reproducible CI, never invented reference numbers. It must identify each source and record the physical-profile's *not qualified* status.
5. Hermetic tests for angular wrap/poles, velocity units, time-scale separation, wrong target, non-finite data, completeness and prohibition of a false numerical acceptance claim; project fast CI and original DE442s qualification unaffected.

## Exclusions and acceptance boundary

- No numerical or default change to `src/ariaephemeris`, no source kernel/fixture refresh, new chart provider, Aria Galaxy code, release or deployment.
- WP5.2's report may show agreement better or worse than a proposed limit, but **a differing Horizons source model cannot establish a pass or fail against Aria's physical-model accuracy budget by itself**. Missing comparability remains **unreconciled** pending separate matched-source diagnosis or external uncertainty review.
- No longitude rate or event/station timing certification; no absolute time-range error bound from 25 sampled epochs.
- The implementation can be **Done** as a bounded comparison pipeline after passing checks and verified merge even when *scientific acceptance* remains unqualified. The parent P3/P6 phases are not Done.
- A passing CI result means valid computation and complete evidence, **not** a commercial numerical accuracy pass.

## Acceptance checklist

- [x] 300 frozen original-source samples verified and evaluated on six SHA-256-pinned physical-centre SPKs; [complete evidence](../../../validation/wp5-2-horizons-comparison.json).
- [x] Per-planet geometric positions/velocities and apparent angular residuals recorded with RMS/p95/max and source-model provenance.
- [x] No source-model discrepancy auto-passed; physical/commercial accuracy explicitly **not qualified**.
- [x] Frozen reference integrity and real six-kernel comparison produced the complete 300-row report; [fast CI #44478988481](https://github.com/DioneGate/ariaephemeris/actions/runs/44478988481) passed Ruff, mypy, non-kernel tests, build/smoke, and [real-kernel pytest #44478988386](https://github.com/DioneGate/ariaephemeris/actions/runs/44478988386) passed. The same job's slower historic qualification remained in progress at merge; it is not claimed complete.
- [x] [Measured results](../p1-external-horizons-comparison.md) include all six planets, largest geometric differences and explicit unresolved source-model uncertainty.
- [x] User-authorised [PR #9 merged](https://github.com/DioneGate/ariaephemeris/pull/9) into main at [`6216f15`](https://github.com/DioneGate/ariaephemeris/commit/6216f15c9bac88bcfa5bf4eeadb444f7730b0ac1); verified main includes the same 300-row evidence blob.

## Implementation evidence and next step

- [Comparator](../../../../tools/datasets/compare_horizons_fixtures.py)
- [Synthetic numerical checks](../../../../tests/unit/test_horizons_numerical_comparison.py)
- [Real six-kernel CI](../../../../.github/workflows/horizons-numerical-comparison.yml)
- [Frozen comparison report](../../../validation/wp5-2-horizons-comparison.json), after CI acquisition
- [WP5.2 findings](../p1-external-horizons-comparison.md), after measured results

**Delivery complete:** [PR #9](https://github.com/DioneGate/ariaephemeris/pull/9) merged at `6216f15`. The bounded comparison is Done; the scientific acceptance gate remains open because reference models differ. Further scientific work must isolate source/correction differences before accepting a threshold for any planet. This is the next bounded validation step, not approval to release.
