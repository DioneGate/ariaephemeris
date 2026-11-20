# Civil-time policy, RM-001/011

Aria's astronomical time envelope and the accuracy/availability of a civil birth record are separate. All calendars here are proleptic Gregorian; converting Julian-calendar records is the caller's responsibility. Supply an explicit evaluation time. Date-only input does not silently become midnight or noon.

## Modern civil input

The default `civil_policy="strict"` preserves recorded UTC conversion from 1972 until the bundled IERS leap-table expiry (28 June 2027, exclusive). Leap seconds, including fractional notation, use the recorded table. Strict future UTC fails; `strict=False` retains the explicit no-additional-leaps assumption and warning. This is not a prediction of future UTC policy.

Use either an explicit numeric offset or a naive local timestamp plus an IANA key, not both. DST gaps are errors and repeated times require `fold=0` or `fold=1`. Transition sizes need not be one hour. Offset seconds are retained. Invalid/irrelevant folds fail explicitly.

IANA conversions use **tzdata 2026.6, IANA 2026f**, loaded directly from its TZif files. The packaged `resources/tzdata-v1.json` fixes all 598 allowed paths and SHA-256 values. Calculations bypass OS TZPATH and its ZoneInfo cache, verify the requested resource and report its identity and selected civil offset. The in-process cache assumes installed data is immutable. Installing a new package/zone release requires a reviewed manifest/dependency update, regression tests and a process restart; there is no background update or network lookup. Historical and predicted future zone rules are evidence of that version's rules, not a universal accuracy guarantee.

## Historical local clocks: explicit opt-in

Before 1972 the default continues to reject civil UTC. To evaluate an explicitly chosen approximation for 1900–1971, select `historical-ut1-v1`:

```python
from ariaephemeris import TimeInput

historical = TimeInput(
    value="1901-01-01T12:00:00",
    timezone="Europe/Paris",
    civil_policy="historical-ut1-v1",
    delta_t_seconds=0.0,  # Demonstration value only: supply justified TT−UT1 for your epoch.
)
```

The input's default `scale="UTC"` identifies the civil parser, but this policy **does not perform historical UTC conversion**. It removes the selected civil offset in nominal clock arithmetic and explicitly interprets the resulting Gregorian clock as **UT1**. Output labels the effective scale and assumption, returns no UTC epoch, and warns about unbounded historical clock/zone accuracy. UTC itself existed in part of this interval; this policy deliberately approximates nominal Greenwich civil time as UT1 rather than implementing the historical UTC rate/drift realisation. For researched records, prefer an explicit UT1 or TT epoch and independently justified delta-T. Local mean time is supported only through an explicit researched numeric offset, including seconds; longitude or zone identifiers do not automatically prove which local clock was used.

Strict historical input requires supplied `delta_t_seconds = TT−UT1`; with `strict=False`, missing delta-T uses the existing named Espenak/Meeus polynomial. Neither is observational truth merely because it is numerically convertible. This policy excludes DUT1, JD, leap-second notation, other scales and adjusted nominal dates outside 1900–1971. Actual engine TT coverage is still checked separately, so the exact lower boundary can fail after conversion.

## Earth rotation and data quality

Strict charts require supplied DUT1 with modern UTC or delta-T with TT/TDB/UT1. Strict topocentric calculations also require supplied polar motion. Missing inputs fail. Non-strict mode retains labelled polynomial delta-T and zero-polar-motion warnings. Results record the used rotation offsets and distinguish caller values from the named model; **caller values are not certified observed or predicted EOP**. Earth-rotation uncertainty stays null, never an invented zero.

RM-001/012 adds optional, explicitly installed [managed Earth orientation](managed-eop.md): pinned Bulletin A DUT1/polar motion, observed/predicted quality, leap-safe interpolation, prediction validity and immutable update policy. The supplied-value contract above remains valid and wins over managed fields. No runtime network resolver or automatic refresh is introduced. Historical coverage, uncertainty intervals and commercial acceptance remain separate.

## Unknown and approximate birth times

`time_accuracy="specified"` is the backwards-compatible default: use the supplied instant. It does not establish the physical accuracy of a birth record. `approximate` accepts an optional positive finite caller-provided `uncertainty_seconds`; a missing bound means unknown, not zero. `unknown` has no numeric bound. Both still require an explicit representative timestamp for planetary evaluation.

Geocentric/heliocentric positions at that representative instant retain the uncertainty and warn that it has not been propagated. They are not bounds for the whole possible interval. Angles, houses, topocentric positions and event-boundary requests reject uncertain times with a structured error. Interval calculations and application UX for unknown birth time remain future work; no precise house result is manufactured.

## Qualification and source references

Tests use the published SOFA example (2010-07-24 11:18:07.318 UTC = 11:19:13.502 TT), CPython's Los Angeles repeated-hour example, pinned civil-transition cases, exact historical offset arithmetic and actual DE442s chart/CLI comparisons with explicit UT1. These demonstrate implementation/semantic agreement, not physical historical time accuracy or worldwide birth-record coverage.

- [SOFA Time Scale and Calendar Tools](https://www.iausofa.org/2023-10-11c#documentation)
- [Python 3.12 zoneinfo](https://docs.python.org/3.12/library/zoneinfo.html)
- [IANA tz database scope and historical limitations](https://data.iana.org/time-zones/tzdb/theory.html)
- [NASA Espenak/Meeus delta-T polynomials](https://eclipse.gsfc.nasa.gov/SEcat5/deltatpoly.html)

D03 (commercial civil-date coverage) and D04 (uncertain-time product behaviour) remain open owner decisions. This opt-in implementation is not their commercial acceptance or a release.
