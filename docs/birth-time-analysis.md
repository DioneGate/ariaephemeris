# Birth-time uncertainty and civil-date coverage — RM-001/013

## Explicit interval analysis

`Ephemeris.birth_time_analysis(request, samples=9)` accepts an approximate
`TimeInput` with a finite positive `uncertainty_seconds`, up to 86,400 seconds.
The interval is symmetric about the explicitly supplied instant. Local civil
input is resolved once, including timezone and fold; the interval then measures
elapsed SI seconds in TT. It does not enumerate alternative DST folds or guess
the meaning of an unknown birth date/time. Supply 3–1001 odd, evenly spaced samples;
the centre and both endpoints are always included. Request limits bound work.

V1 supports geocentric requests without an observer only.

The additive API and CLI `birth-time-analysis` return full numerical provenance
for every sample and sampled longitude offsets relative to the centre, plus
sampled signed-rate minima/maxima. Relative circular offsets in [-180,180) avoid
turning an Aries crossing into a nearly full-circle range. These are circular
offsets at samples, not an unwrapped trajectory. Large intersample excursions,
stations, recrossings and extrema can be missed. No interpolation, probability,
continuous enclosure or physical uncertainty guarantee is claimed. The returned
`continuous_bounds` is false and `physical_uncertainty` is null.

Unknown time or approximate time without a finite bound is rejected. No default
noon or whole-day interval is invented. Angles, houses, aspects and topocentric
intervals are excluded; their existing uncertain-time guards remain in force.
A sampled response does not authorise precise houses on an uncertain chart.
Physical-profile selection and per-body source requirements remain unchanged.

All samples must pass the dataset envelope, and the complete interval must stay
inside the selected historical/strict UTC policy at both endpoints. The TT
shift must not bypass UTC leap expiry or pre-1972 restrictions. Existing
apparent-rate stencils and retarded-source coverage checks still apply. Any
failure aborts the analysis; no clipping, partial success or stale result.
Input-time metadata retains the original civil provenance. Sample TT/TDB epochs
are shifted instants, not fresh civil-time resolutions; supplied Earth rotation
is not re-estimated. Per-sample representative-time warnings remain appropriate:
samples are not individually certified birth instants or continuous bounds.
No managed EOP is needed for the supported geocentric planetary positions.

```python
from ariaephemeris import Ephemeris, PositionRequest, TimeInput

with Ephemeris(".artifacts/de442s.bsp") as engine:
    result = engine.birth_time_analysis(
        PositionRequest(
            TimeInput(
                value="2000-01-01T12:00:00Z", time_accuracy="approximate", uncertainty_seconds=900
            ),
            bodies=("sun", "moon"),
        )
    )
    print(result["ranges"])
```

## Coverage matrix (engineering support, not commercial approval)

All intervals intersect actual TT kernel coverage: 1900-01-01 inclusive to
2101-01-01 exclusive. Corrections/rate stencils additionally need source padding.
Timezone offsets can move a nominal civil date outside these limits.

| Input / operation | Available policy | Additional restrictions |
| --- | --- | --- |
| Strict UTC planetary positions | 1972-01-01 inclusive to 2027-06-28 exclusive | Pinned leap table; timezone gaps rejected and folds explicitly selected |
| Strict UTC angles/houses | Same UTC envelope | Supplied DUT1/delta-T or selected managed EOP; defined observer geometry |
| Managed EOP | Actual complete Bulletin A nodes from 1973; inspect selected snapshot | No gaps/extrapolation; observed by default; predictions opt-in before 2026-12-20; topocentric derivatives need their own supporting epochs |
| Historical civil 1900–1971 | Explicit historical-ut1-v1 | Offset-adjusted clock approximates UT1; strict requires supplied delta-T; clock/zone/rotation physical uncertainty unknown |
| Explicit TT/TDB positions | Kernel TT envelope | No invented civil conversion; physical-profile coverage remains source-specific |
| Explicit UT1 | Kernel TT envelope after conversion | Strict requires supplied delta-T; modelling only in explicit non-strict mode |
| Future non-strict UTC | Kernel TT envelope | Explicit no-additional-leaps assumption and warnings; not qualified future civil truth |
| Approximate bounded time | Planetary samples only | Whole interval passes selected policy; sampled ranges only |
| Unknown / unbounded time | Explicit representative planetary instant only | No interval bounds or precise houses/angles/topocentre/events |

## D03/D04 proposal and remaining gate

D03: propose the strict UTC window above for ordinary modern input, with
historical-ut1-v1 as a separately labelled research option. Do not advertise the
TT envelope as ordinary birth-date support. Modern 1972 entries still cannot
use managed observations absent in the 1973-onwards source; supplied rotation
remains necessary for their strict charts.

D04: retain precise-chart rejection for unknown/approximate input; offer the
explicit bounded planetary sampling API to research callers. Unknown time needs
caller-provided researched information before an interval can be analysed.
Neither this engineering implementation nor its merge approves commercial scope.
P2 remains In progress pending D03/D04 acceptance and broader historical/EOP
coverage qualification. Interval houses and certified continuous planetary
bounds require separately scoped algorithms and references.

Definitions reuse the existing ERFA TT conversions and Aria correction pipeline;
see [conventions](conventions.md), [civil-time policy](time-policies.md),
[managed EOP](managed-eop.md). Qualification compares samples with independently
requested scalar TT evaluations; that proves wrapper consistency, not physical
model accuracy. Tests include civil gaps/folds, historical boundaries, UTC expiry,
leap seconds, circular wrap, request limits and unchanged uncertain-chart guards.
