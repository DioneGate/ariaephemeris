# RM-001/002 — Physical planet-centre data feasibility and source qualification

| Field | Value |
| --- | --- |
| Roadmap | [RM-001 — Engine development and commercial readiness](../README.md) |
| Phase | RM-001-P1 (D01 source feasibility); prerequisite for selected RM-001-P3 calculations |
| Generated / started | 2026-11-18 |
| Baseline | Aria Ephemeris main `df96380ee851e3aeac1962ec6010807342f3b7da` (PR #3 merged; engine still 0.1.0); Aria Galaxy unchanged |
| Product direction | Physical planet centres for Mars–Pluto, retain original barycentre mode; selected source/kernels and numeric standards require evidence and approval |
| Working branch | `feature/rm-001-002-centre-source-feasibility-20261118` |
| Prompt status | **In review** — all six source integrity, binary coverage and same-source CSPICE evaluator gates verified; compact packaging and commercial release gates still open; PR #5 draft/unmerged |

Follow [AGENTS.md](../../../../AGENTS.md) and the [source feasibility evidence](../p1-centre-source-feasibility.md). RM-001/001's separate [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3) has merged into main at `df96380`; this task does not silently accept the outstanding D02–D14 decisions.

## Objective and expected behaviour

Demonstrate that centre-offset SPK segments 499/4, 599/5, 699/6, 799/7, 899/8, and 999/9 are suitable companions to the existing Aria DE442s base. Make selection, identity, coverage and sample calculation **auditable and reproducible**, without changing the current operational barycentre contract or conflating physical centres and system barycentres.

## Verified current state

- `src/ariaephemeris/models.py`: 4–9 currently represent Mars–Pluto system barycentres.
- `src/ariaephemeris/sources/__init__.py`: `Kernel` handles **single-SPK** target/centre resolution, JPL types 2/3, reference frame 1, last matching segment precedence, and km / km/day states.
- `src/ariaephemeris/datasets/__init__.py`: a single SHA-256-pinned DE442s manifest; no supplementary manifest/resolver.
- `src/ariaephemeris/positions/__init__.py`: existing correct mode-aware position and light-time pipeline; current actual body targets are declared in `docs/conventions.md`.
- JPL/NAIF published catalogues, direct centre/parent relationships and nominal `BRIEF` intervals for six candidate files are recorded in [the evidence report](../p1-centre-source-feasibility.md). Published text alone is not a binary segment validation.
- Local shell cannot resolve JPL domains, but [GitHub Actions](https://github.com/DioneGate/ariaephemeris/actions/runs/44402922404) acquired and checksum-verified JUP349, ran a real-SPK audit and nine-point independent CSPICE evaluator comparison successfully. See [observed evidence](../p1-jupiter-centre-qualification.md). The other five planet-centre source/evaluator checks also passed on [pinned WP3 GitHub Actions #44410508647](https://github.com/DioneGate/ariaephemeris/actions/runs/44410508647); [WP3 evidence](../p1-five-centres-qualification.md).

## Scope and exclusions

**This work package includes:** discovering and comparing candidate JPL satellite kernels; documenting physical IDs, exact parent IDs, advertised ranges and public checksum values; implementing a **read-only offline source audit** and unit tests; documenting a Jupiter sample procedure; recording binary qualification gaps and reproducible next steps.

**It explicitly excludes:** changing engine `BODY_IDS` or defaults; new provider profiles; multi-kernel production resolver; compact/redistributed kernel pack generation; P2 historical civil time; additional astrology features; application code, service, release/deployment, repository merge or acceptance of all P1 phase gates.

## Requirements

1. Precisely report six target-centre pairs. The astronomical state must be obtained as `DE442s barycentre + direct satellite centre-relative-to-barycentre offset`, including both position and velocity at **TDB** epoch.
2. Require exactly corresponding direct SPK segments; unrelated satellites, wrong parent centres, unsupported SPK type/frame or partial coverage must not count as suitable.
3. Inspect actual segment intervals for a conservative 1900–2100 TDB window, report gaps and verify independently pinned SHA-256. The official catalogue's MD5 is a transport cross-check, **not** a SHA-256 replacement.
4. Preserve existing DE442s verification for any composed Jupiter state. Never use the satellite kernel's embedded global planetary coordinates as the base silently.
5. Provide stable machine-readable JSON with observed/expected hashes, segment index, type/frame, real intervals, selected sample state and **NOT QUALIFIED** numerical status until a matched independent reference has run.
6. Retain original filenames and JPL provenance. Do not redistribute modified kernels before independent review of NAIF's modified-kernel attribution/validation rules.
7. Fail safely on missing or corrupt data. Lack of a source or pinned digest must **not** be reported as a successful qualification.

## Compatibility and operations

- Current v0.1.0 Python/CLI outputs are unchanged; no application code touched.
- Run offline, explicitly from locally installed source SPKs. No unapproved runtime downloads, new dependencies, secret handling, telemetry or production kernel files committed.
- Full six-source acquisition may require gigabytes of storage; measure actual sizes and extraction feasibility before a compact package design.
- Keep the candidate choice and SHA-256 manifest versioned and reviewable; any later amended candidate needs new qualification evidence.

## Acceptance gates

- [x] Six direct centre targets and suitable JPL **candidate** solutions documented from official catalogue/`BRIEF` summaries.
- [x] Read-only source probe and kernel-independent contract tests committed.
- [x] All six actual SPK sources downloaded, official MD5 checked and separate-commit SHA-256 pins verified (Jupiter [WP1/WP2](../p1-jupiter-centre-qualification.md), other five [WP3](../p1-five-centres-qualification.md)).
- [x] All six direct segment IDs, type-2/frame-1 compatibility and continuous 1900–2100 TDB coverage verified from real SPK binaries.
- [x] Jupiter DE442s + JUP349 centre state and velocity calculated with verified source hashes, [J2000 evidence](../p1-jupiter-centre-qualification.md).
- [x] All six same-kernel CSPICE evaluator comparisons passed initial limits (Jupiter 9 and other planets 11 epochs each). Independent physical model accuracy and commercial product qualification remain separate.
- [ ] Compact source packaging/licence design measured, reviewed, documented.
- [x] Fast CI, Jupiter pinned-source and all-five WP3 pinned-source workflows passed. Application and production release qualification remain open.

**Exit:** only after observed evidence for all gates; source feasibility by itself does not qualify production planet-centre calculations or close wider RM-001-P1.

## Validation and execution record

### Performed / available

- Read Aria source, AGENTS, roadmap and qualification conventions; verified the declared main baseline.
- Queried official JPL satellite-file catalogue, NAIF SPK directory, `aa_summaries.txt`, published MD5 checksums and NAIF use rules.
- Created `tools/datasets/audit_planet_centres.py` and `tests/unit/test_planet_centre_audit.py`; audit is read-only and its tests use synthetic segment records.
- Inspected repository source/report/changes through connected GitHub; record eventual GitHub CI result separately.

### Blocked / not run

- Original local shell DNS failure: **Could not resolve host**. The separate network-enabled GitHub Actions runners successfully acquired, hash-verified and audited all six planet-centre sources.
- Local shell lacked numerical dependencies; controlled GitHub runner installed them and passed the [Jupiter](../p1-jupiter-centre-qualification.md) and [five-planet](../p1-five-centres-qualification.md) independent evaluator and source identity checks.
- Existing numerical qualification and performance claims remain historical, not rerun.

## Delivery record

This is a separately owner-started implementation increment on `feature/rm-001-002-centre-source-feasibility-20261118`. Deliver WP3 in a **draft PR for review** now that all six source/evaluator gates have observed passing evidence; compact pack/licensing and commercial release qualification remain unimplemented. Do not merge, publish or deploy without subsequent permission. Update [progress](../progress.md) and the [prompt register](README.md) when the actual CI status and subsequent binary checks become available. Keep RM-001-P1 Planned until its broader dependencies are accepted. The production multi-kernel resolver requires a separately authorised implementation work package.
