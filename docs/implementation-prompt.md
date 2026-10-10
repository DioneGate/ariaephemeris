# Aria Ephemeris implementation prompt

**Version 0.1 · 10 October 2026 · Proposed implementation plan**

Implement Aria Ephemeris in `DioneGate/ariaephemeris` according to the technical specification in `README.md` and the decisions below.

Deliver a working, independently validated Python library for planetary positions and the initial astrology features. Do not stop at directory scaffolding, mock outputs or unimplemented public methods. Mark subsequent features explicitly as planned. Do not implement the astrology application's UI, accounts, billing or interpretation engine here.

## 1. Product and licensing decisions

Build a commercially usable open-source calculation library that may be used by a closed-source astrology suite. This replaces the earlier proprietary-only library intention; it does not require the consuming suite to become open source.

Use the standard Apache License 2.0 for new Aria-owned implementation, with a NOTICE file identifying the project and original author. The existing repository currently uses MIT; this prompt proposes a prospective migration when implementation begins.

- Retrieve the unmodified authoritative Apache 2.0 licence text.
- Preserve the existing DioneGate copyright-holder identity.
- In NOTICE, identify Aria Ephemeris and Marek as its original project author; do not invent a surname or transfer copyright between the author and organisation.
- Include NOTICE and LICENSE in source and wheel distributions, and document consumer obligations.
- Add SPDX identifiers to new Aria source files.
- Record the licence change in the changelog. Earlier material already released under MIT retains its prior grant; preserve applicable notices in reused material.
- Keep third-party software notices and JPL data terms separate from the licence for Aria code.
- Do not add compulsory branding, advertising, backlinks or UI badges to the Apache licence.
- Explain that Apache attribution normally concerns redistributed copies and derivatives, rather than compulsory credit on every screen of a hosted service.
- Both Aria and third parties may sell software or services using the engine. Do not describe Apache licensing as exclusive commercial rights.
- Use permissive dependencies compatible with this policy. Inspect exact pinned and transitive dependency terms.
- Exclude Swiss Ephemeris code, wrappers and Astrodienst .se1 data from implementation and dataset generation.

Use this NOTICE content as the starting point, subject to preserving existing rights and necessary third-party notices:

> Aria Ephemeris  
> Copyright 2026 DioneGate  
> Original project author: Marek  
> https://github.com/DioneGate/ariaephemeris

Treat this as attribution, not an extra condition extending Apache 2.0. Record contributor credit in AUTHORS.md without implying ownership of their contributions.

## 2. Repository boundaries

Use one repository and one installable Python distribution initially. Keep module boundaries clear enough to extract components later without introducing several packages prematurely.

| Location | Contents |
| --- | --- |
| DioneGate/ariaephemeris | Public library, dataset tools, documentation, tests and examples |
| Separate application repository | Commercial astrology UI, interpretation, user data and service-specific business logic |
| Versioned artefact storage | Original kernels, generated packs and large qualification results |

Do not create or change the application repository or configure paid storage as part of this task. Provide local artefact paths and a storage interface. The engine must function offline after explicit dataset installation.

## 3. Target structure

Use Python's src layout. Create directories when they contain real implementation, documentation or test cases; do not populate future features with misleading stubs.

| Path | Responsibility |
| --- | --- |
| README.md | Product overview, current capabilities, installation, quick start and specification links |
| docs/specification.md | Preserved detailed technical specification from the current README |
| docs/implementation-prompt.md | This prompt and its version history |
| docs/architecture.md | Module dependencies and delivery boundaries |
| docs/conventions.md | Time, frames, units, body centres, corrections and astrology definitions |
| docs/licensing.md | Aria licence, attribution, third-party notices and data terms |
| docs/algorithms/ | Exact references and equations for implemented algorithms |
| docs/validation/ | Validation methodology and small release-summary reports |
| src/ariaephemeris/models.py | Typed requests, responses, enums and immutable state records |
| src/ariaephemeris/errors.py | Stable error codes and public exceptions |
| src/ariaephemeris/time/ | Civil time, Julian dates, TT/TDB/UTC/UT1 and quality metadata |
| src/ariaephemeris/sources/ | SPK reader adapter, segment chains and target resolution |
| src/ariaephemeris/numerics/ | Polynomial evaluation, derivatives and root solving |
| src/ariaephemeris/frames/ | Reference-frame and coordinate transformations |
| src/ariaephemeris/positions/ | Geometric/apparent observer-to-target calculations |
| src/ariaephemeris/astrology/ | Angles, houses, signs, aspects and later orbital points |
| src/ariaephemeris/events/ | Bounded and qualified event searches |
| src/ariaephemeris/datasets/ | Manifests, validation, installation and immutable loading |
| src/ariaephemeris/cli/ | Command-line entry point with thin adapters |
| tools/datasets/ | Explicit source acquisition, qualification and later pack builders |
| tests/unit/ | Independent mathematical and contract checks |
| tests/integration/ | Real-kernel and end-to-end library checks |
| tests/reference/ | Independent evaluator comparisons and provenance-bearing fixtures |
| tests/regression/ | Previously reproduced bugs and edge cases |
| tests/data/ | Tiny legally redistributable fixtures; no production kernels |
| benchmarks/ | Reproducible latency, throughput and memory measurements |
| examples/ | Working positions, chart, batch and event examples |
| data/manifests/ | Checked-in metadata, source hashes and source terms |
| schemas/ | Versioned JSON schemas for manifests and public serialisation |
| .github/workflows/ | Fast CI, kernel qualification and distribution checks |
| pyproject.toml | Package configuration, extras, tool configuration and entry points |
| LICENSE / NOTICE / THIRD_PARTY_NOTICES / AUTHORS.md | Licence, attribution and component notices |
| CONTRIBUTING.md / CHANGELOG.md | Contribution conventions and release history |

Exclude downloaded kernels, generated packs, full validation outputs, caches, private chart data and secrets from ordinary Git history. Use an ignored local artefact directory in development. Avoid committing machine-specific absolute paths.

## 4. Implementation order and technology

Use a supported Python version, float64 numerics and NumPy. Select one documented build backend, lint/type-check tooling and a reproducible dependency-lock approach.

An MIT-licensed jplephem adapter may bootstrap SPK evaluation. ERFA/PyERFA may supply standards transformations under their verified terms. Keep their public APIs behind Aria-owned adapters. Use Skyfield and, where practical, CSPICE as independent validation references rather than wrapping a Skyfield result and then treating it as independent validation of the same result.

Do not write a custom SPK reader merely to claim originality. Aria's own API, convention choices, astrology algorithms, dataset tooling and validation form the engine. A later reader replacement must pass the same reference suite.

Start with official de442s.bsp and preserve its precision. Qualify 1900-01-01 through 2100-12-31 with correction padding; distinguish coverage of the source from coverage of qualified Aria operations.

### Stage A: Package, licensing and real source evaluation

- Inspect existing files and repository instructions; preserve unrelated content.
- Move the detailed README specification to docs/specification.md and update its licensing language consistently.
- Create the installable library and CLI, legal documents, manifests and fast CI.
- Implement explicit dataset acquisition and installation with hashes, provenance and source terms.
- Never invent a checksum; acquire and record the real file's hash.
- Validate SPK segments, dependencies and per-target coverage.
- Provide dataset_info and raw geometric position/velocity evaluation at explicit TDB instants.
- Fail on unavailable bodies, unsupported kernels, corrupt data and out-of-range requests.

### Stage B: Time, frames and planetary positions

- Implement the time contracts in the specification, including two-part Julian dates.
- Reject unresolved timezone ambiguity and nonexistent local times.
- Support leap-second-aware conversions and expose historical/future model uncertainty.
- Strict mode must reject requests needing unavailable time data; distinguish prediction/model use from observations.
- Use IAU 2006 precession and IAU 2000A nutation, with documented Earth-rotation and ecliptic-plane conventions.
- Implement geometric and apparent modes, light-time convergence, aberration and selected gravitational deflection.
- Implement geocentric, heliocentric and explicitly selected topocentric outputs.
- Support Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune and Pluto.
- Expose actual target/centre IDs, including barycentre substitutions and their policy.
- Return degrees, AU, degrees/day and time-quality metadata as specified.
- Derive rates analytically where possible. Use finite differences as a cross-check, not an unexplained replacement.
- Provide positions and positions_batch, preserving order and scalar/batch agreement.

### Stage C: Initial chart calculations

- Implement ASC, DSC, MC and IC from explicitly resolved UT1 and observer location.
- Implement equal and whole-sign houses using independently documented formulas.
- Include geometric limits, high-latitude degeneracies and explicit errors.
- Implement signs, within-sign longitude, selected house membership and boundary rules.
- Implement configurable aspects with circular separation, orbs and documented applying/separating conventions.
- Implement retrograde classification with a reported stationary band.
- Provide chart and aspects operations using common typed models.
- Keep rounding and glyphs outside the numerical core.

### Stage D: Event searches

- Implement ingress, configured aspect perfection, conjunction/opposition and longitude stations.
- Search a bounded interval using adaptive bracketing, continuous residuals and a convergent root solver.
- Account for angle wrapping, retrograde recrossings, multiple events and endpoint inclusion.
- Test completeness; do not assume a coarse fixed grid finds every root.
- Handle grazing/tangential and poorly conditioned events explicitly.
- Return convergence, residual, time scale, dataset, profile and timing-quality information.
- Support cancellation and bounded work budgets.
- Provide find_events and a real CLI example.

Stages A-D form the initial deliverable. Complete them in order, with meaningful validation at each stage, rather than implementing disconnected pieces of every future feature.

## 5. Optional later stages

Prepare documented extension points, but do not claim these capabilities are available until implemented and independently qualified:

- Mean and osculating lunar nodes; distinct mean/osculating apogee variants.
- Named sidereal ayanamsas with versioned equations and reference epochs.
- Chiron, Ceres, Pallas, Juno and Vesta with their own source manifests and uncertainties.
- Vertex, Part of Fortune and additional house systems.
- Returns, lunations and eclipse geometry.
- Qualified compact Aria packs and a browser/native evaluator.

Develop compact packs only after the full-precision reference works. Use per-body Chebyshev refitting, explicit quantisation and independent decoding tests. Validate positions, derivatives and event times after decoding. Refine or retain precision for failing blocks.

A below-10-MB compact pack is a size objective, not an acceptance guarantee. A larger accurate pack is preferable to a small unqualified one. Maintain float64 calculations even when storage precision is reduced.

## 6. API, errors and reproducibility

Implement the specification's positions, positions_batch, chart, aspects, find_events and dataset_info contracts as Python methods. Add CLI serialisation; defer an HTTP server to an optional adapter.

Results must include:

- Engine version and exact dataset ID/hash.
- Requested and resolved origins, frames, corrections and zodiac settings.
- Body target/centre identity and units.
- Time-table/model versions and time quality.
- Coverage and warnings applicable to the calculation.
- Algorithm versions for houses, points and event searches.

Use stable error codes from the specification. Unsupported planned features must raise clear errors, never return approximate placeholders.

Normal calculations must not contact JPL or silently update data. Do not log birth details. Thread-safe dataset handles must be read-only, with request-local state.

## 7. Validation gates

All accuracy figures remain targets until measured. Distinguish source uncertainty, time uncertainty, algorithm disagreement and compression error.

| Gate | Required evidence |
| --- | --- |
| Raw source evaluation | Independent same-kernel agreement within 1 metre and 1 mm/s |
| Apparent geocentric direction | Within 1 arcsecond against convention-matched independent calculations |
| Longitude rate | Within 0.0001 degree/day against a matched derivative reference |
| Qualified angles/houses | Within 1 arcsecond in declared, well-conditioned cases |
| Well-conditioned events | Within 10 seconds against independently established reference events |
| Compact positions, if later implemented | No more than 5 arcseconds added directional error |
| Compact rates/events | Specification thresholds, separately tested around stations |

Use coordinate-vector comparisons near coordinate singularities and circular angular differences elsewhere. Do not compare quantities in different frames and call the difference implementation error.

Test all supported bodies with deterministic grids and seeded off-grid epochs across the qualified interval. Include source-segment boundaries, endpoints, lunar perigee, conjunctions, stations, 0/360-degree transitions, leap seconds, high latitudes and invalid inputs.

Reference fixtures must record kernel hash, evaluator version, time inputs, frame, correction settings and generation method. Never use Aria-generated expected outputs as the only correctness oracle.

Separate fast synthetic/unit checks from real-kernel qualification. Real-kernel CI must report explicit pass/fail/not-run status; it must not turn missing data or silently skipped reference checks into a successful qualification.

Empirical sampling does not prove a continuous maximum error bound. Describe the sampled domain and any analytic bounds honestly.

## 8. CI and packaging

Provide:

1. Fast PR CI for formatting/linting, type checks, meaningful unit tests and package build.
2. A real-kernel qualification workflow, run manually and before release, with verified source acquisition or checksum-keyed caching.
3. Source/wheel installation smoke checks verifying CLI examples and inclusion of LICENSE, NOTICE and applicable dependency notices.
4. Dependency/licence inventory and source-term checks.
5. Reproducible benchmark output identifying CPU, versions, dataset and cold/warm conditions.

Run kernel qualification for the full supported interval before labelling it qualified. Do not make public package publication, deployment, repository visibility changes or application integration writes automatic consequences of implementation.

## 9. Definition of done and final report

The initial deliverable is complete when:

- Stages A-D work with a real pinned JPL dataset.
- A clean environment can install the package and run every documented initial example.
- Library and CLI contracts agree, including metadata and error handling.
- Required independent accuracy, event-completeness and packaging checks pass.
- A machine-readable qualification report records measurements and coverage.
- Current capabilities and unimplemented extensions are accurately separated.
- No Swiss Ephemeris dependency or copied implementation is present.
- Licence migration, attribution and third-party/data terms are documented.
- Dataset/version pinning reproduces the same charts.
- Performance is measured without presenting provisional targets as achievements.

At completion, report implemented features, file changes, exact verification commands, measured maximum errors, benchmark results and any limits. If an external source is unavailable, complete independent work and report precisely which qualification remains blocked; do not fabricate results or describe an unqualified release as finished.

## 10. Primary references

- [Current detailed Aria specification](../README.md) (move it to docs/specification.md during Stage A and update this link)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- [MIT licence and retained earlier rights](https://opensource.org/license/mit)
- [NAIF data/software usage rules](https://naif.jpl.nasa.gov/naif/rules.html)
- [Official JPL/NAIF planetary kernels](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/)
- [SPK specification](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/spk.html)
- [Skyfield position conventions](https://rhodesmill.org/skyfield/positions.html)
- [Skyfield coordinate frames](https://rhodesmill.org/skyfield/coordinates.html)
- [Skyfield time scales](https://rhodesmill.org/skyfield/time.html)
- [ERFA and its licence](https://github.com/liberfa/erfa)
