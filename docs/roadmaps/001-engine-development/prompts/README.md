# RM-001 — Implementation prompt register

[Roadmap](../README.md) · [Progress and evidence](../progress.md) ·
[Prompt template](../../templates/implementation-prompt.md)

RM-001/001 was separately authorised for execution on 18 November 2026. Four
source/contract/evidence documents have been delivered on [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3), **merged into main** at `df96380`. Prompt status is **In review**; owner scope decisions and a real-kernel replay are outstanding. The **parent RM-001-P1 phase and P2–P8 remain Planned**.

## Register

| Prompt ID | File | Phase | Status | Dependencies/blocker | Implementation evidence |
| --- | --- | --- | --- | --- | --- |
| RM-001/001 | [Commercial calculation contract, capability inventory and reproducible baseline](001-commercial-calculation-contract-and-baseline.md) | RM-001-P1 | **In review** | D01 direction selected; D02–D14 remain open; current host has no clone/kernel/pinned deps, so numerical replay blocked | Four [P1 deliverables](../README.md#rm-001001-execution-deliverables-reviewable-not-phase-acceptance) merged via [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3), docs only; source read-back passed; **real-kernel tests not run** |
| RM-001/002 | [Physical planet-centre source feasibility](002-physical-planet-centres-source-feasibility.md) | RM-001-P1 / RM-001-P3 prerequisite | **In review** (six source/evaluator gates passed) | Source binary, coverage, SHA-256 and CSPICE pass for all six; compact source-pack/redistribution and production accuracy gates remain open | [Jupiter evidence](../p1-jupiter-centre-qualification.md), [five-source evidence](../p1-five-centres-qualification.md), [PR #5](https://github.com/DioneGate/ariaephemeris/pull/5) merged at `bfe4a63` |

| RM-001/003 | [Versioned physical-centre multi-kernel engine profile](003-versioned-physical-centre-engine-profile.md) | RM-001-P3 (D01) | **Done** (implementation merged, release gates open) | Independent chart/reference qualification and compact source-pack remain future work | [PR #6](https://github.com/DioneGate/ariaephemeris/pull/6) merged into main at `e8b0642`; default reference mode preserved |
| RM-001/004 | [WP5.1 independent Horizons reference specification and fixture acquisition](004-independent-horizons-reference-fixtures.md) | RM-001-P3/P6 qualification prerequisite | **Done** (acquisition only) | WP5.2 comparison and source-model reconciliation remain outstanding; no commercial numerical qualification | [300 frozen records](../p1-independent-horizons-fixtures.md), 12 SHA-verified originals, [integrity CI](https://github.com/DioneGate/ariaephemeris/actions/runs/44474930652) and [fast CI](https://github.com/DioneGate/ariaephemeris/actions/runs/44474930651) passed, [PR #7 merged at `fa8e5b7`](https://github.com/DioneGate/ariaephemeris/commit/fa8e5b7a4a71d01999f712da7b25cbeb711e5510) |
| RM-001/005 | [WP5.2 independent geometric and apparent Horizons comparison](005-independent-horizons-numerical-comparison.md) | RM-001-P3/P6 qualification evidence | **Done** (comparison implemented/merged; scientific acceptance open) | Horizons and Aria use different source solutions; source-model reconciliation and commercial accuracy certification remain unresolved | [300-case measured results](../p1-external-horizons-comparison.md), [machine report](../../../validation/wp5-2-horizons-comparison.json), [fast CI #44478988481](https://github.com/DioneGate/ariaephemeris/actions/runs/44478988481) passed, [PR #9 merged at `6216f15`](https://github.com/DioneGate/ariaephemeris/commit/6216f15c9bac88bcfa5bf4eeadb444f7730b0ac1) |
| RM-001/006 | [Jupiter/Pluto JPL source-model reconciliation](006-jpl-source-model-reconciliation.md) | RM-001-P3/P6 scientific accuracy prerequisite | **Done** (source attribution; absolute accuracy open) | Jupiter/Pluto offsets agree with Horizons to 0.248/1.908 mm over 25 TDB epochs; DE441/DE442s barycentre models explain 14.82/40.91 km, while physical uncertainty and remaining four planets remain open | [Original source evidence](../../../validation/wp5-3-jpl-source-attribution.json), [analysis](../p1-jpl-source-reconciliation.md), [PR #11 merged at `0b5d6d6`](https://github.com/DioneGate/ariaephemeris/commit/0b5d6d661e5796a7d74889dcffc323741707c1bd) |
| RM-001/007 | [WP5.4 tropical coordinate/rate qualification](007-wp5-4-tropical-coordinate-qualification.md) | RM-001-P3/P6 external chart qualification evidence | **In review** (186 independent-source charts measured) | Six planets' sampled zodiac positions and signed rates agree with JPL source to provisional diagnostics; shared ERFA conventions, exact event timing and full-period absolute accuracy remain open | [186-case measured report](../p1-wp54-tropical-coordinate-qualification.md), [930 original JPL rays](../../../data/fixtures/horizons/wp54-tropical/wp54-horizons-tropical-stencils-v1.json), [numerical evidence](../../../validation/wp54-tropical-coordinate-comparison.json), [PR #12 draft](https://github.com/DioneGate/ariaephemeris/pull/12); no merge authority |


RM-001/002 was explicitly started by the owner on 2026-11-18. Jupiter WP1/WP2 and the five other WP3 sources now have SHA-pinned binary integrity, direct SPK coverage and independent **same-source** CSPICE evaluator evidence, delivered in merged [PR #5](https://github.com/DioneGate/ariaephemeris/pull/5). The source feasibility gate is **In review**, not a claim of commercial model accuracy or complete roadmap phase; compact packing and release qualification remain open. No merge or release is authorised.

WP4 runtime implementation was explicitly authorised by the owner and merged on 19 November 2026 as PR #6; the original `reference` defaults and release boundary remain intact. WP5.1 was separately authorised for implementation and merge, and [PR #7](https://github.com/DioneGate/ariaephemeris/pull/7) **merged** at `fa8e5b7` after the required offline source validation and fast CI passed. This bounded prompt is **Done**, but its external reference acquisition is not numerical chart-comparison certification.

WP5.2 implementation, testing and merge were explicitly authorised by the owner on 19 November 2026; [PR #9 merged](https://github.com/DioneGate/ariaephemeris/pull/9) at `6216f15`. This bounded comparison is **Done** and measured all 300 frozen fixtures, but it **does not certify source-model physical accuracy**.

The owner requested quantitative source-model reconciliation on 19 November 2026 and subsequently **merged PR #11** at `0b5d6d6`. RM-001/006 is **Done for the bounded source attribution**, not an absolute accuracy qualification or a change of DE442s model. The owner then requested implementation of WP5.4; [PR #12](https://github.com/DioneGate/ariaephemeris/pull/12) is **In review**, and no merge or release was authorised for this later package.

Create subsequent rows only for concrete prompts at the owner's request. Do not
create numbered placeholder files.

## Next action

- Review [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3) and the [P1 compatibility matrix](../p1-capability-matrix.md), [contract](../p1-calculation-contract.md), [decisions](../p1-launch-scope-and-decisions.md) and [baseline](../p1-qualification-baseline.md).
- Obtain the required D01–D14 decisions and real-kernel replay; no numerical result beyond historical evidence has been reproduced in this increment.
- Parent phase RM-001-P1 stays Planned. A prompt is **Done only after evidence acceptance and verified merge**; a phase is Done only when its entire gate is met.
- RM-001/002 source evidence and RM-001/003 production profile have merged as PRs #5/#6. Review WP5.1's immutable Horizons source evidence on PR #7, then implement a **separately scoped WP5.2 numerical comparator** with explicit model/convention mismatch handling. No commercial release or Aria Galaxy deployment is implied.

Number subsequent prompts consecutively across the roadmap, not separately per
phase. Link each generated prompt to its phase, source baseline and dependencies.
Use the [framework statuses](../../README.md#status-and-evidence). Keep delivery
In review until merge is verified; a generated prompt alone never completes a phase.
