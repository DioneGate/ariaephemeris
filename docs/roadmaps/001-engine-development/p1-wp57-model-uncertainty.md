# RM-001/010 — Remaining source models and uncertainty

**Status:** bounded numerical qualification passed; PR review and final replay tracked in [progress](progress.md). Absolute physical uncertainty and commercial release remain open.

## Source and scope

Baseline: main `02020a9415d7e71e6c2e5601bf93d32096c94fe0` (PR #14). Original specification frozen at `df381bdf`; direct-offset supplement frozen at `a2272bc`. New evidence comprises **400 source-component states**, **100 separately queried direct centre-to-parent vectors**, and **2,340 apparent ICRF rays** around all **36 JPL-discovered stations**. All original bytes, exact queries, model labels and SHA-256 values verify offline.

The [machine report](../../validation/wp57-model-uncertainty.json) retains each signed vector, velocity component, source identity, station root, derivative stencil and comparison. Kernels remain unchanged: pinned DE442s plus the six original centre-offset SPKs.

## Remaining four-planet attribution

Values below are maxima over 25 predetermined TDB epochs per body, not physical error bounds. Component maxima occur at different epochs and must not be added.

| Body | Geocentric disagreement (km) | Direct offset disagreement (m) | Reference-chain offset mixing (km) | Direct offset velocity disagreement (mm/s) |
| --- | ---: | ---: | ---: | ---: |
| Mars | 3.8310216 | <0.001 | 1.600974e-07 | 3.98666e-09 |
| Neptune | 0.3254954 | 325.495 | 2222.6184 | 6.37874 |
| Saturn | 1.1280833 | <0.001 | 9.443319e-07 | 5.43541e-09 |
| Uranus | 1.7513323e-05 | <0.001 | 4861.531 | 3.58127e-09 |

Mars and Saturn direct offsets agree at the sampled numerical level; their larger geocentric differences reside mainly in the parent/Earth model comparison. Uranus has only about 18 mm of maximum geocentric disagreement despite a roughly 4,862 km parent-query difference: the independently measured query-chain term cancels that difference. It must not be misreported as a physical centre-offset defect.

For Neptune, the approximately **325.5 m** direct-offset maximum and **6.38 mm/s** velocity maximum account for the remaining geocentric discrepancy. Aria retains `nep105.bsp`; the direct Horizons reference identifies `nep098_merged`. This measures differing source solutions, not which solution is observational truth. No source replacement is made.

Every sampled vector satisfies:

`total difference = parent geocentric difference + direct offset difference − reference-chain mixing`.

Position closure is checked within 0.0002 km; velocity closure within 1e-10 km/s. These are numerical identity tolerances, not physical accuracy claims. Legacy Jupiter/Pluto attribution is separately reproduced byte-for-byte.

## Station reference diagnosis and refinement

The original 009 report remains **failed** on six coarse station-reference workloads, despite all 142 event matches. The first 010 capture additionally exposed false double/missing roots: independently fitted local cubic panels are not continuously differentiable at their shared sample knots. Station roots are derivative zeros, so that discontinuity matters. The [initial diagnostic](../../validation/wp57-initial-local-cubic-diagnostic.json) and full initial report in commit `221ecf1` preserve those failures.

The new reference uses a separately identified **C2 not-a-knot cubic spline** of original JPL-only tropical longitudes. Derivatives are continuous across knots. Every real root in the predeclared neighbourhood is retained; multiple, missing, grazing or non-converged roots fail the gate.

All **36/36** stations resolve uniquely and match the frozen full-window Aria returns. Tested source grids are 3 hours, 90 minutes, 45 minutes and shifted 45 minutes; the maximum observed grid difference is **5.2527 seconds**, below the unchanged **30-second** reference diagnostic. Maximum Aria-versus-refined-JPL timing difference is **3.5712 seconds** (Neptune), below the existing **60-second** association diagnostic.

These are finite interpolant and model comparisons. They do not establish a mathematical interpolation bound, universal search completeness or absolute physical timing accuracy. The original 009 report is not silently rewritten as passed.

## Uncertainty register

| Category | Evidence/status | Absolute physical bound |
| --- | --- | --- |
| Implementation agreement | sampled same-source agreement: Pinned SPKs, evaluator and full regression checks; not physical truth | Unknown |
| Planetary/observer/centre models | measured model disagreement: Component attribution includes differing correlated trajectories; no sigma or model ranking | Unknown |
| Horizons query paths | measured context gaps: Direct centre, parent and SSB paths may select different chains; direct centre-to-parent queries isolate offset mixing | Unknown |
| Reference interpolation and rates | empirical refinement: Finite cubic/derivative step agreement is not a rigorous continuous bound | Unknown |
| Frames and apparent corrections | shared standard dependency: Separate code paths share ERFA IAU 2006/2000A; source correction conventions remain explicit | Unknown |
| Source decimal precision | format precision only: Printed RA/Dec digits do not establish physical accuracy; differentiation can amplify quantisation | Unknown |
| Civil time and Earth orientation | outside TT scope: Geocentric TT station evidence does not qualify UTC, UT1, EOP or birth-time uncertainty | Unknown |
| Commercial accuracy decision | open: D07 comparison criteria are distinct from absolute physical uncertainty | Unknown |

Per-station Aria rate sensitivity is measured with complete-pipeline five-point stencils at 0.0005, 0.001, 0.002 and 0.004 TT days; independent JPL rates use separately observed 0.03125, 0.0625 and 0.125 TT-day stencils. The report retains signed rates, spreads and acceleration.

`|delta f / f′| × 86400` is a first-order sensitivity proxy only. For stations, f is degrees/TT day and f′ is degrees/TT day². A zero slope yields unknown, never zero uncertainty. No unvalidated model disagreement is converted to sigma, summed as a budget or used as a universal time bound.

## Defensible interpretation

The evidence supports reporting reproducible agreement with explicitly named, convention-matched references in the sampled windows. It does not support an absolute “accurate to X” promise over 1900–2100, a new approved product threshold or a commercial release. Decision D07, applicable physical uncertainty evidence, civil-time/EOP qualification, deployment and remaining launch capabilities stay open.

Primary references: [Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html), [JPL satellite source inventory](https://ssd.jpl.nasa.gov/sats/ephem/files.html), [NAIF Geometry Finder](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/gf.html), [SciPy CubicSpline](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.CubicSpline.html). The latter documents the continuously differentiable reference interpolator, not astronomical physical uncertainty.

## Numerical replay precision

A source-only replay failed exact equality for a derived station record on one
CI runner, while local reconstruction and a subsequent independent run matched.
Source identity and the 36-station regression remained valid; this indicates
numerical portability needs an explicit precision contract. Replay therefore
keeps exact schemas, source/vector identities, counts, flags, null physical
bounds and legacy Jupiter/Pluto bytes. Derived station roots use 1e-7 TT day
(8.64 ms, the source query timestamp precision), timing aggregates 10 ms, rates
1e-10 deg/TT day and accelerations 1e-9 deg/TT day². Rate spreads use twice
the rate tolerance. Illustrative conditioning proxies must exactly reconstruct from their own
rate/acceleration inputs; those primitives have the explicit tolerances above. These are numerical
replay tolerances, not physical uncertainty bounds; the 30/60-second scientific
criteria, unique root counts and missing/duplicate/ambiguity gates remain exact.

The acceleration replay allowance accounts for second differentiation of F64
angular samples on the 0.03125-day grid (roundoff is amplified by inverse step
squared). It is a numerical portability allowance, not an ephemeris model bound.
