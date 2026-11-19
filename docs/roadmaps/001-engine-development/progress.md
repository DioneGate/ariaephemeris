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

## RM-001/002 WP3 five-source pinned qualification — 2026-11-18

**Baseline and delivery:** [PR #4 was merged](https://github.com/DioneGate/ariaephemeris/commit/03af9337d073dbe424b534de829619cc6a4e301e). Began WP3 on fresh branch `feature/rm-001-002-wp3-five-centres-20261118`, [draft PR #5](https://github.com/DioneGate/ariaephemeris/pull/5). Added `tools/datasets/qualify_planet_centres.py`, kernel-independent tests, a parallel GH Actions matrix, official NAIF [five-source manifest](planet-centre-source-manifest.json), [retained result JSON](p1-five-centres-evidence.json) and [narrative qualification report](p1-five-centres-qualification.md). Did not change existing `src/`, calculated body targets, Aria Galaxy or distributed SPK files.

**Source discovery run:** [#44410136973](https://github.com/DioneGate/ariaephemeris/actions/runs/44410136973) passed for Mars, Saturn, Uranus, Neptune and Pluto. Original satellite kernels matched NAIF published MD5s. Observed SHA-256 digests were recorded separately in the committed manifest; the initial workflow's wildcard artifact upload did not include hidden `.artifacts/` reports (detected in actual job logs), later fixed. Fast CI initially flagged Ruff formatting; corrected.

**Pinned replay:** [#44410508647](https://github.com/DioneGate/ariaephemeris/actions/runs/44410508647) **all five jobs PASS** with the **previously committed** SHA-256 pins, MD5 and DE442s checks, direct target-to-barycentre segment inspection and eleven matched TDB epoch CSPICE evaluator comparisons per planet. All five have **two direct type-2/frame-1 segments and zero gaps** in the audited 1900–2100 interval; all pass the provisional 1 m / 1 mm/s same-source evaluator bounds. Position max residuals (m): Mars 0.0114078, Saturn 0.0045663, Uranus 0.0032164, Neptune 0.0027392, Pluto 0.0022310. No SPK binaries in uploaded artifacts; JSON files were downloaded and inspected to generate the repository's machine-readable evidence. [Fast CI #44410508459](https://github.com/DioneGate/ariaephemeris/actions/runs/44410508459) **PASS** (lint, formatting, mypy, audit, non-kernel tests, build, smoke). Existing general DE442s qualification is separate.

**Acceptance boundary:** Jupiter's separately qualified 599/5 and all five WP3 sources establish **six SHA-pinned, compatible physical-centre offset sources** and numerical same-kernel evaluator checks. This does not independently certify their physical model accuracy, differential dynamical model consistency, geocentric apparent horoscope positions, civil-time handling, commercial pack redistribution or Aria Galaxy provider replacement. Production multi-kernel resolver and `planet-centres-v1` calculation profile remain **unimplemented** and require a new, scoped code work package. PR #5 **draft/unmerged**; RM-001/002 **In review** for sources; RM-001-P1 remains **Planned**.

## RM-001/003 — WP4 multi-kernel calculation engine — 2026-11-19

**Owner-approved implementation:** [draft PR #6](https://github.com/DioneGate/ariaephemeris/pull/6) on `feature/rm-001-002-wp4-multi-kernel-centres-20261119` from `main bfe4a636` (the verified merge of [WP3 PR #5](https://github.com/DioneGate/ariaephemeris/commit/bfe4a636356366514a213c63be07cffd48b5a337)). Engine source modified only in Aria Ephemeris; **no Aria Galaxy code, merge, package publication or deployment**.

**Implementation:** Package-pinned SHA-256/size source manifest in `src/ariaephemeris/resources/planet-centres.json`; strict offline verifier `datasets.verify_centre_sources`; new `sources/centres.py` resolver composing **direct physical target offset + DE442s planet system barycentre**, never alternate planetary positions inside the satellite files; `planet-centres-v1` target/profile selection in raw states, scalar/batch positions, chart and events; position-mode light-time evaluated with selected centre targets; self-deflection avoided; physical-profile source hashes/identities and **explicit not-commercially-qualified status** in metadata; new CLI `--centre-kernel BODY=FILE` option and matching JSON schemas. Original v0.1.0 `reference` profile and all default target identities are unchanged.

**Tests:** fail-closed source identity/corruption/coverage/type/frame/partial-installation unit tests, physical event profile and false-certificate safeguards, real-source per-planet scalar/batch/reference parity, geometric/apparent/rate/provenance checks, and combined all-six-loaded ten-body chart and batch CI. Qualification workflows extended, but WP4 does not claim an independently established physical model error budget or commercial app parity.

**Verification and gates:** [Real-source Jupiter workflow](https://github.com/DioneGate/ariaephemeris/actions/runs/44471515305) **passed** and [five-source runtime matrix](https://github.com/DioneGate/ariaephemeris/actions/runs/44471515371) **5/5 passed** on an earlier amended source revision; subsequent tests/documentation were refined. [Full six-source workflow #44471769118](https://github.com/DioneGate/ariaephemeris/actions/runs/44471769118) **completed successfully**: six pinned unmodified JPL SPKs verified and loaded simultaneously, full ten-body physical-centre positions, whole-sign chart and batch passed. Later revisions are subject to their own CI. [Fast checks](https://github.com/DioneGate/ariaephemeris/actions/runs/44471515337) and standard [DE442s regression](https://github.com/DioneGate/ariaephemeris/actions/runs/44471515277) identified formatting/typing and unit assertion issues on earlier commits; those were addressed in subsequent commits, with final CI results to be recorded separately. These early failures are not claimed as passing.

**Open scope:** full-source performance and memory profile, representative independent apparent positions/rates/event fixtures, model-combination compatibility, commercially suitable compact pack/licensing, complete data installation experience, HTTP service and provider-neutral Aria Galaxy migration. WP4 code **In review** until final checks and owner approval; RM-001-P3 and parent P1 still **Planned**. Do not merge/release/deploy without separate authorisation.

## RM-001/004 — WP5.1 independent Horizons fixture acquisition, 2026-11-19

**Owner authorisation:** explicitly requested WP5.1 implementation, brief report and **merge into `main` after successful checks**. Work branch `feature/rm-001-004-independent-horizons-fixtures-20261119`, [PR #7](https://github.com/DioneGate/ariaephemeris/pull/7). Baseline is `main e8b0642`, after WP4 PR #6 merged. The work does not modify `src/` or change any chart outputs, profile defaults, application code, SPK packages or deployment.

**Independent reference acquisition observed:** the [original NASA/JPL Horizons API](https://ssd.jpl.nasa.gov/api/horizons.api) returned 12 complete responses, stored under [`data/fixtures/horizons/raw/`](../../../data/fixtures/horizons/raw/). Manifest [`horizons-reference-v1.json`](../../../data/fixtures/horizons/horizons-reference-v1.json) stores exactly **300 records** from six physical planet centres × 25 epochs × geometric `TDB/ICRF/499 etc` vectors and apparent `TT/ICRF/quantity-45` positions. Query URLs, API signatures, target and centre source lines, raw SHA-256 and independent-source model choices are retained. Dates are stratified from 1900 through 2100, with selected kernel join ±0.04-day samples and four anchors; no reference case was calculated using Aria.

**Observed source differences:** Horizons labels Mars `mar099`, Jupiter `jup365_merged`, Saturn `sat441l`, Uranus `ura184_merged`, Neptune `nep098_merged` and Pluto `plu060_merged`, with DE441 appearing in several centre/observer source headers. These are **not necessarily Aria's DE442s + six pinned supplementary kernels**; WP5.2 must distinguish scientific source-model differences from implementation errors, and separately align TT and TDB epochs before comparisons.

**Validation:** the initial new offline verifier run passed its complete 12-response SHA-256/300-row semantic check, demonstrating the frozen data matches its archived JPL responses. Initial fast CI flagged only Ruff formatting in newly authored files, and the independent test workflow lacked an installed package; both were corrected. Subsequent CI statuses are tracked on [PR #7](https://github.com/DioneGate/ariaephemeris/pull/7) and must be recorded as actually observed, not presumed. Live acquisition has been restricted to manually dispatched workflow runs; routine CI only checks the frozen files offline.

**Post-merge verification (19 November 2026):** [WP5.1 PR #7](https://github.com/DioneGate/ariaephemeris/pull/7) merged into main at [`fa8e5b7a4a71d01999f712da7b25cbeb711e5510`](https://github.com/DioneGate/ariaephemeris/commit/fa8e5b7a4a71d01999f712da7b25cbeb711e5510). [Offline integrity + acquisition parser CI #44474930652](https://github.com/DioneGate/ariaephemeris/actions/runs/44474930652) **passed**; [fast CI #44474930651](https://github.com/DioneGate/ariaephemeris/actions/runs/44474930651) **passed** (Ruff, formatting, mypy, licence audit, nonkernel tests, build and package smoke). **Actual main read-back** found `case_count=300` and the same fixture file blob SHA as the merged branch. RM-001/004 is **Done for reference acquisition only**, not physical-profile accuracy qualification. Ordinary numerical/deployment gates remain separate.

**Acceptance boundary:** WP5.1 is independent **source acquisition**, not an Aria-vs-Horizons comparison, absolute planetary accuracy certification, event root acceptance or commercial release. See [WP5.1 report](p1-independent-horizons-fixtures.md) and [bounded prompt](prompts/004-independent-horizons-reference-fixtures.md). Next is separately scoped WP5.2 external numerical comparison with source/convention diagnostics. Parent RM-001-P3/P6 remain Planned.

## Delivery log

| Date | Phase/prompt | Change and evidence | Validation | Deployment |
| --- | --- | --- | --- | --- |
| 2026-10-20 | Planning administration only | Saved the standalone eight-phase plan, roadmap register, reusable templates and empty prompt register | Existing framework/source inspection; new document links, identifiers, status consistency and scope checked | Documentation only; no runtime deployment |
| 2026-11-15 | RM-001 documentation review | Added AGENTS.md and refined RM-001 on [docs branch](https://github.com/DioneGate/ariaephemeris/tree/docs/agents-rm001-commercial-readiness-20261115); [PR #1](https://github.com/DioneGate/ariaephemeris/pull/1) opened for review then merged at `22b8cdf` on 15 November | GitHub repository and documentation inspection only; numerical tests not run | Documentation only; no runtime deployment |
| 2026-11-18 | RM-001/001 prompt preparation (not execution) | Authored P1 [prompt](prompts/001-commercial-calculation-contract-and-baseline.md), updated registers/index; [PR #2](https://github.com/DioneGate/ariaephemeris/pull/2) opened then merged into `main` at `36a9cec` | Both repository heads and relevant source/contracts inspected read-only; Markdown prompt/register/progress read-back verified; branch comparison confirms five documentation-only files; numerical tests and kernel checks not run | Documentation only; no application/runtime deployment |
| 2026-11-18 | RM-001/001 execution, **In review** | [Four P1 source/evidence documents](p1-capability-matrix.md) delivered on [execution branch](https://github.com/DioneGate/ariaephemeris/tree/docs/rm-001-001-execution-20261118); [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3) open, unmerged; 14 owner decisions remain Open | Read-only sources and Markdown read-back checked (29 object rows; 14 decisions; 11 fixtures); local Git clone **DNS-blocked**, no kernel; **all numerical tests NOT RUN** | Documentation only; no app code, merge, package release or deployment |

| 2026-11-18 | RM-001/002 started; **Blocked** on real-kernel evidence | Source matrix, offline audit and synthetic coverage tests on dedicated feature branch; draft PR for review | Official summaries reviewed, binary source checks and independent Jupiter comparison **NOT RUN**; CI separately pending | No engine runtime changes, no app changes, no merge, release or deployment |

| 2026-11-18 | RM-001/002 WP3; **source/evaluator gates in review** | Five-source manifest, CSPICE qualification matrix, 5 pinned JSON reports, PR #5 draft | [Pinned matrix #44410508647](https://github.com/DioneGate/ariaephemeris/actions/runs/44410508647) **5/5 pass**; fast CI #44410508459 **passed** | No runtime change, no app change, no merge/release/deployment |

| 2026-11-19 | RM-001/003 WP4 **In review** | Versioned physical-centre runtime profile on [draft PR #6](https://github.com/DioneGate/ariaephemeris/pull/6); source SHA manifests, resolver, CLI/schemas, tests and all-six workflow | Six per-source real-kernel profile tests passed on earlier revision; final CI and all-six workflow tracked in WP4 section | Engine branch only; no app modification, merge or deployment |

| 2026-11-19 | RM-001/004 WP5.1 — **Done** (bounded acquisition) | 300 original NASA/JPL records, raw responses, hashes, model provenance; [PR #7 merged](https://github.com/DioneGate/ariaephemeris/commit/fa8e5b7a4a71d01999f712da7b25cbeb711e5510) | Offline integrity #44474930652 **PASS**; fast CI #44474930651 **PASS** | Source evidence only; no chart calculation or deployment change |

Record subsequent increments here with exact phase/prompt ID, branch/PR,
review/merge evidence, commands/results, remaining gaps and deployed-version
status. Do not mark work Done until its merge and acceptance are verified.
The roadmap README owns phase status; this log owns evidence.

## Next action

WP5.1 [PR #7 merged at `fa8e5b7`](https://github.com/DioneGate/ariaephemeris/commit/fa8e5b7a4a71d01999f712da7b25cbeb711e5510) after passing source-integrity and fast CI checks. Next, separately authorise WP5.2 comparison of the new frozen reference data against `planet-centres-v1`, aligning TT/TDB and coordinate conventions, and diagnosing mismatched JPL source solutions before applying tolerances. No commercial release or Aria Galaxy migration is implied.
