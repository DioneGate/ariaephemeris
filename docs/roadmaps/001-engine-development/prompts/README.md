# RM-001 — Implementation prompt register

[Roadmap](../README.md) · [Progress and evidence](../progress.md) ·
[Prompt template](../../templates/implementation-prompt.md)

RM-001/001 was separately authorised for execution on 18 November 2026. Four
source/contract/evidence documents have been delivered on [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3), **merged into main** at `df96380`. Prompt status is **In review**; owner scope decisions and a real-kernel replay are outstanding. The **parent RM-001-P1 phase and P2–P8 remain Planned**.

## Register

| Prompt ID | File | Phase | Status | Dependencies/blocker | Implementation evidence |
| --- | --- | --- | --- | --- | --- |
| RM-001/001 | [Commercial calculation contract, capability inventory and reproducible baseline](001-commercial-calculation-contract-and-baseline.md) | RM-001-P1 | **In review** | D01 direction selected; D02–D14 remain open; current host has no clone/kernel/pinned deps, so numerical replay blocked | Four [P1 deliverables](../README.md#rm-001001-execution-deliverables-reviewable-not-phase-acceptance) merged via [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3), docs only; source read-back passed; **real-kernel tests not run** |
| RM-001/002 | [Physical planet-centre source feasibility](002-physical-planet-centres-source-feasibility.md) | RM-001-P1 / RM-001-P3 prerequisite | **In review** (six source/evaluator gates passed) | Source binary, coverage, SHA-256 and CSPICE pass for all six; compact source-pack/redistribution and production accuracy gates remain open | [Jupiter evidence](../p1-jupiter-centre-qualification.md), [five-source evidence](../p1-five-centres-qualification.md), [PR #5](https://github.com/DioneGate/ariaephemeris/pull/5) draft, unmerged |

| RM-001/003 | [Versioned physical-centre multi-kernel engine profile](003-versioned-physical-centre-engine-profile.md) | RM-001-P3 (D01) | **In review** | Six SPK source identity/coverage and CSPICE evaluator gates passed in WP1–WP3; new full-six integration and independent chart/release gates pending | [Draft PR #6](https://github.com/DioneGate/ariaephemeris/pull/6), opt-in resolver/profile, source manifest, geometric/apparent tests and six-in-one workflow; no merge or deployment |

RM-001/002 was explicitly started by the owner on 2026-11-18. Jupiter WP1/WP2 and the five other WP3 sources now have SHA-pinned binary integrity, direct SPK coverage and independent **same-source** CSPICE evaluator evidence, captured in draft [PR #5](https://github.com/DioneGate/ariaephemeris/pull/5). The source feasibility gate is **In review**, not a claim of commercial model accuracy or complete roadmap phase; compact packing and release qualification remain open. No merge or release is authorised.

WP4 runtime implementation was explicitly authorised by the owner on 19 November 2026. RM-001/003 tracks that work, with no change to existing `reference` defaults and no deployment authority.

Create subsequent rows only for concrete prompts at the owner's request. Do not
create numbered placeholder files.

## Next action

- Review [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3) and the [P1 compatibility matrix](../p1-capability-matrix.md), [contract](../p1-calculation-contract.md), [decisions](../p1-launch-scope-and-decisions.md) and [baseline](../p1-qualification-baseline.md).
- Obtain the required D01–D14 decisions and real-kernel replay; no numerical result beyond historical evidence has been reproduced in this increment.
- Parent phase RM-001-P1 stays Planned. A prompt is **Done only after evidence acceptance and verified merge**; a phase is Done only when its entire gate is met.
- For RM-001/002, review the [six-source evidence](../p1-centre-source-feasibility.md) and [WP3 qualification](../p1-five-centres-qualification.md), and separately authorise a production multi-kernel resolver/profile increment. Neither PR #5 nor this register authorises merge, release or deployment.

Number subsequent prompts consecutively across the roadmap, not separately per
phase. Link each generated prompt to its phase, source baseline and dependencies.
Use the [framework statuses](../../README.md#status-and-evidence). Keep delivery
In review until merge is verified; a generated prompt alone never completes a phase.
