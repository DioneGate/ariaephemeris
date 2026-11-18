# RM-001/002 — Physical planet-centre data feasibility and source qualification

| Field | Value |
| --- | --- |
| Roadmap | [RM-001 — Engine development and commercial readiness](../README.md) |
| Phase | RM-001-P1 (D01 source feasibility); prerequisite for selected RM-001-P3 calculations |
| Generated / started | 2026-11-18 |
| Baseline | Aria Ephemeris main `36a9cec742e8248fdee599b7cf620b2b19d12cc7`; Aria Galaxy unchanged |
| Product direction | Physical planet centres for Mars–Pluto, retain original barycentre mode; selected source/kernels and numeric standards require evidence and approval |
| Working branch | `feature/rm-001-002-centre-source-feasibility-20261118` |
| Prompt status | **Blocked** for real-kernel source qualification; code and documentary evidence committed for review |

Follow [AGENTS.md](../../../../AGENTS.md) and the [source feasibility evidence](../p1-centre-source-feasibility.md). RM-001/001's separate [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3) remains unmerged; this task does not silently accept its remaining D02–D14 decisions.

## Objective and expected behaviour

Demonstrate that centre-offset SPK segments 499/4, 599/5, 699/6, 799/7, 899/8, and 999/9 are suitable companions to the existing Aria DE442s base. Make selection, identity, coverage and sample calculation **auditable and reproducible**, without changing the current operational barycentre contract or conflating physical centres and system barycentres.

## Verified current state

- `src/ariaephemeris/models.py`: 4–9 currently represent Mars–Pluto system barycentres.
- `src/ariaephemeris/sources/__init__.py`: `Kernel` handles **single-SPK** target/centre resolution, JPL types 2/3, reference frame 1, last matching segment precedence, and km / km/day states.
- `src/ariaephemeris/datasets/__init__.py`: a single SHA-256-pinned DE442s manifest; no supplementary manifest/resolver.
- `src/ariaephemeris/positions/__init__.py`: existing correct mode-aware position and light-time pipeline; current actual body targets are declared in `docs/conventions.md`.
- JPL/NAIF published catalogues, direct centre/parent relationships and nominal `BRIEF` intervals for six candidate files are recorded in [the evidence report](../p1-centre-source-feasibility.md). Published text alone is not a binary segment validation.
- Executing host cannot resolve JPL domains, lacks SPKs and `jplephem`/`spiceypy` runtime dependencies. Numerical checks cannot be represented as passing.

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
- [ ] All six **actual** SPKs downloaded; source checksums cross-checked and SHA-256 pinned independently.
- [ ] All six direct segment IDs, types, frames and **continuous binary coverage** verified.
- [ ] At least one Jupiter DE442s + JUP349 centre state and velocity calculated with exact source hashes.
- [ ] Matching CSPICE/Horizons reference comparison performed and numerical residuals/tolerances reviewed.
- [ ] Compact source packaging/licence design measured, reviewed, documented.
- [ ] CI and normal local test suite show actual executed pass/skip statuses.

**Exit:** only after observed evidence for all gates; source feasibility by itself does not qualify production planet-centre calculations or close wider RM-001-P1.

## Validation and execution record

### Performed / available

- Read Aria source, AGENTS, roadmap and qualification conventions; verified the declared main baseline.
- Queried official JPL satellite-file catalogue, NAIF SPK directory, `aa_summaries.txt`, published MD5 checksums and NAIF use rules.
- Created `tools/datasets/audit_planet_centres.py` and `tests/unit/test_planet_centre_audit.py`; audit is read-only and its tests use synthetic segment records.
- Inspected repository source/report/changes through connected GitHub; record eventual GitHub CI result separately.

### Blocked / not run

- `curl -IL --max-time 12 https://naif.jpl.nasa.gov/.../jup365_2027.bsp` and `curl -IL --max-time 12 https://ssd.jpl.nasa.gov/sats/ephem/files.html`: **Could not resolve host** in the current command-line environment. No full candidate files downloaded.
- Python module probe: `jplephem` and `spiceypy` not installed. DE442s absent locally. Hence **NO actual source-segment/SPK-jplephem inspection, source SHA-256 comparison, Jupiter state output or independent CSPICE comparison**.
- Existing numerical qualification and performance claims remain historical, not rerun.

## Delivery record

This is a separately owner-started implementation increment on `feature/rm-001-002-centre-source-feasibility-20261118`. Deliver in a **draft PR for review** while the actual kernel-source and numerical gates are blocked. Do not merge, publish or deploy without subsequent permission. Update [progress](../progress.md) and the [prompt register](README.md) when the actual CI status and subsequent binary checks become available. Keep RM-001-P1 Planned until its broader dependencies are accepted.
