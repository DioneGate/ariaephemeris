# Development roadmaps

Versioned delivery plans for Aria Ephemeris initiatives spanning several bounded
implementation prompts. Keep these records in Markdown alongside the code.

## Roadmap register

| ID | Roadmap | Progress and evidence | Current focus |
| --- | --- | --- | --- |
| RM-001 | [Engine development and commercial application readiness](001-engine-development/README.md) | [Progress](001-engine-development/progress.md) | All eight phases Planned. Generate the first P1 prompt only when requested. |

This register is for discovery. Each roadmap's README owns phase status; its
progress log owns implementation evidence; its prompt register owns prompt status.

## Organisation

| Location | Responsibility |
| --- | --- |
| `docs/roadmaps/README.md` | Register, identifiers and working conventions |
| `docs/roadmaps/NNN-short-name/README.md` | Outcomes, phases, dependencies, acceptance gates, decisions and current phase status |
| `docs/roadmaps/NNN-short-name/progress.md` | Dated baseline, delivery evidence and remaining gaps |
| `docs/roadmaps/NNN-short-name/prompts/README.md` | Generated prompt register, dependencies and implementation evidence |
| `docs/roadmaps/NNN-short-name/prompts/NNN-short-name.md` | One bounded implementation prompt, created when requested |
| `docs/roadmaps/templates/` | Reusable roadmap, progress and prompt templates |

IDs are repository-scoped and stable: RM-001, RM-002, etc. Phase IDs append
-P1, -P2, etc. Prompt numbering restarts per roadmap, not per phase:
RM-001/001, RM-001/002, and so on. Every prompt records its phase.
Never renumber delivered work. Include repository context when referring to
similarly numbered roadmaps in another project.

## Status and evidence

| Status | Meaning |
| --- | --- |
| Planned | Scope recorded; implementation has not started |
| Ready | A generated prompt is actionable; required decisions and dependencies are resolved |
| In progress | Implementation underway; include branch or PR evidence when available |
| Blocked | Work cannot proceed; state the blocker and next action |
| In review | Implementation and validation available for review; not yet merged |
| Done | Acceptance verified and delivery merged into the target branch |
| Deferred | Intentionally postponed; record why and when to revisit |

Writing a roadmap or generating a prompt does not complete a feature.
A phase is Done only when all required work and phase acceptance criteria are
verified. Keep source implementation, tests, sampled qualification, merge and
deployment evidence distinct. Missing kernel data or skipped tests are not passes.
Avoid unsupported completion percentages, dates and numerical accuracy claims.

## Working cycle

1. Create a roadmap from the [roadmap template](templates/roadmap.md), add a
   [progress log](templates/progress.md) and prompt register, and register it here.
2. Inspect current main and record a dated baseline with source and evidence links.
   Distinguish reusable implemented foundations from the work still required.
3. When the owner requests the next increment, resolve the relevant decisions and
   generate a small prompt from the [prompt template](templates/implementation-prompt.md).
   Save it in that roadmap's prompts folder and register it.
4. Recheck the prompt baseline, source, dependency status and session authority
   before implementation. Preserve newer changes and unrelated work.
5. Record actual commands, results, qualification scope, remaining gaps and branch/
   PR evidence during delivery. Use In review until merge is verified.
6. Only then mark the prompt Done; update the parent phase only when its complete
   acceptance gate is satisfied. Record deployed-version evidence separately.

Prompt generation, implementation, merge, package publication and deployment are
separate actions. Recording a roadmap does not authorise those later actions.
Do not generate all future prompts automatically or create placeholder prompt files.

## Existing documentation

The [specification](../specification.md), [architecture](../architecture.md),
[conventions](../conventions.md) and [validation records](../validation/README.md)
retain their existing responsibilities. Roadmaps describe intended changes and
link to those records; they do not rewrite current runtime behaviour.

The [original implementation prompt](../implementation-prompt.md) remains at its
existing path as historical project material. It is not RM-001/001 and does not
prove that any new roadmap phase is complete. Preserve upstream legal notices.
Keep new roadmap narratives focused on Aria's own outcomes and capabilities.
