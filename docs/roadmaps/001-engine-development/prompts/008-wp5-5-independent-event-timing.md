# RM-001/008 — WP5.5 Independent JPL Event Timing Qualification

| Field | Value |
| --- | --- |
| Roadmap | [RM-001](../README.md), P3/P6 scientific validation prerequisite |
| Authorised | 2026-11-19 — owner requested **implementation** of WP5.5; no merge, app change or release requested |
| Verified baseline | Main after [WP5.4 PR #12 merged](https://github.com/DioneGate/ariaephemeris/pull/12); original SHA-verified Horizons apparent directions and numerical report |
| Dedicated branch | `feature/rm-001-008-wp5-5-independent-event-timing-20261119` |
| Review | [Draft PR #13](https://github.com/DioneGate/ariaephemeris/pull/13) |
| Status | **In review** — 22/22 source event roots and near-root JPL sign brackets measured, full PR replay pending; no merge authority |

## Objective

Build a separate, reproducible **independent-source event-time comparison**, evaluating Aria Ephemeris's existing opt-in `planet-centres-v1` `find_events` behaviour against independently interpolated NASA/JPL Horizons geocentric apparent tropical event times. Measure signed event timing differences **in seconds of TT**, conditioning and reference interpolation sensitivity, and preserve the source data and scientific limitations.

This is *not* a new production event-search algorithm, universal event-completeness proof, verified observational dynamical uncertainty budget or commercial release approval.

## Scientific definitions and bounded sample

- **Six stations**: one station for each physical planetary centre 499, 599, 699, 799, 899, 999, root of independently derived JPL Horizons `dλ/dTT = 0` for true tropical ecliptic longitude.
- **Six zodiac ingresses**: one 30° tropical longitude boundary per physical centre, equation `wrap(λ_target − 30k°) = 0`.
- **Five conjunctions and five oppositions**: Mars (499) against Jupiter/Saturn/Uranus/Neptune/Pluto (599/699/799/899/999). Equations `wrap(λ_Mars − λ_other) = 0` or `wrap(λ_Mars − λ_other − 180°) = 0`.
- All positions are **geocentric (Earth 399), airless apparent, tropical true ecliptic-of-date IAU 2006/2000A** at explicit **TT Julian Date**; event times are seconds of TT, not civil UTC.
- Six station and ingress *candidate windows* are nominated by Aria's prior WP5.4 stress samples; the 10 pair-event candidate windows are nominated by a bounded 2023–2025 Aria phase scan. **Aria only selects windows, never the expected JPL source longitude, rate, signed event equation or reference event root.** The resulting sample is conditional on Aria's candidates: it cannot prove independent event **discovery or completeness**.
- Nine explicitly scheduled JPL times at `t ± 0.03125, 0.0625, 0.09375, 0.125` TT days surround each nominated candidate. For stations, derive independent signed rate at **each** of the nine times from five independent JPL directions spaced by `±0.0125/0.025` TT days. No reference values derive from Aria's source state or built-in rate.
- The source is official Horizons `EPHEM_TYPE=OBSERVER`, `QUANTITIES=45`, `REF_SYSTEM=ICRF`, `APPARENT=AIRLESS`, `TIME_TYPE=TT`, physical planet centres, geocentric Earth 399; each raw response, complete request URI/parameters, source solution labels and original-byte SHA-256 is archived immutable.
- Independently compute tropical direction using reference `PNM06A`, `OBL06`, `NUT06A` at each TT sample; this is a separate code path but shares **ERFA 2.0.1.5 IAU standard primitives** with Aria. Distinguish independent *source observations* from a fully independent frame implementation.

## Reference root, conditioning and comparisons

Determine one and only one **observed source-root sign-change bracket** in each nine-node JPL grid. Reject missing, duplicated, nonfinite or phase-wrap false roots. Fit a **local four-point cubic** within the identified JPL bracket, bisect that interpolant, and record root TT JD, original source bracket width (about 45 minutes), signed slope of the equation at root, and cubic-minus-linear timing sensitivity. **A cubic root is a numerical approximation; the finite JPL grid, cubic-vs-linear comparison and dense root calculations are not a rigorous absolute error bound.**

Run existing Aria `find_events(EventRequest(profile="planet-centres-v1"))` separately over the ±0.25-day neighbourhood of the nominated candidate, preserving source provenance, `timing_qualified=false`, algorithmic conditioning and event-search budget. Report signed `Aria_event_TT − independent_JPL_interpolated_TT` seconds; missing/multiple Aria events and poor source slopes must be visible, never silently scored as passes.

Provisional **60 seconds** external comparative discrepancy is a research diagnostic only. It is not an approved physical event-timing accuracy claim, interpolation uncertainty certificate, universal accuracy limit, full 1900–2100 coverage or commercial release gate. No auto-widened threshold or hidden missing results.

## Non-functional boundaries

- New `tools/datasets` acquisition, authentication, mathematical and comparison scripts, tests, frozen external fixtures, scientific report and separate CI only.
- No modification to `src/ariaephemeris`, the event API, algorithm defaults, data models, deployed Aria Galaxy, profile default, binary SPKs, package release or entitlement/licensing.
- Acquisition is **manual-only after the initial reviewed dataset freeze**, normal CI is entirely offline except fetching original pinned JPL SPK sources as needed for explicit reproducibility.
- Retain original Horizons source-model differences (DE441 vs Aria DE442s) and quantitative but *not certified* interpolation error.

## Acceptance

- [x] Exactly 22 candidate windows (6 stations, 6 ingresses, 5 conjunctions, 5 oppositions), all 504 original JPL event-grid rays SHA-verified across 14 responses; 9-node source sign brackets and complete five-point station-rate stencils verified.
- [x] Fail-closed source provenance, physical target/Earth 399/airless apparent ICRF TT conventions, missing/duplicate source detection, and independent JPL-only reference values verified, without Aria-substituted expected values.
- [x] 22/22 JPL-only roots and 22/22 corresponding Aria event times compared in [machine report](../../../validation/wp55-independent-event-roots.json), with signed errors, bracket width, cubic–linear sensitivity, conditioning and provisional diagnostic exceedances. Independently sourced 224 further near-root JPL rays confirmed **22/22 sign changes within ±15 seconds**, with **22/22 Aria times also inside those source brackets** in [fine-time report](../../../validation/wp55-jpl-fine-root-brackets.json).
- [ ] Pure synthetic rate, angle wrap, interpolation and event-kind tests passed; [real six-kernel JPL capture #44534617647](https://github.com/DioneGate/ariaephemeris/actions/runs/44534617647) **PASS** and [JPL-only 15-second confirmation #44535411289](https://github.com/DioneGate/ariaephemeris/actions/runs/44535411289) **PASS**. Final **PR-scoped offline integrity, pinned six-kernel byte-for-byte reproduction and project fast CI** must be checked at final code head.
- [x] [Scientific event-timing report](../p1-wp55-independent-event-timing.md), [22-case numerical evidence](../../../validation/wp55-independent-event-roots.json), [fine-source sign-bracket evidence](../../../validation/wp55-jpl-fine-root-brackets.json), source registry and roadmap progress prepared in [draft PR #13](https://github.com/DioneGate/ariaephemeris/pull/13). **No merge or deployment authorised.**

## Reproducibility and science boundary

Source acquisition: [`acquire_wp55_events.py`](../../../../tools/datasets/acquire_wp55_events.py), original response verifier [`verify_wp55_events.py`](../../../../tools/datasets/verify_wp55_events.py), pure reference root maths [`wp55_event_math.py`](../../../../tools/datasets/wp55_event_math.py), separate [`compare_wp55_events.py`](../../../../tools/datasets/compare_wp55_events.py), tests [`test_wp55_independent_event_timing.py`](../../../../tests/unit/test_wp55_independent_event_timing.py).

**Independent-source result ≠ independent blind discovery ≠ rigorous interpolation uncertainty ≠ absolute astronomical physical accuracy ≠ commercial event-time release.** Parent P3/P6 remain Planned.
