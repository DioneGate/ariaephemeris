# RM-001/009 — Independent event-discovery completeness benchmark

| Field | Value |
| --- | --- |
| Roadmap | [RM-001](../README.md) |
| Phase | RM-001-P3/P6 qualification evidence |
| Generated/reviewed | 2026-11-19 |
| Baseline | main `b170f7443008f3b8e7b6fbcda656bdefa541e99f` |
| Dependencies | RM-001/008 merged in PR #13; six SHA-pinned physical-centre sources |

## Objective and expected behaviour

Compare complete Aria event catalogues against an independently discovered JPL
catalogue in predeclared TT windows, including searches with no events. Separate
missing, additional, duplicate, ambiguous and timing-discrepant results.

## Verified current state

WP5.5 times 22 Aria-nominated events and independently verifies JPL crossings.
It does not test blind discovery. `src/ariaephemeris/events/__init__.py` uses a
finite extrema-aware scan; its convergence tolerance is not a completeness bound.
PR #13 merged at the baseline above. Existing source rays and reports stay frozen.

## Scope and exclusions

Deliver qualification-only specification, external-source acquisition, offline
integrity verification, independent catalogue discovery, full-list comparison,
tests, reproducible CI and evidence. Keep runtime, source defaults, Aria Galaxy,
publication and deployment unchanged unless a demonstrated scoped runtime defect
requires a separately documented correction within this authorised increment.
RM-001/010 is planned only; its source-model investigation is not implemented here.

## Requirements

- Freeze a machine-readable specification before acquiring source data: complete
  2023–2025 TT window, four fixed historical windows, six source-seam windows;
  physical Mars–Pluto centres; station/ingress and all 15 pairs' conjunctions and
  oppositions. Also compare Mars pairs at 60°, 90° and 120° in the main window.
- Match geocentric, airless apparent, tropical IAU 2006/2000A true ecliptic of date
  at TT. Archive original Horizons quantity-45 rays, exact queries and SHA-256.
  No Aria-derived candidate date, expected count or output enters discovery.
- Use independently fitted local cubic source interpolants; enumerate station
  derivative zeros and longitude/relative-longitude target roots in every panel.
  Check fine, coarser and shifted grids with the same predeclared window.
- Use half-open [start,end) catalogue ownership, source padding for derivatives,
  circular unwrapping, event direction and explicit goal identities. Surface
  grazing/close/ambiguous roots and incomplete/nonfinite/unresolved input.
- One-to-one full-list matching must report every unmatched event on both sides,
  duplicates and ambiguous assignments. Never turn a failed/limited search into
  an empty successful catalogue. Record empty-reference workloads explicitly.
- Use a 60-second comparison association band and 30-second grid-convergence
  diagnostic, as benchmark criteria only, not approved physical accuracy limits.
- Report per-kind/window counts, signed timing differences, bracket/interpolation
  limitations, shared ERFA dependency and differing JPL models. A converged finite
  scan is empirical benchmark evidence, never a universal completeness proof.

## Compatibility and operations

Only development/reference tooling changes. Runtime stays offline and API/schema
contracts remain stable. Source acquisition is explicit, serial and resumable;
ordinary checks replay frozen files without network. Keep kernels uncommitted.
Rollback removes qualification additions without changing calculation results.

## Acceptance criteria

- [ ] Predeclared specification and reference discovery are independent of Aria.
- [ ] Original external-source bytes/semantics and complete sample coverage verify.
- [ ] All declared workloads have complete reference and Aria result lists.
- [ ] Missing/additional/duplicate/ambiguous/unresolved cases are zero or explicitly
  diagnosed and prevent a passing benchmark verdict.
- [ ] Grid convergence and empty-window outcomes are recorded, not inferred.
- [ ] Adversarial analytic tests cover recrossings, tangencies, close roots,
  wrap, endpoints, matching ambiguity, corrupt source and search failures.
- [ ] Fast checks, real-kernel comparison and frozen numerical replay pass.
- [ ] Records show actual merge evidence before delivery is called Done.

## Validation

Run pinned Ruff, mypy, audit, non-kernel pytest, build/package smoke; run the new
offline original-source verifier and six-real-kernel catalogue comparison/replay.
Run available real-kernel integration tests; record the separate legacy long
qualification outcome accurately. Primary mathematical guidance: NAIF Geometry
Finder Required Reading, https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/gf.html;
Horizons conventions: https://ssd.jpl.nasa.gov/horizons/manual.html. Reference
transforms share ERFA standards with Aria and are not fully independent models.

## Delivery record

The owner explicitly authorised documentation updates, implementation, testing
and merge on 19 November 2026. Branch:
`feature/rm-001-009-independent-event-discovery`. See [progress](../progress.md)
for actual evidence. No release or deployment is authorised.
