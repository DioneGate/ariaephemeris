# Aria Ephemeris

**Product and technical specification · Version 0.1 · 10 October 2026**

Aria Ephemeris is a planned proprietary calculation engine for an astrology suite. It will provide planetary positions, chart angles, houses, calculated points and astronomical event searches using independently developed Aria code and commercially usable astronomical data.

The objective is to support a closed-source commercial product without a Swiss Ephemeris professional licence or a dependency requiring publication of Aria source code. Permissively licensed components may be used where their terms allow this.

**Status:** specification only. No engine, datasets, packages or API described below have been implemented or validated yet. Accuracy, performance and size figures are acceptance targets unless explicitly identified as published source-file characteristics.

## 1. Product decisions

| Area | Decision |
| --- | --- |
| Ownership | Aria implementation is intended to remain proprietary |
| Astronomical foundation | Official JPL Development Ephemeris trajectories, initially DE442 |
| Baseline dataset | Official `de442s.bsp`; approximately 32 MB |
| Initial supported interval | 1900-01-01 through 2100-12-31, with sufficient source padding for corrections |
| Core default | Apparent geocentric tropical ecliptic positions referred to the true equinox/ecliptic of date |
| First delivery | Python package and a backend integration for the astrology suite |
| Reference implementation | Full-precision JPL evaluation; precision reduction is optional |
| Compact delivery | Independently generated Aria coefficient packs, released only after qualification |
| Runtime connectivity | Calculations run locally; no live JPL query required |
| Public claims | Publish only coverage and accuracy demonstrated by release evidence |

"Own ephemeris" means an Aria engine and, optionally, an Aria representation of JPL trajectories. It does not mean claiming ownership of JPL data or initially developing a new gravitational integration and observational orbit-fitting programme.

Repository visibility and software licensing are separate. A public repository exposes its contents even without an open-source licence. Keep proprietary implementation and build artefacts in a private repository if confidentiality is required. The current scaffold includes an MIT `LICENSE`. This README does not override that licence. Replace it with the chosen proprietary terms before adding proprietary implementation; rights already granted for earlier published material are not retroactively revoked.

## 2. Scope and phased capabilities

### 2.1 Initial release

- Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune and Pluto.
- Earth as an internal reference and optional heliocentric output body.
- Ecliptic longitude, latitude and distance; equatorial right ascension and declination.
- Geometric and apparent position modes, with explicit frame and correction metadata.
- Angular rates and retrograde status, including a configurable stationary band.
- Geocentric charts and an explicitly selected topocentric mode.
- ASC, DSC, MC and IC.
- Equal houses and whole-sign houses.
- Configurable aspect angles and orbs; applying/separating classification with an indeterminate state.
- Batch positions suitable for activation curves and transit timelines.
- Sign ingress, aspect perfection, conjunction/opposition and longitude-station searches.

### 2.2 Subsequent releases

| Capability | Prerequisite |
| --- | --- |
| Mean lunar nodes | Versioned mean-node model, published equations and validated conventions |
| Osculating lunar nodes | Geometric lunar state vectors, consistent frame and documented definition |
| Mean/osculating lunar apogee | Explicit model; definitions and differences documented |
| Chiron, Ceres, Pallas, Juno and Vesta | Separately acquired and qualified small-body datasets |
| Vertex and Part of Fortune | Versioned formulas, angle conventions and day/night policy |
| Sidereal charts | Named and versioned ayanamsa models with source references |
| Placidus, Koch, Porphyry, Regiomontanus and Campanus | Independently implemented algorithms and high-latitude qualification |
| Solar/lunar returns and lunations | Qualified event solver and correction conventions |
| Solar/lunar eclipses | Additional geometry, Earth orientation and shadow/contact modelling |
| Historical extension | Wider JPL kernel, time-model qualification and calendar policy |
| Browser/offline package | Qualified compact packs and an equivalent runtime evaluator |

A lunar node is a calculated orbital point, not a JPL body. "True node" must not be treated as a universal definition: the release must name the implemented convention. Compatibility with another astrology application's convention is a separate validation task.

Eclipse markers must not be inferred merely from a longitude conjunction or opposition. Eclipse detection and contact times have separate acceptance criteria.

### 2.3 Outside initial scope

- New numerical integration of the solar system or independent fitting of observations.
- Spacecraft navigation, occultation-grade predictions or scientific mission certification.
- Astrological interpretation, user accounts, billing and horoscope-wheel rendering.
- Fixed-star catalogues and star astrometry.
- Guaranteed reproduction of every Swiss Ephemeris setting or numerical result.
- Silent extrapolation outside qualified dataset coverage.

## 3. Data sources and provenance

### 3.1 Baseline JPL data

Download `de442s.bsp` from the [official NAIF planetary-kernel directory](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/). Its documented coverage is 26 December 1849 to 22 January 2150 TDB.

DE442 updates DE440 using additional observations, including Uranus occultations. The short kernel limits coverage; it is not an intentionally low-precision planetary model. See the [DE442 technical comments](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de442_tech-comments.txt) and [short-kernel extraction definition](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de442s.mrg).

DE440 may be supported as a separately identified compatibility dataset. DE441 is a possible long-range extension. Switching models must create a new dataset identity; existing charts must remain reproducible.

Standard planetary kernels include several planetary-system barycentres rather than all planet centres. Output must identify the actual target. A centre/barycentre substitution requires a measured error budget and an explicit policy; it must never be hidden behind a generic planet label in numerical metadata.

### 3.2 Additional inputs

- Leap-second table for UTC/TAI conversion.
- Earth orientation parameters, including UT1-UTC and polar motion, where needed.
- A versioned delta-T model for dates without adequate Earth-orientation observations.
- Frame constants and precession/nutation models.
- Optional planet-centre or small-body kernels.
- Timezone database for civil birth-time conversion in the application adapter.

[JPL Horizons](https://ssd.jpl.nasa.gov/horizons/manual.html) can generate small-body SPK files. Its documented generation interval is 1600-2500. Each body has its own orbit solution, usable interval and uncertainty; planetary precision targets must not automatically be assigned to asteroids.

### 3.3 Dataset manifest

Every source and derived pack must record:

- Stable dataset ID, semantic version, source model and target/centre IDs.
- Official download URL, acquisition date, SHA-256 hash and archived source comments.
- Reference frame, units, time scale and actual coverage for each segment.
- Runtime-qualified interval, including correction and event-search padding.
- Source usage terms, their recorded version/date and redistribution conditions.
- Builder version, configuration, numeric encoding and build inputs.
- Validation report, measured maxima, sampling policy and known limitations.
- Optional uncertainty information, clearly distinguished from compression error.

Original kernels are immutable. Dataset acquisition occurs through an explicit build/update operation. Runtime requests must not download data or change model versions automatically.

## 4. Licensing and proprietary boundaries

The implementation must use original Aria code or dependencies whose exact licences permit the intended closed-source deployment and distribution. This requirement applies to transitive dependencies, generators and redistributed data, not only the top-level package.

[NAIF's published rules](https://naif.jpl.nasa.gov/naif/rules.html) allow commercial use of SPICE components without fees and permit kernel redistribution. Modified kernels require changed filenames, suitable metadata and updated producer attribution. Retain JPL provenance separately; never present an Aria-derived pack as an official JPL release. Toolkit redistribution has additional rules that must be observed if included.

| Component | Policy |
| --- | --- |
| Original Aria source | Proprietary; no open-source grant intended |
| Official JPL/NAIF kernels | Preserve source identity and comply with the relevant usage terms |
| Aria-derived packs | Record producer, provenance and applicable upstream terms |
| NumPy and other numerical dependencies | Pin versions and retain applicable notices |
| `jplephem` / Skyfield | MIT-licensed candidates for bootstrap or validation; retain required notices |
| ERFA / PyERFA | Candidates for standards-based transformations; review both licences and distribution notices |
| CSPICE | Optional independent validator or selected implementation component under NAIF's specific terms |
| Swiss Ephemeris code, wrappers and `.se1` data | Excluded from Aria implementation and dataset generation |

Using raw JPL files with Swiss Ephemeris does not remove Swiss Ephemeris licensing obligations. Do not copy or translate Swiss implementation code into Aria. Implement mathematics from independently documented sources and keep algorithm provenance.

Required before distributing an implementation: a proprietary `LICENSE`, `THIRD_PARTY_NOTICES`, dependency inventory and data-source manifest. This README expresses product intent; it is not a complete software licence. A proprietary licence must not purport to override third-party rights.

Relevant candidate terms: [Skyfield MIT licence](https://github.com/skyfielders/python-skyfield/blob/master/LICENSE), [jplephem MIT licence](https://github.com/brandon-rhodes/python-jplephem/blob/master/LICENSE.txt), and [ERFA licence](https://github.com/liberfa/erfa/blob/master/LICENSE).

## 5. Architecture and implementation strategy

Keep astronomy, astrology and delivery adapters separate:

| Module | Responsibility |
| --- | --- |
| `time` | Julian dates, UTC/TAI/TT/TDB/UT1, calendars and time-model quality |
| `sources` | Read source kernels and resolve target/centre segment chains |
| `numerics` | Polynomial evaluation, derivatives, interpolation and root solving |
| `frames` | Coordinate transformations and precession/nutation |
| `positions` | Geometric/apparent states, observer corrections and spherical outputs |
| `astrology` | Houses, angles, nodes, ayanamsas, points and aspects |
| `events` | Bracketed event searches with explicit conditioning and tolerances |
| `datasets` | Manifests, loading, validation and pack selection |
| `adapters` | Python API, CLI and optional HTTP integration |
| `builders` | Offline source acquisition and compact-pack generation |

Use Python and float64 for the first implementation, with NumPy for batched calculations. A permissive SPK reader can bootstrap the engine; an Aria-owned reader may replace it once equivalence is demonstrated. Standards routines may be reused under suitable licences rather than rewritten solely to avoid open-source dependencies.

If implementing the reader, support the SPK types used by the selected datasets, validate endian/layout information and honour segment precedence and fallback rules. Unsupported kernel types must fail explicitly. Type 2 stores position polynomials and derives velocity; Type 3 stores position and velocity polynomials. See the [SPK specification](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/spk.html).

Memory-map large packs where possible. Separate immutable dataset handles from request state. Cache numeric segments without caching personal chart details.

A Rust/native/WASM evaluator is a later portability option, not a first-release prerequisite. Any alternative runtime must pass the same fixtures and precision gates.

## 6. Numerical and time conventions

### 6.1 Time

- Accept an explicitly specified time scale. Low-level API supports two-part Julian dates in TT and TDB.
- Civil input requires an ISO timestamp with offset or a local date/time plus IANA timezone. Reject unresolved ambiguous and nonexistent local times.
- Use a documented proleptic Gregorian calendar by default; Julian-calendar input requires an explicit flag.
- Evaluate JPL trajectories in TDB. Treat TT, TDB, UTC and UT1 as distinct.
- Support leap-second-aware conversion; do not assume UTC has uniform 86,400-second days.
- Pre-UTC historical civil times require an explicit policy; never pretend modern UTC rules extend unchanged to 1900.
- Future UTC and UT1 conversion must expose assumptions and uncertainty. Offer strict mode requiring supplied values where necessary.
- House/angle calculations use Earth rotation based on UT1, not simply TT or TDB.
- Return time-model identity, observed/predicted/modelled status and applicable warnings.

A small interpolation error does not imply equivalent absolute accuracy when the input birth time or historical Earth rotation is uncertain.

### 6.2 Positions

Use IAU 2006 precession and IAU 2000A nutation as the initial standards profile, with matched Earth-rotation and sidereal-time routines. Document the ecliptic-plane definition and equinox rotation precisely; an API frame name alone is not a complete numerical convention.

Provide geometric and apparent modes explicitly. Apparent mode includes:

1. Resolve the observer and target states from the required segment chains.
2. Iterate light travel time with bounded convergence.
3. Apply the selected aberration and gravitational deflection model.
4. Transform to the selected equatorial/ecliptic frame.
5. Produce longitude, latitude, distance and derivatives using consistent conventions.

Topocentric mode uses a WGS84 observer location, elevation and Earth orientation. Atmospheric refraction is excluded from zodiac positions; it belongs to a separately selected horizon-output option.

Record every correction and model used. Allow ecliptic-of-J2000 and mean-of-date outputs separately from the default true-of-date frame. Default tropical longitude is measured from the equinox, not constellation boundaries.

Angular values are calculated at full precision. Round only in the presentation adapter. Normalise longitude to `[0, 360)`; calculate derivatives and event residuals on continuous/unwrapped quantities.

## 7. Astrology calculations

- Derive sign index and within-sign longitude from the selected tropical or sidereal longitude.
- Return ASC, DSC, MC and IC independently of the chosen house system.
- Equal houses start at the Ascendant; whole-sign house one starts at its sign boundary. MC is not forced to equal the tenth-house cusp.
- Name the house algorithm/version and return twelve cusps plus house membership rules.
- When a house system or chart angle is undefined, return an explicit error. A user-selected fallback is allowed only if reported.
- Define boundary inclusion and angle wrapping consistently.
- Implement aspects using configurable longitude separation, aspect angle and orb rules.
- Classify applying/separating from a documented continuous residual and its derivative; return indeterminate near exactness/stationary thresholds.
- Define retrograde status from longitude rate in the requested coordinate convention. A stationary band must not be confused with an exactly solved station.
- Lunar orbital points use geometric lunar states and independently sourced orbital formulas. Keep mean and osculating variants distinct.
- Every sidereal model must declare epoch, reference definition and precession convention.
- Part of Fortune requires explicit sect/day-night policy; do not choose an undocumented formula.

## 8. Accuracy and qualification targets

These targets describe implementation agreement and optional approximation error against a matched full-precision reference. They do not guarantee absolute celestial-position accuracy, certainty of birth times or agreement between different astronomical conventions.

| Quantity | Full-precision acceptance target | Compact-profile target |
| --- | --- | --- |
| Raw state position | At most 1 metre disagreement with independent evaluation of identical source segments | Per-body Cartesian bounds selected to meet angular limits |
| Raw state velocity | At most 1 mm/s disagreement with the same reference | Measured velocity bounds required |
| Apparent geocentric direction | At most 1 arcsecond against matched independent calculations | At most 5 arcseconds added error against Aria full precision |
| Longitude rate | At most 0.0001 degree/day against a matched derivative reference | At most 0.001 degree/day added error |
| Chart angles / qualified house cusps | At most 1 arcsecond against an independent, convention-matched calculation in well-conditioned cases | Same calculation gate; ephemeris compression is not a house-algorithm tolerance |
| Well-conditioned longitude events | At most 10 seconds against the full-precision reference | At most 60 seconds added event-time error |

Report maximum, percentile and RMS errors per body and quantity. A candidate fails if any qualified case exceeds its limit. Near-pole coordinates, degenerate houses and ill-conditioned events need separately documented validity domains.

Stations and tangential contacts require separate timing qualification because small position/rate errors can create large time errors. Return uncertainty or an ill-conditioned result instead of claiming a universal timing guarantee.

Small-body uncertainty must be reported separately from implementation residual. Do not claim a 1-arcsecond absolute asteroid accuracy merely because a kernel evaluator matches its source.

## 9. Optional compact Aria format

### 9.1 Design

Use a versioned binary format provisionally named `.ariaeph`, with a manifest and independently indexed body/time blocks. The format must include:

- Magic bytes, format version, endian marker and numeric encoding.
- Source model, dataset ID and content hash.
- Per-block target, centre, frame, units, time scale, interval and polynomial degree.
- Chebyshev coefficient arrays and all scales/offsets needed to decode them.
- Qualification evidence and supported interval in the associated manifest.
- Block integrity checks and bounded lengths/counts to prevent malformed-file reads.

Retain Cartesian trajectories where future topocentric, latitude, distance or alternate-frame calculations require them. A longitude-only pack is allowed only as a separately named restricted product.

### 9.2 Builder

1. Acquire and verify official sources.
2. Preserve float64 source evaluation as the baseline.
3. Fit candidates with body-specific intervals/degrees.
4. Reduce coefficients or quantise residuals only with measured error checks.
5. Validate after decoding, including derivatives and block boundaries.
6. Refine failing blocks or retain full-precision coefficients.
7. Produce a deterministic pack and validation report.

Preserve correction padding and reference-body dependencies. Never extrapolate to fill missing intervals. Quantisation must be tested after all transformations, not only in coefficient space.

A sampled validation report establishes observed error, not a mathematical proof between samples. Use dense/adaptive off-grid sampling and adversarial cases; record whether a bound is empirical or analytically established.

### 9.3 Size policy

The official short kernel is already approximately 32 MB. Date restriction and removal of unnecessary segments are the first optimisation options.

A compact modern planetary pack below 10 MB is a design objective, not a guaranteed result. Retain a larger pack if required to satisfy accuracy. Small-body data is sized and versioned separately.

For scale only, ten trajectories with three coordinates, twelve 32-bit coefficients per coordinate and four-day blocks over 300 years occupy about 4 MB before indexing and metadata. This arithmetic does not demonstrate that those parameters satisfy the acceptance targets.

## 10. Proposed API contract

The following is a target contract, not an available endpoint.

| Operation | Purpose |
| --- | --- |
| `positions(request)` | One or many bodies at one instant |
| `positions_batch(request)` | Ordered series for curves and timelines |
| `chart(request)` | Positions, angles, selected houses and calculated points |
| `aspects(request)` | Configured aspects and their status |
| `find_events(request)` | Qualified events within a bounded interval |
| `dataset_info(id)` | Coverage, source, capabilities and qualification metadata |

Example request:

```json
{
  "time": {"value": "2000-01-01T12:00:00Z", "scale": "UTC"},
  "bodies": ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"],
  "origin": "geocentric",
  "frame": "true_ecliptic_of_date",
  "position_mode": "apparent",
  "zodiac": {"type": "tropical"},
  "dataset_id": "aria-de442-reference-v1",
  "profile": "reference",
  "strict": true
}
```

Each result must include engine version, dataset ID/hash, conventions, resolved time scales and time-quality metadata. Body entries contain target/centre identity, longitude/latitude in degrees, distance in AU, longitude rate in degrees/day and motion status. Equatorial output uses right ascension and declination in degrees; adapters may convert right ascension to hours. Display glyphs and minute rounding belong to the consuming app.

Chart requests add observer latitude/longitude/elevation, house system and selected points. Event requests add a finite interval, event type, residual definition and tolerance. Results report event time, solver convergence, profile, timing qualification and warnings.

Use stable machine-readable errors, including `OUT_OF_RANGE`, `UNSUPPORTED_BODY`, `UNSUPPORTED_FRAME`, `TIME_DATA_UNAVAILABLE`, `AMBIGUOUS_LOCAL_TIME`, `HOUSE_UNDEFINED`, `ILL_CONDITIONED_EVENT`, `NON_CONVERGENCE` and `DATA_INTEGRITY_ERROR`.

HTTP delivery is optional and wraps the same library contracts. Apply request limits and cancellation to large batch/event searches. A natal chart must not be sent to JPL during normal calculation.

## 11. Validation plan

Use independent implementations, not only Aria tests against Aria-generated fixtures:

- Compare raw states against CSPICE or another independently implemented evaluator with the identical kernel.
- Compare transformed coordinates against Skyfield or equivalent standards-based calculations with matched time scales, target centres, frames and corrections.
- Cross-check selected cases against Horizons and archive the full query, model identity and output.
- Compare compact packs against the qualified Aria reference at fitting-independent epochs.
- Validate houses and calculated points against independent documented formulas and reference cases.

Cover every body across the qualified interval with fixed-grid and seeded random epochs. Concentrate additional cases around lunar perigee, conjunctions, stations, sign boundaries, eclipses, leap seconds, segment boundaries and dataset endpoints.

Test timezone ambiguity, historical time policies, future assumptions, hemisphere changes, high latitudes, angle wrapping, malformed packs and missing dependencies. Compare derivatives both analytically and through an independent numerical check. Verify event completeness as well as timing; a solver that misses events fails even if its returned events are accurate.

Validation must separate source-model differences, coordinate-convention differences, time-model uncertainty and implementation error. Horizons is a cross-check rather than a universal identical-model oracle.

## 12. Operational and release requirements

- Pin engine, data, time tables and dependency versions for reproducible charts.
- Version code, source models and compact packs independently.
- Run calculations without network access after datasets are installed.
- Read-only dataset handles must support concurrent requests safely.
- Preserve cancellation, bounded search windows and explicit convergence limits.
- Log numerical diagnostics without birth details or other personal data.
- Benchmark on a named CPU/environment; report cold/warm latency, throughput and memory separately.
- Provisional warm targets: under 100 ms for a ten-body positions request and under 2 seconds for 10,000 ten-body geocentric epochs. Revisit after a baseline measurement.
- Publish no executable installation commands or production badges until they work.

Each release must include measured qualification reports, checksums, notices, dependency inventory and a reproducibility manifest. No compact pack may be labelled qualified solely because its generator completed successfully.

## 13. Suggested repository layout

This is a planned structure; the current repository contains a README and an MIT licence, with no engine implementation.

```text
src/ariaephemeris/
  time/
  sources/
  numerics/
  frames/
  positions/
  astrology/
  events/
  datasets/
  adapters/
builders/
tests/
  reference/
  regression/
  properties/
docs/
  algorithms/
  conventions/
  data-sources/
  validation/
data/
  manifests/
benchmarks/
LICENSE
THIRD_PARTY_NOTICES
pyproject.toml
README.md
```

Large source kernels and generated packs belong in a versioned artefact store or controlled release distribution rather than ordinary Git history. Manifests and retrieval/build definitions belong in the repository.

## 14. Delivery milestones and exit gates

| Milestone | Deliverable | Exit gate |
| --- | --- | --- |
| M0: Foundations | Licence inventory, frozen conventions, source/time manifests | Dependencies and sources meet proprietary deployment requirements |
| M1: Reference positions | JPL evaluator, time conversions, coordinate modes and batch API | Raw-state and apparent-position accuracy gates pass |
| M2: Initial charts | Angles, equal/whole-sign houses, aspects and topocentric mode | Independent chart validation and explicit edge-case handling pass |
| M3: Events | Ingress, aspects and stations | Completeness, timing and conditioning qualification pass |
| M4: Extended points | Nodes, apogee variants, minor bodies and selected house systems | Each feature has definitions, source terms and its own validation evidence |
| M5: Compact packs | Builder, format, decoder and optional browser evaluator | Decoded positions, rates and event timing meet compact-profile gates |
| M6: Product integration | Versioned package/API integrated into the astrology suite | Reproducibility, performance and distribution requirements pass |

M1-M3 can support an initial commercial astrology product without M5. Compression must not delay a working full-precision engine.

## 15. Technical references

These references document data formats, astronomical conventions and usage terms; they are not evidence that Aria has been implemented.

- [JPL planetary and lunar ephemeris export information](https://ssd.jpl.nasa.gov/planets/eph_export.html)
- [Official NAIF planetary kernels](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/)
- [DE442 technical comments](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de442_tech-comments.txt)
- [NAIF usage and redistribution rules](https://naif.jpl.nasa.gov/naif/rules.html)
- [SPK format and evaluation specification](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/spk.html)
- [JPL Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html)
- [Skyfield position conventions](https://rhodesmill.org/skyfield/positions.html)
- [Skyfield coordinate frames](https://rhodesmill.org/skyfield/coordinates.html)
- [Skyfield time scales](https://rhodesmill.org/skyfield/time.html)
- [jplephem evaluator and extraction documentation](https://pypi.org/project/jplephem/)
- [ERFA standards routines and licence](https://github.com/liberfa/erfa)
- [IERS conventions](https://iers-conventions.obspm.fr/)

Algorithm documents must add exact publications, model versions, equations and reuse terms before implementing houses, lunar orbital points, ayanamsas or historical time models.
