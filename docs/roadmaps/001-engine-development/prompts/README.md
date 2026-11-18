# RM-001 — Implementation prompt register

[Roadmap](../README.md) · [Progress and evidence](../progress.md) ·
[Prompt template](../../templates/implementation-prompt.md)

RM-001/001 was separately authorised for execution on 18 November 2026. Four
source/contract/evidence documents have been delivered on [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3), **open and unmerged**. Prompt status is **In review**; owner scope decisions and a real-kernel replay are outstanding. The **parent RM-001-P1 phase and P2–P8 remain Planned**.

## Register

| Prompt ID | File | Phase | Status | Dependencies/blocker | Implementation evidence |
| --- | --- | --- | --- | --- | --- |
| RM-001/001 | [Commercial calculation contract, capability inventory and reproducible baseline](001-commercial-calculation-contract-and-baseline.md) | RM-001-P1 | **In review** | D01–D14 owner approvals open; current host has no clone/kernel/pinned deps, so numerical replay blocked | Four [P1 deliverables](../README.md#rm-001001-execution-deliverables-reviewable-not-phase-acceptance) on [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3), docs only; source read-back passed; **real-kernel tests not run** |
| RM-001/002 | [Physical planet-centre source feasibility](002-physical-planet-centres-source-feasibility.md) | RM-001-P1 / RM-001-P3 prerequisite | **Blocked** (evidence in draft PR) | Local JPL DNS unavailable; six binary segment SHA/coverage inspections and independent Jupiter comparison not run | [Source report](../p1-centre-source-feasibility.md), offline audit and synthetic tests on dedicated branch; not qualified for commercial use |

RM-001/002 was explicitly started by the owner on 2026-11-18. Source discovery and tooling are in review, but the task is **Blocked** until real SPK files and independent qualification are available. No merge or release is authorised.

Create subsequent rows only for concrete prompts at the owner's request. Do not
create numbered placeholder files.

## Next action

- Review [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3) and the [P1 compatibility matrix](../p1-capability-matrix.md), [contract](../p1-calculation-contract.md), [decisions](../p1-launch-scope-and-decisions.md) and [baseline](../p1-qualification-baseline.md).
- Obtain the required D01–D14 decisions and real-kernel replay; no numerical result beyond historical evidence has been reproduced in this increment.
- Parent phase RM-001-P1 stays Planned. A prompt is **Done only after evidence acceptance and verified merge**; a phase is Done only when its entire gate is met.
- For RM-001/002, execute the documented SPK audit and Jupiter reference comparison on a controlled runner; candidate discovery is not binary/source qualification. This PR does not authorise merge, release or deployment.

Number subsequent prompts consecutively across the roadmap, not separately per
phase. Link each generated prompt to its phase, source baseline and dependencies.
Use the [framework statuses](../../README.md#status-and-evidence). Keep delivery
In review until merge is verified; a generated prompt alone never completes a phase.
