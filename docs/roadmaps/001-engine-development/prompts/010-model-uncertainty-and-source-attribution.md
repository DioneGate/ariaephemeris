# RM-001/010 — Remaining source attribution and model-aware uncertainty

| Field | Value |
| --- | --- |
| Roadmap | [RM-001](../README.md) |
| Phase | RM-001-P3/P6 qualification evidence |
| Generated/reviewed | 2026-11-19 |
| Baseline | main `02020a9`, PR #14 merged; verify full SHA in progress |
| Dependencies | Frozen WP5.2 vectors, WP5.3 attribution, WP5.6 blind source/catalogues |

## Objective and expected behaviour

Attribute remaining four-planet source differences and distinguish implementation,
reference interpolation, model disagreement and unknown physical uncertainty.
Diagnose the six station-grid convergence failures exposed by 009 without
changing its frozen report or relaxing its 30-second reference criterion.

## Verified current state

PR #14 merged the 009 harness and original source: 28,356 JPL rays, 237 workloads,
142 Aria/reference event matches and 193 empty workloads. No event was missing,
additional, duplicated or ambiguously associated. The full benchmark nevertheless
**failed**: six station workloads do not converge across the coarse reference
grids. The failure is preserved as evidence, not relabelled a pass.
WP5.3 attributed Jupiter/Pluto model differences; four other planets remain open.

## Scope and exclusions

Qualification tools, independently obtained source, tests, uncertainty register,
scientific evidence and documentation only. Preserve runtime, source defaults,
profile and time/frame conventions. Aria Galaxy, civil-time/EOP implementation,
production release and deployment are excluded.

## Requirements

- Reuse WP5.3's exact vector decomposition at the existing 25 TDB dates per body
  for Mars, Saturn, Uranus and Neptune: four source roles each, 400 new original
  JPL states. Keep planetary, Earth, physical-centre and query-context contributions
  distinct, including velocity. Report per-body max/RMS/p95 and per-epoch vectors.
- Verify original raw responses, exact target/origin/frame/time/units and SHA-256;
  reconstruct all 100 frozen WP5.2 discrepancies with unchanged pinned kernels.
  Preserve existing Jupiter/Pluto output byte-for-byte after helper generalisation.
- Predeclare a source-only refinement around all 36 stations discovered in 009.
  Candidate centres come from the JPL-only fine catalogue, never Aria times.
  Acquire independent quantity-45 airless ICRF rays at explicit TT; compare continuous
  cubic-spline stationary roots at 3h/90m/45m and shifted 45m grids. Retain the original
  coarse failures and quantify the refinement with the same 30-second diagnostic.
- Compare refined independent station times with frozen 009 Aria events using the
  existing 60-second association diagnostic. Retain every root and ambiguity.
- Measure derivative step sensitivity for JPL source samples and the complete Aria
  position pipeline. Keep empirical step spreads and first-order conditioning
  proxies separate from mathematical bounds or physical uncertainty.
- Maintain an uncertainty register covering source models, query paths, numerical
  evaluation, frame/correction conventions, interpolation, quantisation and civil
  time/EOP. Unsupported absolute physical position/rate/time bounds are null with
  reasons and closure requirements. Never interpret model disagreement as sigma,
  add independent maxima, or invent a zero uncertainty.
- Numerical source decomposition and station refinement are bounded evidence;
  no automatic commercial acceptance, universal completeness or model upgrade.

## Compatibility and operations

Extend existing development helpers through optional parameters with unchanged
legacy defaults and reports. New datasets/reports have separate identities.
Source acquisition is explicit, serial, immutable and resumable; normal CI is
network-free for reference data and replays pinned evidence. Keep kernels out of
Git. Rollback removes qualification additions without changing engine outputs.

## Acceptance criteria

- [ ] All 400 new source components verify; 100 original residuals close.
- [ ] Legacy Jupiter/Pluto attribution replays unchanged.
- [ ] Every one of 36 JPL-discovered stations has complete fine source and unique
  root lists, converges under the declared diagnostic, and matches its frozen
  Aria event. Any unresolved case remains failed/unknown, never discarded.
- [ ] Original six 009 failures remain preserved and correctly explained.
- [ ] Derivative sensitivity and conditioning retain explicit units and limits.
- [ ] Physical uncertainties remain unknown where no applicable evidence exists.
- [ ] Fast checks and real-kernel replay pass; status reflects actual review/merge.

## Validation

Use pinned Ruff, formatting, mypy, notice audit, unit tests, build/package smoke,
offline source verification and real-kernel numerical replay. Test vector closure,
query identity/corruption, missing source, multiple roots, zero/ill-conditioned
slopes, unknown uncertainty and immutable historical failures. Scientific primary
references: JPL Horizons manual (https://ssd.jpl.nasa.gov/horizons/manual.html),
JPL satellite source inventory (https://ssd.jpl.nasa.gov/sats/ephem/files.html),
and NAIF Geometry Finder Required Reading
(https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/gf.html).
Shared ERFA IAU primitives are disclosed, not independent model certification.

## Delivery record

Owner requested carrying on with 010 on 19 November 2026. Dedicated branch:
`feature/rm-001-010-model-uncertainty`. Implement and test the bounded evidence;
record actual commands, source hashes, scientific limitations and PR in progress.
Keep parent P3/P6 open. No publication or deployment is included.

## Evidence-driven refinement — 19 November 2026

The initial 400-state attribution and 2,340 station-ray capture are frozen in
commit `221ecf1`. Initial independent local cubic panels have derivative jumps
at knots, producing artificial double/missing stationary roots; the failed
report is retained in Git and a separate compact diagnostic. A C2 not-a-knot
cubic spline resolves all 36 captured stations locally with the original
30-second convergence criterion. No runtime event algorithm changes.

Large cancelling Uranus/Neptune terms require 100 additional direct physical
centre-to-parent vectors (25 existing TDB dates per remaining body). These use a
separate predeclared specification and immutable source identity, preserving
the original 400 components. Distinguish true direct-offset disagreement from
reference-chain mixing; never call the large effective-offset term a pure
physical-offset error. Preserve vector closure and explicit velocity units.
