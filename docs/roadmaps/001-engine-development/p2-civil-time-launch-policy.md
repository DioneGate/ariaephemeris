# P2 civil-time launch policy and qualification

## D03 — Dates Aria Galaxy should offer

Use the strict UTC conversion policy for ordinary civil entry. Resolve the
user's local time against pinned timezone data or an explicit offset before
testing availability. Ask which occurrence they mean during a clock overlap
and reject a time that falls in a clock gap.

| Calculation | Launch policy | Verified behaviour with pinned inputs |
| --- | --- | --- |
| Geocentric planetary positions | Offer inside strict UTC coverage. | From 1972-01-01 00:00 UTC inclusive to 2027-06-28 00:00 UTC exclusive with the tested leap table. |
| Angles and houses with managed Earth orientation | Offer when the installed data provides observed UT1 for the resolved instant and the geometry is defined. | Snapshot starts at 1973-01-02 00:00 UTC. 2026-11-19 00:00 UTC passes. One second later requires a predicted interpolation endpoint. |
| Predicted Earth orientation | Keep explicit opt-in for specialist use. | With opt-in, 2026-12-19 23:59:59 UTC passes and 2026-12-20 00:00 UTC fails. |
| Pre-1972 civil input | Keep the historical UT1 approximation in the research workflow, with explicit assumptions and source quality. | Ordinary strict UTC rejects it. Existing historical tests exercise supplied delta-T and comparison with explicit UT1. |
| Topocentric positions | Qualify separately for any product that offers them. | Require polar motion and coverage for the shifted evaluation epochs as well as the requested instant. |

These dates apply to the reference profile and the tested source versions.
Qualify any additional target profile for its own source coverage. At launch,
derive availability from the active snapshots and check the actual request.
Use a controlled update process for leap-second, timezone and Earth-orientation
data. The November snapshot illustrates the immediate operational consequence:
observed-only houses for dates after its last observed node require a newer
qualified snapshot. If the active source cannot support houses, a qualifying
planetary preview remains available.

## D04 — Exact, approximate and unknown times

- **Exact** uses the supplied resolved instant. Show houses and angles only
  when rotation data and geometry support them.
- **Approximate with a bounded window** offers sampled geocentric planetary
  ranges. Label these as sampled ranges and omit precise angles and houses.
- **Approximate without a bound, or unknown** permits a planetary preview at
  an explicitly selected representative instant. Preserve the original time
  quality and label the preview's time. If no representative instant is
  supplied, leave the calculation unresolved. Omit precise angles and houses.

## Replay and acceptance

```sh
ARIA_KERNEL=.artifacts/de442s.bsp \
ARIA_CIVIL_EOP=.artifacts/eop/finals2000A.all \
pytest -q tests/integration/test_civil_launch_coverage.py \
  tests/integration/test_civil_time_pipeline.py tests/test_birth_time_analysis.py
```

The focused replay passed 37 tests on 23 November 2026. The engine checks hashes
for DE442 short and `iers-usno-finals2000a-20261120-v1` when opening them.
The tests qualify engine behaviour at representative inputs and transitions.
Before advertising coverage, Aria Galaxy needs a provider-level replay with
its deployed source snapshots and a verified data refresh procedure.

D03 and D04 are recorded here as the recommended launch defaults under the
instruction to proceed with RM-001/014. Commercial release approval and
broader historical or source qualification remain P2 follow-up items.
