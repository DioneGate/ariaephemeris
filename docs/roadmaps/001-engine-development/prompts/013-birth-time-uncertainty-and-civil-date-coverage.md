# RM-001/013 — Birth-time uncertainty and civil-date coverage

| Field | Value |
| --- | --- |
| Roadmap / phase | RM-001 / RM-001-P2 |
| Generated/reviewed | 2026-11-21 |
| Baseline | main e52d11af6d5a7ac64ffc30c9ae387bb5140e8170, PR #17 merged |
| Authority | Owner requested implementation, tests and merge |
| Dependencies | 011 civil policies and 012 managed EOP |

## Objective and expected behaviour

Offer explicit bounded geocentric planetary time-uncertainty sampling, with honest sampled
ranges and a calculation-specific civil-date coverage matrix for D03/D04 review.

## Verified current state

011 supports uncertainty metadata but evaluates one representative instant;
precise uncertain houses/angles/topocentric/events reject. 012 supplies managed
modern rotation but does not propagate intervals. PR #17 is merged, not In review.

## Scope and exclusions

Add Python/JSON CLI sampling through existing position algorithms. No new source,
planetary conventions, application changes, exact interval houses, continuous
bounds, commercial acceptance, publication or deployment.

## Requirements

Resolve local input once and sample a symmetric elapsed TT interval from a finite
positive approximate-time bound. Include centre/endpoints; limit interval to one
day on each side and 3–1001 odd samples. Preserve full target/profile/time/source
provenance. Summarise circular longitude offsets and signed rates as sampled
extrema, never physical or continuous bounds. Reject unbounded time, unsupported
origins, invalid budgets and any source/time coverage failure. Never bypass civil
policy edges via TT shifting. Retain precise-chart guards.

## Compatibility and operations

Additive API and CLI, offline with unchanged pinned sources and request defaults.
Caller explicitly chooses sampling resolution. No partial success or source
fallback. See [detailed contract](../../../birth-time-analysis.md).

## Acceptance criteria

- Scalar TT comparisons match each sampled position/rate.
- Circular wrap and leap elapsed-seconds semantics pass.
- UTC/historical/kernel boundaries, ambiguity, budgets and guards fail safely.
- Coverage matrix separates observed, supplied, modelled and unsupported cases;
  D03/D04 proposals remain proposals, P2 In progress.

## Validation

Run Ruff/format, mypy, audit, non-kernel and real-kernel pytest, baseline
qualification/oppositions, build and clean package smoke. Record actual results;
finite samples do not establish universal extrema or absolute physical accuracy.

## Delivery record

Branch feature/rm-001-013-birth-time-coverage. See progress and prompt register;
keep In review until verified merge, then record actual evidence.
