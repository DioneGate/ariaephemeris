# RM-001 — Progress and evidence

[Roadmap and phase statuses](README.md) · [Prompt register](prompts/README.md)

## Baseline — 2026-10-20

Repository: DioneGate/ariaephemeris. Inspected main at
[`39b25ae`](https://github.com/DioneGate/ariaephemeris/commit/39b25aec9023bcc79172a0f0cf7aed373efafc89),
dated 10 October 2026. Package version: 0.1.0. Recheck main before generating a
phase prompt or implementing work; this is a dated source baseline.

### Reusable foundations

| Capability | Existing evidence | Work remaining |
| --- | --- | --- |
| Offline Python API and JSON CLI | [README](../../../README.md), [package metadata](../../../pyproject.toml), [engine](../../../src/ariaephemeris/engine.py) | Contract inventory and application integration |
| Verified JPL DE442s data | [Dataset manifest](../../../src/ariaephemeris/resources/de442s.json), [dataset installer](../../../src/ariaephemeris/datasets/__init__.py) | Multiple datasets and controlled update policy |
| Positions, rates and motion | [Conventions](../../conventions.md), [validation](../../validation/README.md) | Broader model/target qualification and selected additional points |
| Angles, equal/whole-sign houses and aspects | [Astrology module](../../../src/ariaephemeris/astrology/__init__.py) | Standalone public house API, angle rates and selected additional systems |
| Bounded event searches | [Events](../../../src/ariaephemeris/events/__init__.py), [validation](../../validation/README.md) | Additional techniques and feature-specific completeness evidence |
| Fast checks, packaging and qualification tooling | [Fast CI](../../../.github/workflows/ci.yml), [kernel workflow](../../../.github/workflows/qualification.yml) | Exact-release and deployment acceptance for the intended offering |

### Constraints and qualification boundaries

- Operational interval is 1900-01-01 through 2100-12-31 TT. Civil-time constraints
  are narrower; pre-1972 civil UTC is rejected and strict charts need Earth-rotation inputs.
- The pinned leap table expires on 28 June 2027. Strict later UTC is rejected.
  No time-data update or broader civil-time support is delivered by this roadmap.
- Mars–Pluto targets are planetary-system barycentres, qualified as those targets.
- Additional points, houses, sidereal modes, minor bodies and compact packs remain planned.
- Recorded numerical qualification sampled 4,712 epochs per target and 680 events
  in 39 declared windows. It is not a new test run, a physical uncertainty bound,
  or a universal completeness proof.
- Recorded warm ten-body median is 77.4 ms; a ten-body 10,000-epoch batch took
  67.63 s on the documented shared host. These are not application service-level results.
- [Fast CI 38050411850](https://github.com/DioneGate/ariaephemeris/actions/runs/38050411850)
  passed for the inspected implementation head. A full-kernel workflow exists;
  this planning record does not claim that workflow has run successfully.
- No release or application deployment is established by this planning increment.
  Integration remains future work.

### Evidence boundary

This record uses repository/source inspection and existing committed evidence.
No numerical tests, kernel download, qualification, benchmark or production check
was rerun to create the roadmap framework. All P1–P8 phase status remains Planned.
Saving this framework does not complete the P1 calculation-contract/baseline gate.

## Delivery log

| Date | Phase/prompt | Change and evidence | Validation | Deployment |
| --- | --- | --- | --- | --- |
| 2026-10-20 | Planning administration only | Saved the standalone eight-phase plan, roadmap register, reusable templates and empty prompt register | Existing framework/source inspection; new document links, identifiers, status consistency and scope checked | Documentation only; no runtime deployment |

Record subsequent increments here with exact phase/prompt ID, branch/PR,
review/merge evidence, commands/results, remaining gaps and deployed-version
status. Do not mark work Done until its merge and acceptance are verified.
The roadmap README owns phase status; this log owns evidence.

## Next action

Await the owner's request to generate the first bounded P1 implementation prompt.
Then recheck main, inspect current contracts and register RM-001/001 with its
actual readiness, dependencies and source baseline. No delivery prompt is created
or executed by the roadmap-registration task.
