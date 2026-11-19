# RM-001/008 — WP5.5 Independent Event Timing Qualification

**Date:** 19 November 2026 · **Delivery:** [PR #13](https://github.com/DioneGate/ariaephemeris/pull/13), merged at `b170f744` · **Profile:** opt-in `planet-centres-v1` with SHA-pinned DE442s and six original satellite SPKs · **Time:** geocentric apparent **TT**, not civil UTC · **Scientific status:** **22 independent-source event-time comparisons measured and independently fine-bracketed; commercial release accuracy not certified**.

Primary evidence: [22 independent Horizons-vs-Aria event comparisons](../../validation/wp55-independent-event-roots.json), [504 original JPL event-grid rays](../../../data/fixtures/horizons/wp55-events/wp55-horizons-event-roots-v1.json), [224 additional fine-time JPL rays](../../../data/fixtures/horizons/wp55-root-refinement/wp55-jpl-fine-root-brackets-v1.json) and [22 fine-bracket verification records](../../validation/wp55-jpl-fine-root-brackets.json). Exact original raw Horizons responses are SHA-256 verified and archived with query parameters, source-model names and traceable request URLs.

## Executive result

**All 22 selected events** were found by Aria's unchanged `find_events` physical-centre search and independently located using NASA/JPL Horizons airless apparent ICRF directions. The results cover six planetary retrograde stations, six tropical 30° sign ingresses, five Mars/outer-planet conjunctions and five Mars/outer-planet oppositions.

| Event kind | Number of samples | Maximum absolute Aria−JPL reference timing difference | RMS | p95 | Missing Aria events |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stations | 6 | **4.6136 seconds** (Neptune) | 2.3103 s | 4.0422 s | 0 |
| Tropical zodiac ingresses | 6 | **0.04357 seconds** (Saturn) | 0.02445 s | 0.04025 s | 0 |
| Conjunctions | 5 | **0.03955 seconds** (Mars–Saturn) | 0.02425 s | 0.03879 s | 0 |
| Oppositions | 5 | **0.03919 seconds** (Mars–Neptune) | 0.02480 s | 0.03907 s | 0 |
| **Total** | **22** | **4.6136 seconds** | — | — | **0** |

**No sampled event exceeded the provisional 60-second discrepancy diagnostic.** This is not an approved product time-accuracy threshold, and finite model-to-model agreement is not a continuous or absolute physical uncertainty guarantee.

### Additional independently observed root check

The original [504-source-ray dataset](../../../data/fixtures/horizons/wp55-events/wp55-horizons-event-roots-v1.json) sampled each event equation at nine TT epochs spaced **0.03125 days (45 minutes)** over ±0.125 day. A separately implemented **four-point local cubic**, bisected inside the directly observed JPL sign-change bracket, produced an independent reference root. Its original observed bracket was **45 minutes wide**; the difference between a local linear and cubic interpolation was also recorded, but this agreement is **not a validated interpolation-error bound**.

We therefore acquired a **new, independent JPL source check at TT t−30, t−15, t+15, t+30 seconds** around **the JPL-only interpolated root**, not around an Aria result. Stations required five additional JPL apparent RA/Dec observations at each fine date to evaluate their signed dλ/dTT independently.

- **22/22** source-defined event functions changed sign between t−15 and t+15 seconds: an **independently observed 30-second crossing interval** for each selected event.
- **22/22** also changed sign between t−30 and t+30 seconds.
- **22/22** Aria event times lie within the separately observed 30-second JPL source crossing intervals.
- These checks add **224 original JPL rays in seven original response files**, with independent per-response byte SHA-256 and complete source chronology.
- The source sign crossings establish existence of at least one zero in each bracket **assuming local continuity**. They do **not mathematically prove a unique root**, rule out multiple roots between sparse observations, establish absolute observational accuracy, or qualify event discovery/completeness over an arbitrary interval.

The direct 30-second source sign brackets are a substantially stronger control than comparing only two interpolated timestamps; nevertheless, **neither sub-second interpolation nor these brackets should be advertised as guaranteed sub-second astronomical timing accuracy**.

## Reference definitions and independence

All 22 source equations are constructed **only from independently obtained JPL Horizons `EPHEM_TYPE=OBSERVER`, `QUANTITIES=45` apparent ICRF RA/Dec**, using `TIME_TYPE=TT`, geocentric observer **399**, physical centres **499/599/699/799/899/999**, and `APPARENT=AIRLESS`. Every direction is transformed to tropical true ecliptic/equinox of date with IAU 2006/2000A `PNM06A`, `OBL06` and `NUT06A` at the *corresponding exact TT time*.

| Event | Independently evaluated root equation |
| --- | --- |
| Planetary station | `dλ_planet/dTT = 0`, signed **degrees per TT day**; five-point JPL-only derivative at ±0.0125 and ±0.025 TT day |
| Zodiac sign ingress | `wrap(λ_planet−30° × k) = 0` |
| Conjunction | `wrap(λ_Mars−λ_other) = 0` |
| Opposition | `wrap(λ_Mars−λ_other−180°) = 0` |

The numerical reference equation is **not** calculated from Aria's position/rate API. Aria's existing `find_events` searches separately for its own root within the ±0.25-day event neighbourhood. The comparison retains each returned Aria event, source provenance, TT time, conditioning and the signed root difference against the independently interpolated source.

**Selection-bias limitation:** The six station/ingress candidate dates come from prior WP5.4 Aria-nominated 2023–2025 stress cases; ten Mars-versus-other planet pair-event windows were selected by an Aria phase sign-change scan over the same period. **The independent JPL data selects the measured source crossing inside those windows; Aria selected which windows to measure.** This is a *conditional timing comparison*, not an independent global event search, a proof of no missed events outside a window, or a test of all possible aspects/planet pairs.

**Shared standards limitation:** The source directions come from an independent JPL ephemeris, but the separate coordinate transforms share **ERFA 2.0.1.5 IAU 2006/2000A primitives** with Aria; they are not independent precession/nutation implementations. The original reference often identifies **DE441**, while Aria composes a verified **DE442s** planetary base and separately pinned original satellite offsets. The model differences and observational covariance are not proven zero.

## Conditioning, engineering thresholds and recommended interpretation

Near stationary longitude, the derivative `dλ/dTT` becomes zero and the event-time uncertainty amplification is proportional to `1/|d²λ/dTT²|`. Neptune has the largest observed sampled station time difference, **4.61 s**, which is consistent with stations being more sensitive than longitude crossing events. The machine report includes the original rate/angle equation slope, source bracket width and sensitivity proxy per event.

**Important:** The earlier provisional coordinate/rate diagnostic **0.05 arcseconds / 0.0001 degrees/day** must **not** be treated as a universal event timing error budget. At slow Neptune/Pluto stations, a hypothetical signed-rate difference of 0.0001 deg/day, divided by the observed small local acceleration, can correspond to hours of estimated event-time sensitivity. This is a *conditioning illustration*, not the measured or certified timing error.

For a **future, explicitly approved product-level agreement test**, the observed sample supports investigating separate candidate comparative bands: **10 seconds** for well-conditioned stations and **1 second** for well-conditioned ingresses/conjunctions/oppositions, alongside the existing 60-second broad diagnostic. Those are **not approved**, are based on 22 deliberately nominated samples rather than random/complete coverage, and are **not assertions of truth-model accuracy or numerical uncertainty guarantees**. Exact condition and model conventions must appear in any product SLA.

## Test coverage and delivery boundary

The new qualification is separate, reproducible, and **does not alter Aria's runtime event algorithms**:

- [Pure reference-root code](../../../tools/datasets/wp55_event_math.py) rejects wrapped-angle jumps, duplicate/ambiguous JPL zero brackets, incomplete/nonfinite grids and roots outside direct source brackets.
- [Original JPL event acquisition](../../../tools/datasets/acquire_wp55_events.py) and [SHA semantic verifier](../../../tools/datasets/verify_wp55_events.py) archive/validate all 504 source samples and 22 event identity/time-grid contracts.
- [Independent JPL root comparison](../../../tools/datasets/compare_wp55_events.py) computes complete per-event signed TT timing errors, return/missing-event metadata, reference interpolation sensitivity, model uncertainty flags and per-kind max/RMS/p95.
- [Additional source-only fine-bracket acquisition](../../../tools/datasets/acquire_wp55_root_brackets.py) and [offline 30-second bracket verifier](../../../tools/datasets/verify_wp55_root_brackets.py) retain 224 further original source positions and all 22 near-root validations.
- [Synthetic numerical/event unit tests](../../../tests/unit/test_wp55_independent_event_timing.py) check station root, 0/360 and ±180 cyclicity, moving true-ecliptic directions, reference rate, pure event interpolation, false root detection and test-window independence.

The [initial real-source workflow #44534617647](https://github.com/DioneGate/ariaephemeris/actions/runs/44534617647) **passed**, including real checksum-pinned DE442s + six physical-centre SPK downloads, all 504 original JPL observations, 22 numerical root comparisons and source integrity, with generated evidence committed. The [source-only near-root workflow #44535411289](https://github.com/DioneGate/ariaephemeris/actions/runs/44535411289) **passed** 224 fine original JPL rays, raw SHA verification and all 22 observed sign brackets. [Final review validation #44536016732](https://github.com/DioneGate/ariaephemeris/actions/runs/44536016732) **PASSED** both independent original-Horizons source-integrity checks and the **byte-for-byte six-real-SPK replay** of the complete 22-root event report and JPL fine 15-second bracket report, without reacquiring any Horizons data. [Fast CI #44536016808](https://github.com/DioneGate/ariaephemeris/actions/runs/44536016808) **PASSED** Ruff, mypy, original source audit, non-kernel pytest, build/package smoke; [original WP5.1 reference integrity #44536016553](https://github.com/DioneGate/ariaephemeris/actions/runs/44536016553) **PASSED**. The project's separate longer historical DE442s qualification remains a distinct regression and is not counted as independent physical event timing acceptance.

**Still open:** independent event-discovery/completeness benchmarks, certified model-aware absolute time uncertainty, all 1900–2100 dates, additional planet pairs and event angles, grazing/double-root conditions, perturbations at satellite-kernel boundaries, Sun/Moon/inner planets, civil UTC/EOP and any commercial production acceptance. Parent RM-001 P3/P6 remains Planned.

**Outcome:** reproducible **sampled JPL event-timing agreement plus independently observed 30-second crossing intervals for all 22 events**. **No source model/provider default change, no Aria Galaxy change, no package publication, no deployment** was authorised by the original implementation request. Subsequent owner authority completed [PR #13](https://github.com/DioneGate/ariaephemeris/pull/13), merged at `b170f744`; bounded RM-001/008 is **Done**.
