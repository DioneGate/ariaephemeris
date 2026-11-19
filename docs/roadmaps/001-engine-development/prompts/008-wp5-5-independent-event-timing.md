# RM-001/008 — WP5.5 Independent JPL Event Timing Qualification

| Field | Value |
| --- | --- |
| Roadmap | [RM-001](../README.md), P3/P6 scientific validation prerequisite |
| Authorised | 2026-11-19 — owner requested **implementation** of WP5.5; no merge, app change or release requested |
| Verified baseline | Main after [WP5.4 PR #12 merged](https://github.com/DioneGate/ariaephemeris/pull/12); original SHA-verified Horizons apparent directions and numerical report |
| Dedicated branch | `feature/rm-001-008-wp5-5-independent-event-timing-20261119` |
| Review | [Draft PR #13](https://github.com/DioneGate/ariaephemeris/pull/13) |
| Status | **In progress** until independent original JPL rays, numerical report and reproducible CI are archived; no merge authority |

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

- [ ] Exactly 22 nominated source windows (6 stations, 6 ingresses, 5 conjunctions, 5 oppositions) independently populated from raw SHA-verified Horizons directions, with 9-node observed sign brackets and complete station 5-point rate stencils.
- [ ] Fail-closed independent sample provenance, TT frame convention, source target/observer identities, no missing records or substituted Aria reference values.
- [ ] 22 original source-derived reference roots calculated; signed Aria minus JPL event-time differences and method/conditioning/provisional exceedances recorded per event and kind.
- [ ] Synthetic rate, wrap, interpolation and event-kind tests; pinned original-source six-kernel real comparison, test/ruff/mypy/package gate and byte-for-byte numerical replay passed with actual run links.
- [ ] Scientific report, roadmap prompt register and progress record written; [PR #13](https://github.com/DioneGate/ariaephemeris/pull/13) prepared for owner review, **not merged**.

## Reproducibility and science boundary

Source acquisition: [`acquire_wp55_events.py`](../../../../tools/datasets/acquire_wp55_events.py), original response verifier [`verify_wp55_events.py`](../../../../tools/datasets/verify_wp55_events.py), pure reference root maths [`wp55_event_math.py`](../../../../tools/datasets/wp55_event_math.py), separate [`compare_wp55_events.py`](../../../../tools/datasets/compare_wp55_events.py), tests [`test_wp55_independent_event_timing.py`](../../../../tests/unit/test_wp55_independent_event_timing.py).

**Independent-source result ≠ independent blind discovery ≠ rigorous interpolation uncertainty ≠ absolute astronomical physical accuracy ≠ commercial event-time release.** Parent P3/P6 remain Planned.
