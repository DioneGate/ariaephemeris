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

## RM-001/001 evidence execution — 2026-11-18

**Authorisation and boundary:** owner requested execution of RM-001/001 after prompt PR #2 was [merged into main as `36a9cec`](https://github.com/DioneGate/ariaephemeris/commit/36a9cec742e8248fdee599b7cf620b2b19d12cc7). Checked the new engine `main` at exactly `36a9cec742e8248fdee599b7cf620b2b19d12cc7` (Python package 0.1.0) and Aria Galaxy `main` at exactly [`4ab5f99`](https://github.com/DioneGate/archetypal-activation/commit/4ab5f99f277d9c9a221bcf911a820fd9eda50972) read-only. Changes are **documentation/evidence only** on [`docs/rm-001-001-execution-20261118`](https://github.com/DioneGate/ariaephemeris/tree/docs/rm-001-001-execution-20261118), submitted as [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3), **open and unmerged**.

**Four execution deliverables:**

1. [P1 capability matrix](p1-capability-matrix.md): **29** current application canonical chart object rows and **19** cross-cutting operation rows, every row linked to source/semantics/qualification/coverage/owner/phase/fixture. Recognises app `true_node` range alias and potential native mean-node fallback, physical planetary centre vs Aria system barycentre, V6 documents and V2 aspect policies.
2. [P1 proposed numerical calculation contract](p1-calculation-contract.md): explicit physical target IDs, frames, correction and time/data version choices, rates/house/sect semantics, provenance/errors, provider schema evolution, selected historic comparison thresholds, no implied equivalence.
3. [P1 candidate launch/decision register](p1-launch-scope-and-decisions.md): commercial versus research pilot scope and **14 open owner decisions** D01–D14, all expressly unapproved; paid launch of ordinary planet-labelled charts blocked until the physical-centre choice is resolved and qualified.
4. [P1 qualification baseline](p1-qualification-baseline.md): exact JPL DE442s manifest SHA, existing historical 2026-10-10 qualification/benchmark scope, **11 proposed independent fixture groups** F01–F11, actual attempted commands, blocked numerical replay and reproducible runner procedure.

**Validation actually performed:** Connected GitHub inspected both exact source heads, engine manifest, source, app chart/series contracts and historical reports. Read-back of each new Markdown file confirmed expected content and cross-links (29 object rows, 14 owner decisions, 11 fixtures). Environment probe on 2026-11-18 gave Python 3.13.5, Linux 6.18.57; local checkout/kernel absent, required Python numerical packages absent. Attempted `git ls-remote https://github.com/DioneGate/ariaephemeris.git HEAD` failed `Could not resolve host: github.com`. **Therefore no fresh numerical fast tests, kernel qualification, benchmark, package build or app E2E tests were run**. Never conflate documentation inspection with a numerical pass or deployment acceptance.

**Known blockers and follow-ups:** a pinned, network-enabled (or pre-populated) runner and verified kernel are needed to replay qualification; D01–D14 require owner disposition before downstream phases are Ready. Historical reported 0.1.0 batch 67.63 seconds at ten-body 10,000-epoch load remains an unmet proposed capacity requirement. No centre target substitution, P3 functionality, HTTP adapter, app code, new runtime data, merge, publish or deployment was performed. Prompt **In review**, parent **RM-001-P1 Planned**, P2–P8 Planned; PR #3 is for review, not completed acceptance.

## RM-001/002 source feasibility — 2026-11-18

**Owner direction:** pursue physical centres for six major planets without silently changing the current barycentre profile. Inspected Aria Ephemeris main `36a9cec` and official JPL/NAIF catalogue, BRIEF summaries, MD5 and rules. Published NAIF text confirms 499/4 MAR099, 599/5 JUP349, 699/6 SAT456, 799/7 URA184 part 3, 899/8 NEP105, and 999/9 PLU060, with nominal ranges spanning 1900–2100. This is **published whole-kernel/BRIEF summary evidence**; per-target binary segment types, frames, continuity, locally computed SHA-256 and numerical agreement are not verified.

**Branch:** `feature/rm-001-002-centre-source-feasibility-20261118`, based on **main `df96380`** ([RM-001/001 PR #3 merged](https://github.com/DioneGate/ariaephemeris/commit/df96380ee851e3aeac1962ec6010807342f3b7da)); the older 001 execution entry captures the state before its merge. **Deliverables:** [source feasibility and gates](p1-centre-source-feasibility.md), [bounded prompt](prompts/002-physical-planet-centres-source-feasibility.md), `tools/datasets/audit_planet_centres.py` (offline read-only SPK target/parent/type/frame/coverage/hash + optional verified-base Jupiter composition), and `tests/unit/test_planet_centre_audit.py` (synthetic source/coverage/error tests). No existing engine source, application code, defaults or production data changed.

**Actual limitations:** shell `curl` to NAIF/JPL failed DNS (`Could not resolve host`); host lacks `jplephem`, `spiceypy`, DE442s and six supplementary SPKs. **All real-kernel centre inspection, composed Jupiter state, reference residual, compact-pack measurement and independent numerical qualification NOT RUN.** The synthetic tests are subject to CI reporting and cannot substitute for numerical evidence. Prompt **Blocked** pending a controlled runner; RM-001-P1 **Planned**; no merge, release or deployment approved.

## RM-001/002 WP1/WP2 Jupiter real-kernel execution — 2026-11-18

**Passing evidence:** [initial Jupiter workflow #44402646337](https://github.com/DioneGate/ariaephemeris/actions/runs/44402646337) downloaded `jup349.bsp` (97,525,760 bytes), verified NAIF published MD5 `c7ef9d1829bb39bbbc2ba30d4a5a8a05`, observed SHA-256 `a8f682fd0f156db47ee9672e0276f0842eb70d3ade8533fed59e38b6d5032971` and verified two 599/5 type-2/frame-1 SPK segments with no gaps across 1900–2100. A separate commit pinned SHA-256 in [source manifest](jupiter-source-manifest.json); [pinned workflow #44402922404](https://github.com/DioneGate/ariaephemeris/actions/runs/44402922404) **completed successfully**, including both checksums, pinned auditor, nine geometric/J2000 TDB samples compared with CSPICE, and artifact upload.

**Measured residuals:** maximum position disagreement **0.0059855203 m**, velocity disagreement **9.54658e-8 mm/s**, against provisional same-source evaluator limits of 1 m and 1 mm/s. Details including J2000 state, direct segment spans and limitations in [Jupiter qualification record](p1-jupiter-centre-qualification.md). **This is same-kernel independent evaluator agreement, NOT physical astronomical model accuracy nor commercial launch qualification.** The local shell DNS obstacle was bypassed by a GitHub Actions runner. Existing engine outputs and Aria Galaxy code unchanged.

**Status:** Jupiter WP1/WP2 **completed with passing evidence**, remaining five centre source kernels and six-body packaging source feasibility **Blocked**; RM-001-P1 **Planned**, RM-001/002 overall not Done, PR #4 draft and unmerged.

## Delivery log

| Date | Phase/prompt | Change and evidence | Validation | Deployment |
| --- | --- | --- | --- | --- |
| 2026-10-20 | Planning administration only | Saved the standalone eight-phase plan, roadmap register, reusable templates and empty prompt register | Existing framework/source inspection; new document links, identifiers, status consistency and scope checked | Documentation only; no runtime deployment |
| 2026-11-15 | RM-001 documentation review | Added AGENTS.md and refined RM-001 on [docs branch](https://github.com/DioneGate/ariaephemeris/tree/docs/agents-rm001-commercial-readiness-20261115); [PR #1](https://github.com/DioneGate/ariaephemeris/pull/1) opened for review then merged at `22b8cdf` on 15 November | GitHub repository and documentation inspection only; numerical tests not run | Documentation only; no runtime deployment |
| 2026-11-18 | RM-001/001 prompt preparation (not execution) | Authored P1 [prompt](prompts/001-commercial-calculation-contract-and-baseline.md), updated registers/index; [PR #2](https://github.com/DioneGate/ariaephemeris/pull/2) opened then merged into `main` at `36a9cec` | Both repository heads and relevant source/contracts inspected read-only; Markdown prompt/register/progress read-back verified; branch comparison confirms five documentation-only files; numerical tests and kernel checks not run | Documentation only; no application/runtime deployment |
| 2026-11-18 | RM-001/001 execution, **In review** | [Four P1 source/evidence documents](p1-capability-matrix.md) delivered on [execution branch](https://github.com/DioneGate/ariaephemeris/tree/docs/rm-001-001-execution-20261118); [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3) open, unmerged; 14 owner decisions remain Open | Read-only sources and Markdown read-back checked (29 object rows; 14 decisions; 11 fixtures); local Git clone **DNS-blocked**, no kernel; **all numerical tests NOT RUN** | Documentation only; no app code, merge, package release or deployment |

| 2026-11-18 | RM-001/002 started; **Blocked** on real-kernel evidence | Source matrix, offline audit and synthetic coverage tests on dedicated feature branch; draft PR for review | Official summaries reviewed, binary source checks and independent Jupiter comparison **NOT RUN**; CI separately pending | No engine runtime changes, no app changes, no merge, release or deployment |

Record subsequent increments here with exact phase/prompt ID, branch/PR,
review/merge evidence, commands/results, remaining gaps and deployed-version
status. Do not mark work Done until its merge and acceptance are verified.
The roadmap README owns phase status; this log owns evidence.

## Next action

Run [RM-001/002's six-source audit and Jupiter independent comparison](p1-centre-source-feasibility.md) on a host with pinned local SPK files; do not mark binary source feasibility or numerical acceptance as passed from the NAIF text inventory. Separately review [RM-001/001 execution PR #3](https://github.com/DioneGate/ariaephemeris/pull/3), resolve owner decisions D01–D14 in the [launch decisions](p1-launch-scope-and-decisions.md), and run the [pinned numerical replay](p1-qualification-baseline.md) on a host with checkout, dependencies and checksum-verified DE442s data. A further implementation prompt may be warranted for each unresolved P2/P3 gate but must be explicitly requested. **Do not merge PR #3 without separate authorisation.** RM-001/001 remains In review; RM-001-P1 is Planned pending full owner acceptance and numerical evidence.
