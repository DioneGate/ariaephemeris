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


## Planning review — 2026-11-15

The latest checked `main` is [`0791564`](https://github.com/DioneGate/ariaephemeris/commit/079156477e57959877c63b4047ca1b7163f498de); package version remains 0.1.0. The 20 October baseline above is retained as historical evidence.

This **documentation-only** review adds repository agent governance and makes the existing RM-001 commercial-release boundary more explicit: provider-call inventory, application migration evidence, planetary barycentre/centre compatibility, staged Python performance optimisation and a benchmark-gated Rust proof of concept. No P1–P8 delivery phase was implemented or accepted. No tests, kernel qualification, benchmarks, application integration, release or deployment were executed as part of this review. The documentation changes are committed on a dedicated branch and proposed in [PR #1](https://github.com/DioneGate/ariaephemeris/pull/1); the PR is not merged and no implementation phase status changed.

## Prompt preparation — 2026-11-18

Rechecked **Aria Ephemeris main** at [`22b8cdf`](https://github.com/DioneGate/ariaephemeris/commit/22b8cdfc321dccf05d2683e57728e8e49897f830), package 0.1.0, and inspected **Aria Galaxy (DioneGate/archetypal-activation) main** read-only at [`4ab5f99`](https://github.com/DioneGate/archetypal-activation/commit/4ab5f99f277d9c9a221bcf911a820fd9eda50972).

Created [RM-001/001](prompts/001-commercial-calculation-contract-and-baseline.md) from the standard implementation-prompt template. It is an **unexecuted** bounded P1 source/contract inventory, proposed launch-scope and repeatable baseline task. Inspected the engine's models, conventions, qualification, architecture, licence documentation and the application's frontend ephemeris adapter, native backend ephemeris and chart call paths, chart data/analysis contracts, object registry, local time resolution and activation ownership. Explicit differences include Aria planetary-system barycentres versus centre-sensitive chart expectations; current application provider/provenance schema literals; apparent chart versus true-position activation defaults; 0001–2999 application date contract versus the engine's 1900–2100 TT operational interval and narrower civil time; unsupported nodes, Placidus, Lahiri and optional derived points.

Branch: [`docs/rm-001-001-commercial-calculation-contract-20261118`](https://github.com/DioneGate/ariaephemeris/tree/docs/rm-001-001-commercial-calculation-contract-20261118); [PR #2](https://github.com/DioneGate/ariaephemeris/pull/2) **open, not merged**. Prompt status is **Planned**; RM-001-P1 through P8 remain Planned. Owner launch scope and accuracy/date/provider/schema choices remain open; future prompt execution requires separate authorisation.

**Verification boundary:** GitHub source/Markdown inspection and read-back only; no numerical code change, tests, kernel download, qualification, benchmark, HTTP service, application commit, release or deployment. Historical numerical/test results above are not rerun or promoted to contemporary passes. Separately verified [PR #1's 15 November merge](https://github.com/DioneGate/ariaephemeris/commit/22b8cdfc321dccf05d2683e57728e8e49897f830); the preceding review entry described PR #1 as open *at that earlier review time*.

## Delivery log

| Date | Phase/prompt | Change and evidence | Validation | Deployment |
| --- | --- | --- | --- | --- |
| 2026-10-20 | Planning administration only | Saved the standalone eight-phase plan, roadmap register, reusable templates and empty prompt register | Existing framework/source inspection; new document links, identifiers, status consistency and scope checked | Documentation only; no runtime deployment |
| 2026-11-15 | RM-001 documentation review | Added AGENTS.md and refined RM-001 on [docs branch](https://github.com/DioneGate/ariaephemeris/tree/docs/agents-rm001-commercial-readiness-20261115); [PR #1](https://github.com/DioneGate/ariaephemeris/pull/1) opened for review then merged at `22b8cdf` on 15 November | GitHub repository and documentation inspection only; numerical tests not run | Documentation only; no runtime deployment |
| 2026-11-18 | RM-001/001 prompt preparation (not execution) | Authored P1 [prompt](prompts/001-commercial-calculation-contract-and-baseline.md), updated registers/index; [PR #2](https://github.com/DioneGate/ariaephemeris/pull/2) open for review, unmerged | Both repository heads and relevant source/contracts inspected read-only; Markdown prompt/register/progress read-back verified; branch comparison confirms five documentation-only files; numerical tests and kernel checks not run | Documentation only; no application/runtime deployment |

Record subsequent increments here with exact phase/prompt ID, branch/PR,
review/merge evidence, commands/results, remaining gaps and deployed-version
status. Do not mark work Done until its merge and acceptance are verified.
The roadmap README owns phase status; this log owns evidence.

## Next action

Review and approve or amend the [RM-001/001 prompt](prompts/001-commercial-calculation-contract-and-baseline.md) in [PR #2](https://github.com/DioneGate/ariaephemeris/pull/2). Resolve or track outstanding scope/conventions/qualification owner decisions and separately authorise P1 execution. Recheck both `main` branches before any implementation or evidence runs. Do **not** mark RM-001/001 or RM-001-P1 Done from prompt generation, documentation merge, or unexecuted test instructions.
