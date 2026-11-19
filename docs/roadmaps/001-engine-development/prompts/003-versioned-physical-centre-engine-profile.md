# RM-001/003 — Versioned physical-centre multi-kernel engine profile (WP4)

| Field | Value |
| --- | --- |
| Date and owner authorisation | 19 November 2026 — user explicitly requested WP4 implementation |
| Roadmap | [RM-001](../README.md), D01 / RM-001-P3 source-and-profile prerequisite |
| Current main baseline | `bfe4a636356366514a213c63be07cffd48b5a337` (source WP1–WP3 PRs #4/#5 merged) |
| Delivery branch | `feature/rm-001-002-wp4-multi-kernel-centres-20261119` |
| Pull request | [#6](https://github.com/DioneGate/ariaephemeris/pull/6), **draft / not merged** |
| Prompt status | **In review**; release/commercial qualification not approved |

## Objective

Expose a **separately named**, offline `planet-centres-v1` calculation profile using six checksum-pinned satellite SPK direct-centre offsets and the existing DE442s barycentre states. Preserve the default v0.1.0 `reference` profile *unchanged* (including original planetary system barycentres) and never substitute an uninstalled physical centre with a barycentre.

## Source and scope

Previously qualified centre/parent pairs: Mars 499/4, Jupiter 599/5, Saturn 699/6, Uranus 799/7, Neptune 899/8, Pluto 999/9. Source identity and real binary segments were qualified in [Jupiter](../p1-jupiter-centre-qualification.md) and [other-five](../p1-five-centres-qualification.md) reports, using two separate JPL evaluator implementations (jplephem and CSPICE) on the **same** source model. These reports are not independent claims about the astronomical model's absolute physical accuracy.

Included: package SHA-256/source-size manifest; strict offline source verification; an opt-in multi-source resolver; centre vectors and velocities (including light-time-retarded evaluations); target-specific metadata; Python request `profile` propagation through positions, chart, batch, raw states, and events; CLI repeatable `--centre-kernel`; profile-aware schemas; unit, per-source real-kernel and full six-in-one engine tests; data/provenance documentation.

Excluded: default provider migration, new house/point/zodiac features, historic UTC expansion, modified/compact kernel redistribution, external HTTP service, Aria Galaxy edits, production release/deployment and statistical validation of absolute physical uncertainty.

## Contract and safety checks

1. No source, wrong digest, wrong size or unsupported SPK segment/coordinate frame → explicit failure; no silent fallback. Partial source installations are allowed for testing but only corresponding physical bodies can be requested.
2. Preserve source `reference` output, target IDs, metadata and original numerical qualification; physically selected source never changes the baseline target list.
3. Direct source records only: for each target NNN, use `NNN wrt N` displacement; always resolve N wrt SSB through the verified **DE442s** base. Never import the satellite kernel's alternate planetary barycentre chain.
4. Frame 1 SPK types 2/3, stable segment precedence, coverage checks for the numerical interval with guard. Preserve km/day velocities and the existing apparent correction pipeline, avoiding Jupiter/Saturn self-deflection.
5. Physical-profile results include exact profile, physical target, source filename and SHA-256, plus **unqualified for commercial release** status. Event timing certificates valid for reference data must never transfer to the new physical profile.
6. No automatic network access on calculations. No 2+ GB source kernels committed or included in a Python wheel.

## Acceptance evidence and remaining qualification

- [x] Source identities/continuous segment availability and same-source evaluator agreement verified across all six bodies in WP1–WP3 (prior recorded evidence).
- [x] Opt-in implementation, CLI/schema updates and tests committed on dedicated branch, PR #6 opened as a draft.
- [ ] Fast CI (Ruff, formatter, mypy, audit, nonkernel tests, package build and smoke) completed with all checks passing on final source revision.
- [ ] Original DE442s regression tests and original numerical qualification pass with reference profile unchanged.
- [ ] Six distinct real satellite SPKs pass physical-profile scalar, geometric/apparent, batch, provenance and safe-error tests.
- [ ] All six installed **simultaneously**, one complete ten-body chart and batch pass full-kernel CI.
- [ ] Owner reviews numerical behaviour, packaging/model limitations and PR #6. Separately authorised merge required.

Even if these technical checks pass, **absolute/source-model uncertainty, full independent geocentric chart fixtures, event timing validation and performance memory footprint are not yet qualified**. No commercial release/Aria Galaxy default change permitted.

## Actual runtime/verification sources

- [Six-source package manifest](../../../../src/ariaephemeris/resources/planet-centres.json)
- [Physical-centre resolver](../../../../src/ariaephemeris/sources/centres.py)
- [Python engine orchestration](../../../../src/ariaephemeris/engine.py)
- [WP4 six-file integration workflow](../../../../.github/workflows/full-centres-integration.yml)
- [WP4 real source matrix](../../../../.github/workflows/planet-centre-qualification.yml) and [Jupiter workflow](../../../../.github/workflows/jupiter-centre-qualification.yml)
- [WP4 numerical conventions](../../../conventions.md) and [standalone usage](../../../../README.md)

The above files remain **in the open draft PR until merged**. Record measured CI evidence and any failing gate in [progress.md](../progress.md); never infer test success from the existence of a workflow.
