# RM-001/011 — Reliable explicit civil-time input

| Field | Value |
| --- | --- |
| Roadmap | [RM-001](../README.md) |
| Phase | RM-001-P2 |
| Generated/reviewed | 2026-11-19 / 2026-11-20 |
| Baseline | main `e55c0ff68301c6ea0159258adf562ed7187bc398`, PR #15 merged |
| Authority | Owner requested implementation of 011; no merge or deployment requested |
| Dependencies | Existing TimeInput/ERFA resolver; pinned IERS leap table; D03/D04 commercial decisions remain open |

## Objective and expected behaviour

Make explicit local date/time conversion reproducible across hosts, provide an opt-in pre-1972 civil interpretation, and prevent uncertain birth times from producing precise chart angles. Preserve existing strict defaults and numerical profiles.

## Verified current state

`src/ariaephemeris/time/__init__.py` already resolves UTC, TT, TDB and UT1, rejects DST gaps/unresolved folds, and requires supplied Earth rotation in strict charts. Timezones currently depend on host TZPATH. Pre-1972 UTC is rejected. TimeInput has no uncertainty semantics. Equal/Whole Sign and ASC/MC already exist. PR #15 passed all final checks and merged at `e55c0ff`; its bounded model results do not quantify historical clock accuracy.

## Scope and exclusions

Change TimeInput, the time resolver, timezone resource loading, uncertain-time geometry/search guards, embedded request schemas, legal inventory, tests and time-policy documentation. Pin tzdata 2026.6 / IANA 2026f and every included TZif hash. Keep astronomical kernels, production application, public result shapes and default strict behaviour.

This bounded P2 increment does not ingest observed/predicted EOP, invent historical UTC, implement Julian-calendar input, geocode locations, establish birth-record accuracy, calculate uncertainty intervals, introduce house systems, or approve a commercial date promise. Controlled observed EOP ingestion remains a separate P2 work package; existing explicit DUT1/delta-T and polar-motion requirements remain.

## Requirements

1. Default `civil_policy="strict"`: pre-1972 UTC remains rejected. New `historical-ut1-v1` applies only to ISO civil input with scale UTC, after offset conversion in nominal years 1900–1971. Interpret the adjusted clock as approximate UT1, never as recorded UTC. Reject JD usage, other scales, DUT1 and leap notation with that policy.
2. In strict historical mode require caller delta-T (TT minus UT1, seconds). In non-strict mode retain the separately labelled Espenak/Meeus model. Historical clock/zone uncertainty remains unknown. Preserve second-level IANA or explicit offsets.
3. Load zones from verified tzdata resources with ZoneInfo.from_file, bypass host TZPATH/global cache. Reject unlisted resources, changed bytes and unexpected package versions. Updates require dependency/manifest changes and requalification; never download during calculation.
4. Accept `time_accuracy="specified"` (default), `approximate` or `unknown`; optional positive finite `uncertainty_seconds` is only a caller-supplied approximate-input bound. Require an explicit representative timestamp even for unknown time. Do not infer noon or zero uncertainty. Reject uncertain angles/houses/topocentric calculations and uncertain event boundaries until interval analysis exists. Geocentric positions retain warnings and the bound/unknown metadata without claiming propagated uncertainty.
5. Return calendar, effective scale, civil policy, selected offset/fold, timezone version/hash, leap identity/expiry, used DUT1/delta-T values and their user/model status. Unknown Earth-rotation uncertainty is null. User offsets must not be relabelled as observed EOP.
6. Preserve recorded fractional leap seconds, strict leap-table expiry, explicit future assumptions, DST gap/fold behaviour, engine coverage and source-model identity. Reject conflicting or ignored timezone/fold fields, date-only implicit midnight, malformed offsets/fields and nonfinite uncertainty.

## Compatibility and operations

New fields are optional and added to every embedded TimeInput schema. Results gain quality metadata; result layouts and default astronomy remain unchanged. Timezone results intentionally identify the versioned source rather than relying on mutable OS data. Redundant offset+zone input now fails explicitly instead of ignoring the zone. `specified` means use the timestamp as supplied, not a physical assertion of exact birth-record accuracy. Rollback: previous package, requests and pinned environments; new optional policies require this implementation.

## Acceptance criteria

- Pinned timezone output is independent of host TZPATH and caches; all 598 resource hashes verify.
- Historical local input yields the same TT/UT1 and real-kernel chart as its explicitly declared UT1 equivalent.
- SOFA's published UTC-to-TT example, leap fractions/expiry, full-day/half-hour gaps, folds, historical second offsets, bad resource identities and uncertainty guards pass.
- Existing scalar/batch, chart/CLI, schema, source and numerical regression checks pass. Real-kernel or source skips do not count as qualified cases.
- Docs distinguish bounded implementation delivery, original 009 failures and 010 refinements, remaining P2 work and D03/D04 product decisions.

## Validation

Run Ruff/format, mypy, source/licence audit, non-kernel pytest, full DE442s pytest, existing qualification plus oppositions, build and clean wheel/sdist smoke. Use published SOFA and CPython examples and independently specified civil offsets as semantic references; compare historical charts against the explicit UT1 route for algebraic equivalence. This does not independently measure historical clock accuracy. See [time policies](../../../time-policies.md) for references and operational rules.

## Delivery record

Branch `feature/rm-001-011-civil-time`. Prompt stays In review until acceptance and verified merge; P2 remains In progress with controlled EOP ingestion, interval analysis and commercial decisions outstanding. Record executed results and PR evidence in [progress](../progress.md). No release or deployment is authorised.
