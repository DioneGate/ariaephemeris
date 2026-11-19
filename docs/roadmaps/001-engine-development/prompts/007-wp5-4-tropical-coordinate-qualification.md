# RM-001/007 — WP5.4 Astrological Coordinate Qualification

| Field | Value |
| --- | --- |
| Roadmap | [RM-001](../README.md), P3 scientific capability qualification and P6 release evidence |
| Authorisation | 19 November 2026 — owner requested **implementation of WP5.4**, not merge or release |
| Main baseline | WP5.1 external references, WP5.2 geometric/apparent comparison, WP5.3 JPL source reconciliation PR #11 merged |
| Branch | `feature/rm-001-007-wp5-4-astrological-coordinate-qualification-20261119` |
| Review | [Draft PR #12](https://github.com/DioneGate/ariaephemeris/pull/12) |
| Status | **In progress** until real-source acquisition and CI evidence; **In review** once reviewable; **Done only on authorised merge** |

## Objective

Independently qualify the **astrological coordinate interface** of Aria Ephemeris's opt-in `planet-centres-v1` profile: geocentric apparent **tropical true-ecliptic longitude, ecliptic latitude and signed longitude rate in degrees per TT day**, including sign boundaries and retrograde transitions. Reference data comes from NASA/JPL Horizons rather than Aria-generated expected values. Coverage and model/frame independence must be stated honestly.

WP5.4 is separate from WP5.5 event root/ingress/station **timing accuracy** and WP5.6 release qualification.

## Verified current state

- WP5.1 archived 150 original independent Horizons `OBSERVER QUANTITIES='45'` geocentric physical-centre apparent ICRF RA/Dec values (25 TT instants each × six planets), with SHA-256 raw-text evidence. Their conventions deliberately avoid Horizons' differently defined ecliptic-of-date output.
- WP5.2 measured 150 apparent inertial sky-direction residuals across six planets: maximum **0.004789 arcseconds** (Jupiter) at the frozen sample dates, with source ephemerides not identical.
- WP5.3 [PR #11](https://github.com/DioneGate/ariaephemeris/pull/11) source model attribution established Jupiter/Pluto 14.82/40.91 km geocentric differences are dominated by JPL DE441-vs-DE442s planetary reference trajectories rather than direct physical centre offsets. It did **not** establish a continuous physical uncertainty bound.
- Aria's `positions` and `positions_batch` already implement IAU 2006/2000A true ecliptic/equinox of date, geocentric apparent corrections and a **five-point 0.001 TT day** signed longitudinal derivative of the entire corrected pipeline. `BodyPosition.right_ascension_deg` is true-equator-of-date and must **never** be compared directly with Horizons ICRF quantity 45.

## Bounded scope and methods

1. Preserve WP5.1 original `OBSERVER QUANTITIES=45` ICRF airless apparent RA/Dec samples at TT JD. Independently acquire additional Horizons rays at signed ±0.0125 and ±0.025 TT days for an **independent five-point longitude-rate estimator**. Keep every original response, exact URL and parameters, source header and SHA-256, no numerical data inferred from Aria.
2. Use the **existing 25 dates per planet**, including 1900/2100, J2000, modern dates and physical SPK boundaries, and **six new 2023–2025 stress dates per planet**: an Aria-*nominated* station and zodiac sign ingress, each at estimated root ±0.25 TT days. Aria is used only to select the candidate test dates; all expected coordinates and rate signs come from Horizons. **This does not independently determine astronomical event root times.**
3. Derive true tropical ecliptic longitude/latitude directly from each independent Horizons inertial direction by applying the independently coded 3D transformation to IAU 2006/2000A true equator/ecliptic-of-date: `PNM06A`, mean obliquity `OBL06` and nutation `NUT06A` at TT. The transform is **not imported from Aria**, but both sides intentionally use PyERFA 2.0.1.5, so this is **not a fully independent IAU precession-nutation implementation**. Include an independent closed-form rotation round-trip and frame-motion unit tests.
4. Compute reference rate from **five separately acquired Horizons directions** at TT `t-0.025, t-0.0125, t, t+0.0125, t+0.025` days, transforming at each date into the **moving true ecliptic**. Apply a cyclic-safe five-point derivative, compare signed deg/TT day with Aria's different-spacing rate output.
5. Report **longitude, latitude** residuals in arcseconds and **rate** residual in degrees per TT day: per-planet sampled max/RMS/p95; exact values and signed residual for every fixture. Report motion sign disagreements **outside** a declared near-station ambiguity band, sign-index disagreements **away from** cusp ambiguity and data for ±0.25 days around events.
6. Fail closed on missing/wrong target centre (499/599/699/799/899/999), Earth origin 399, bad TT epochs/IAU coordinate frame, corrupt external source or incomplete 25+6 samples/body. Re-run the original WP5.1 SHA validator. Regular tests must be completely offline; only explicitly authorised acquisition uses live Horizons. No fallback to generated Aria expected values.

## Quantitative acceptance and limitations

The **provisional diagnostic** `0.05 arcseconds` absolute longitude/latitude difference and `0.0001 deg/TT day` absolute longitude-rate difference are **not approved physical or commercial accuracy limits**. Record actual exceedances rather than automatically changing tolerances or manufacturing a pass. Near station, classification is ambiguous when either `|rate| <= 0.0002 deg/day`; near ingresses, classification is ambiguous inside 0.05 arcseconds of a sign boundary. Never certify event timing or exact zodiac sign at a genuinely unresolved boundary without an independently proven tolerance.

- Horizons' physical-centre rays can use different planetary/observer reference ephemerides to Aria DE442s plus original SPK centre offsets. Residuals are **model-to-model** differences.
- The apparent correction and IAU frame implementation are **not fully mathematically independent**; shared ERFA is a disclosed limitation.
- Critical times are nominated by Aria for **stress coverage** only, not independently calculated event root benchmarks.
- A finite 186-sample profile cannot prove all times in 1900–2100, the full lunar/inner planet launch chart, or absolute observational uncertainty.
- No `src/ariaephemeris`, public API, chart provider, original SPK or Aria Galaxy changes, no release, merge or deployment implied.

## Acceptance checklist

- [ ] Immutable JPL original-source acquisition includes exactly **780 new external reference rays**, reuses 150 original WP5.1 rays, and reconstructs **930 independently sourced time-stencil points**, 186 chart cases.
- [ ] Six physical centres each have **25 historical/segment** and **3 station + 3 ingress** chart cases; independent rate direction and moving-frame computations validated.
- [ ] Complete, truthful per-planet measured residual statistics: longitude/latitude arcsec and signed rate deg/TT day; motion/sign disagreements reported, including ambiguous conditions.
- [ ] Original-source hashes, no stale/missing measurements, 100% defined coverage, semantic source conventions and no commercial accuracy overclaims.
- [ ] Offline mathematical/unit tests, fast CI, pinned six-source real comparison, immutable numerical replay and existing qualification regressions verified, with actual CI evidence.
- [ ] Brief measured report and progress/register produced; PR #12 prepared for review, **not merged** without separate owner instruction.

## Evidence and expected reproducibility

- [External acquisition](../../../../tools/datasets/acquire_wp54_tropical.py)
- [Raw-source fixture SHA verifier](../../../../tools/datasets/verify_wp54_tropical.py)
- [Separate transformation and signed-rate comparator](../../../../tools/datasets/compare_wp54_tropical.py)
- [Independent projection and critical-case unit tests](../../../../tests/unit/test_wp54_tropical_qualification.py)
- [Real-kernel acquisition/qualification workflow](../../../../.github/workflows/wp54-acquisition-and-numerical-qualification.yml)
- [Full numerical report](../../../validation/wp54-tropical-coordinate-comparison.json) when captured
- [WP5.4 scientific findings](../p1-wp54-tropical-coordinate-qualification.md) when measured

The next WP5.5 task is independent **event-root timing**, not a side effect of using an Aria-selected station candidate in WP5.4. Sign/house astrology policy and application integration remain separately controlled by the roadmap.
