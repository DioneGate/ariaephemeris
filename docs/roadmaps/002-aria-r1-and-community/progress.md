# RM-002 — Progress and evidence

[Epic and increments](README.md) · [Prompt register (stories)](prompts/README.md)

## Baseline — 2026-11-28

Repository: DioneGate/ariaephemeris. Inspected `main` at
[`0cbb394`](https://github.com/DioneGate/ariaephemeris/commit/0cbb394) (24 November 2026).
Package version 0.1.0. Recheck `main` before generating any story.

**Evidence class:** source and documentation inspection, plus one ad-hoc local test run
(described below). No real-kernel qualification, benchmark, service or deployment was run
for this baseline.

### Reusable foundations (from source and historical RM-001 records)

- Sun, Moon, Mercury, Venus and the Mars–Pluto system barycentres (default `reference`
  profile); an opt-in `planet-centres-v1` physical-centre profile using six external satellite
  SPKs (about 2.18 GB). See the [README](../../../README.md) and RM-001/002–003.
- Apparent and geometric positions; geocentric, heliocentric and topocentric origins; signed
  rates; batches; bounded ingress, aspect and station searches.
- Angles (ASC/MC) and Equal/Whole Sign cusps in `src/ariaephemeris/astrology/__init__.py`.
- Civil time with pinned tzdata 2026.6, an opt-in historical pre-1972 approximation, managed
  offline EOP, and bounded birth-time sampling (RM-001/011–013, merged).
- Historical qualification 0.1.0 (10 October 2026): DE442s, 1900–2100 TT, apparent direction
  maximum 4.794e-06″ against the matched reference. Warm ten-body chart median 77.4 ms;
  10-body × 10,000-epoch batch **67.63 s**. See [validation](../../validation/README.md).
- DE442s source coverage is 1849-12-26 to 2150-01-22 TDB (`resources/de442s.json`). It is
  qualified only for 1900–2100.

### Verified gaps for R1.0 (source inspection)

- There is no implementation of the mean or true lunar nodes, Lilith, Vertex, Part of Fortune,
  sect, angle rates, Placidus or other house systems, sidereal modes, or minor bodies. A grep
  of `src/` finds none of them.
- The bundled leap table expires on **28 June 2027**. After that date, strict UTC fails by
  design ([time policies](../../time-policies.md)).
- There is no service process. The CLI and library are the only entry points.
- The application integration is not started. Per the RM-001 capability matrix, the app has two
  independent SE consumers (chart and range) and a silent true-node → mean-node fallback.
- RM-001 decisions D02–D14 are Open. D01 was resolved as physical centres; RM-002 E05 proposes
  revisiting it for R1.0.

### Ad-hoc check (not a baseline pass)

On 2026-11-28, with **unpinned** Python 3.13.18 and packages installed outside
`requirements/development.lock`, `pytest -m 'not kernel'` gave 173 passed and 1 failed
(`tests/unit/test_math.py::test_independent_limited_deflection_equation_matches_standard`).
In addition, `tests/unit/test_planet_centres_qualification.py` could not be collected because
`spiceypy` was missing. This run does not meet the supported environment (Python 3.12, pinned
lock). Treat the failure as unverified until it is reproduced on the pinned environment in
RM-002-P1.

## Delivery log

| Date | Increment/story | Change and branch/PR/merge evidence | Validation | Deployment |
| --- | --- | --- | --- | --- |
| 2026-11-28 | RM-002 registration | Epic, increments, decisions and agile vocabulary recorded on branch `claude/youthful-fermat-k1vlpy` (planning documentation only) | Documentation only; no code changed | None |

A roadmap-registration entry is planning administration, not increment delivery.

## Next action

The owner reviews and resolves decisions E01–E20, starting with E01, E03, E05, E09 and E10,
which shape the critical path. Then request the first RM-002-P1 story. Recording this plan
does not authorise implementation, application-repository changes, merge, publication or
deployment.
