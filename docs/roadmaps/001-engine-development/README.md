# RM-001 — Engine development and commercial application readiness

| Field | Value |
| --- | --- |
| Product owner | Marek / DioneGate |
| Last reviewed | 2026-11-18 (RM-001/001 prompt preparation; no phase implementation) |
| Inspected implementation baseline | [`39b25ae`](https://github.com/DioneGate/ariaephemeris/commit/39b25aec9023bcc79172a0f0cf7aed373efafc89), package 0.1.0 |
| Progress and evidence | [progress.md](progress.md) |
| Implementation prompts | [Prompt register](prompts/README.md) |
| Framework | [Roadmap register and conventions](../README.md) |
| Agent working rules | [Repository AGENTS.md](../../../AGENTS.md) |
| Current main checked | [`36a9cec`](https://github.com/DioneGate/ariaephemeris/commit/36a9cec742e8248fdee599b7cf620b2b19d12cc7), 2026-11-18 (RM-001/001 execution baseline; app main `4ab5f99`) |

## Outcome

Develop Aria Ephemeris into a dependable, independently maintained astronomical
calculation platform for the commercial Aria application. Prioritise trustworthy
everyday chart calculations and efficient activation timelines, then expand
techniques, historical coverage and deployment options. **The commercial milestone is the ability to run the agreed Aria Astrology offering using Aria Ephemeris as its sole declared astronomical provider, with reproducible numerical and application evidence.**

This roadmap preserves the standalone development plan prepared on 20 October 2026 and formalises the commercial integration and performance decision gates on 15 November 2026. It does not start numerical implementation, generate a phase prompt, authorise changes in the application repository, a merge, package release or production deployment.

## Scope and boundaries

- Develop the engine's contracts, time handling, chart capabilities, integration
  boundary, performance, qualification and release process.
- Reuse the existing application contracts and preserve their numerical semantics.
- Accounts, payments, entitlements and personal chart storage remain application
  responsibilities. This roadmap does not authorise changes in the application repository.
- First paid use need not await all long-range or specialist work. Resolve the
  advertised calculation scope before treating optional capabilities as release blockers.
- Existing 0.1.0 features are reusable foundations, not completion of these phases.
- Keep Python as the baseline and scientific validation implementation; investigate Rust only through measured, qualified proof-of-concept work, not as an assumed launch dependency.
- **MVP commercial release:** P1–P6 gates apply only to the explicitly selected launch scope. P7–P8 remain optional unless a requirement makes them mandatory.
- All eight phases below are Planned. [RM-001/001](prompts/001-commercial-calculation-contract-and-baseline.md) has been prepared as a documentation-only task definition; it is not executed.
- The earlier outline's AE-01 through AE-08 map in order to RM-001-P1 through
  RM-001-P8. Use the repository-scoped RM identifiers for future work.

## Principles

1. Correct, explicit results take precedence over feature count.
2. Separate numerical calculation, dataset management, civil-time resolution, house geometry and application integration.
3. Use JPL data and independently implemented, appropriately licensed mathematical models. Preserve source identities and applicable notices.
4. Never substitute a target, house system, zodiac, time model or dataset silently.
5. Distinguish implemented, tested, qualified and deployed. None implies the others.
6. Treat model uncertainty, numerical implementation error and civil-time uncertainty separately.
7. Report unavailable optional points without inventing zero positions or reusing stale values.
8. Keep the engine reusable. Accounts, payments, entitlements and personal chart storage belong to the application.
9. Reuse the application's versioned chart and aspect-policy contracts; do not duplicate its aspect/orb logic unnecessarily.
10. Retain explicit offline calculation: any data update is a controlled, versioned operation.


## RM-001/002 — D01 physical planet-centre source feasibility (in review)

The owner selected **physical centres for Mars–Pluto** as the intended commercial target identity, preserving v0.1.0's barycentre profile. [RM-001/002](prompts/002-physical-planet-centres-source-feasibility.md) now has actual binary/hash/segment and same-JPL-data CSPICE evidence for **all six bodies**: [Jupiter](p1-jupiter-centre-qualification.md) on merged PR #4; [Mars, Saturn, Uranus, Neptune and Pluto](p1-five-centres-qualification.md) on [merged PR #5](https://github.com/DioneGate/ariaephemeris/pull/5). The [source feasibility matrix](p1-centre-source-feasibility.md) tracks both completed data gates and remaining model/commercial boundaries. **Source/evaluator agreement is not absolute physical accuracy or a full production qualification**. Compact redistribution, source model compatibility, the production resolver, application integration and remaining D02–D14 owner decisions are separate. RM-001/002 source gate is **In review**, RM-001-P1 **Planned**, and no runtime target/default was changed.

## RM-001/003 — D01 opt-in production multi-kernel calculation profile (in review)

The owner authorised WP4 on 19 November 2026. [RM-001/003](prompts/003-versioned-physical-centre-engine-profile.md) implements the explicit `planet-centres-v1` Python calculation profile on [draft PR #6](https://github.com/DioneGate/ariaephemeris/pull/6), based on `main bfe4a63` after WP3 [PR #5 merged](https://github.com/DioneGate/ariaephemeris/commit/bfe4a636356366514a213c63be07cffd48b5a337). Six SHA-256-pinned original NAIF satellite kernels are used **only for their direct centre offsets**, with Aria DE442s as the parent planetary source. Existing `reference` output remains the default. The PR includes unit tests, six per-source real-kernel integration jobs, a combined all-six chart/batch workflow, schema and CLI changes, and source provenance in outputs. **Runtime code is implemented but not merged, released or commercially qualified**; current gate and actual CI outcomes are in [progress](progress.md). Compact redistribution, source dynamical compatibility, full physical-profile apparent/chart fixtures and app-provider migration remain separate approval gates.

## RM-001/004 — WP5.1 frozen independent Horizons benchmark (in review)

The owner authorised implementation **and merge after passing checks** on 19 November 2026. [WP5.1](prompts/004-independent-horizons-reference-fixtures.md) has obtained **300 genuine JPL Horizons records** (six physical centres × 25 independently specified dates × two reference modes), retaining [all 12 original API responses and exact SHA-256 provenance](../../../data/fixtures/horizons/), with offline source-integrity validation. [The results report](p1-independent-horizons-fixtures.md) records Horizons' live source-model labels, notably Jupiter `jup365_merged`, Saturn `sat441l`, and Neptune `nep098_merged`, which differ from Aria's selected centre-offset kernels. Geometric vectors are **TDB ICRF**, apparent inertial RA/Dec are **TT ICRF**: the data is ready for WP5.2 reference comparisons but **WP5.1 has not evaluated Aria's numerical error**. [PR #7](https://github.com/DioneGate/ariaephemeris/pull/7) **merged** at [`fa8e5b7`](https://github.com/DioneGate/ariaephemeris/commit/fa8e5b7a4a71d01999f712da7b25cbeb711e5510), after offline integrity and fast CI passed. The bounded WP5.1 acquisition is **Done**; P3/P6 phase status remains Planned. No engine runtime, reference defaults, Aria Galaxy code or deployment changed.

## RM-001/005 — WP5.2 external numerical comparison (Done, scientific acceptance open)

The user requested WP5.2 implementation, testing and merge on 19 November 2026. [Prompt RM-001/005](prompts/005-independent-horizons-numerical-comparison.md) and [merged PR #9](https://github.com/DioneGate/ariaephemeris/pull/9) delivered an **offline numerical comparator** between Aria's six-source `planet-centres-v1` profile and the 300 independent frozen JPL Horizons cases. It explicitly aligns TDB geometric 3D vectors and TT inertial apparent ICRF RA/Dec, verifies all 12 reference source hashes, and retains per-case and per-body maxima/RMS/p95 with model labels. [Measured results](p1-external-horizons-comparison.md) show **all 150 apparent samples below a provisional 1-arcsecond diagnostic level**; the largest sampled geometric position difference is approximately **40.91 km for Pluto**, with other-source model discrepancies unresolved. **This is a bounded measurement, not a commercial accuracy qualification**; no Aria engine runtime or Aria Galaxy code changed, and parent P3/P6 remain Planned. [Fast CI #44478988481](https://github.com/DioneGate/ariaephemeris/actions/runs/44478988481) passed, the independent 300-case report was read back from main, and [PR #9 merged at `6216f15`](https://github.com/DioneGate/ariaephemeris/commit/6216f15c9bac88bcfa5bf4eeadb444f7730b0ac1). Bounded WP5.2 is Done; broader scientific acceptance remains open.

## RM-001/006 — Jupiter and Pluto JPL source-model reconciliation (Done, scientific acceptance open)

The owner requested diagnosis of Jupiter and Pluto's larger WP5.2 geometric discrepancies. [RM-001/006](prompts/006-jpl-source-model-reconciliation.md) adds eight independently sourced Horizons vector responses and 200 TDB source-component states, their immutable SHA-256 provenance, a strict offline verifier and [50 exact source-residual decompositions](p1-jpl-source-reconciliation.md) in [merged PR #11](https://github.com/DioneGate/ariaephemeris/pull/11). **The 14.82 km Jupiter and 40.91 km Pluto geocentric discrepancies are accounted for by differing planetary barycentre/observer models; effective centre offsets differ by at most 0.248 mm and 1.908 mm respectively over the sampled dates.** JPL source comments confirm that `jup349.bsp` inherits physical Jupiter 599 from `jup365.bsp`, while `plu060.bsp` merges a DE440 planetary base and Pluto's original direct offset. The independent Horizons reference reports DE441. This is strong numerical **source-model attribution, not a certification of absolute astronomical uncertainty**. Proposed product-alignment limits remain for owner review and additional dense sampling, frame/correction and event testing. No engine model, defaults, source binaries, Aria Galaxy or deployment was changed; [PR #11 merged](https://github.com/DioneGate/ariaephemeris/commit/0b5d6d661e5796a7d74889dcffc323741707c1bd) on 19 November 2026. WP5.3 attribution is Done, while parent scientific certification remains open.

## RM-001/007 — WP5.4 Tropical coordinates and signed rates (Done, commercial acceptance open)

The owner authorised **implementation, not merge** of WP5.4 on 19 November 2026. [Draft PR #12](https://github.com/DioneGate/ariaephemeris/pull/12) now captures [930 independently sourced Horizons apparent inertial directions](../../../data/fixtures/horizons/wp54-tropical/wp54-horizons-tropical-stencils-v1.json) (780 newly queried, 150 reused from WP5.1) for 186 geocentric apparent **tropical true-ecliptic-of-date** positions, latitudes and signed longitude rates. This includes 25 baseline/segment cases per physical Mars–Pluto planet and 3 station + 3 ingress stress cases each. [Measured findings](p1-wp54-tropical-coordinate-qualification.md) show **max 0.004433 arcsec longitude, 0.004786 arcsec latitude and 6.228 × 10⁻⁸ degrees per TT day signed-rate discrepancy** across the sampled cases, with **zero robust motion-direction or zodiac-sign mismatches**. Reference coordinates/rates are derived only from JPL apparent inertial RA/Dec; critical test times are Aria-*nominated* and true-date IAU transform standards share ERFA 2.0.1.5, both disclosed. Provisional 0.05″ coordinate and 0.0001°/day rate thresholds were not exceeded, **but neither is a qualified absolute uncertainty or event-root timing limit**. No engine runtime, default profile, Aria Galaxy or deployment changed; parent RM-001-P3/P6 remain Planned.

## RM-001/008 — WP5.5 independently sourced event timing (In review)

The owner authorised implementation of event-timing qualification on 19 November 2026. [RM-001/008](prompts/008-wp5-5-independent-event-timing.md) on [draft PR #13](https://github.com/DioneGate/ariaephemeris/pull/13) prepares explicit TT-domain **22 source-nominated planetary events**: six physical-centre stations, six tropical 30° ingresses, and five Mars–outer-planet conjunctions plus five oppositions. It obtains **original JPL Horizons airless apparent inertial rays** at independent nine-point observed root grids (and five-point JPL-derived rate stencils for stations), solves reference roots *only* from these source observations, and separately compares Aria's existing `find_events` returned roots, signed differences, bracket and conditioning. Candidate test windows are Aria-nominated: **this is not blind event discovery, global completeness, rigorous interpolation error or commercial accuracy certification**. The 60-second threshold is only an unapproved diagnostic. No engine runtime, source model defaults or Aria Galaxy changes are permitted in this review package. The initial [22-case independent JPL numerical report](../../validation/wp55-independent-event-roots.json) measured **22/22 corresponding Aria events**, with maximum TT discrepancies of **4.61 s for stations (Neptune)**, **0.044 s ingresses**, **0.040 s conjunctions** and **0.039 s oppositions**. Independently sourced JPL **±15-second near-root observations**, [all 224 new rays and per-case sign-bracket evidence](../../validation/wp55-jpl-fine-root-brackets.json), demonstrate **22/22 original JPL event sign changes within an observed 30-second window**, and **all 22 Aria times lie within those source brackets**. The source comparison is not an absolute physical truth-model accuracy or global event-completeness certificate; all candidate tolerances remain unapproved. [Source kernel/event acquisition #44534617647](https://github.com/DioneGate/ariaephemeris/actions/runs/44534617647) and [JPL-only fine root #44535411289](https://github.com/DioneGate/ariaephemeris/actions/runs/44535411289) passed; full PR-specific replay and CI pending.

## Delivery plan

| Phase | Outcome | Depends on | Status | Next action |
| --- | --- | --- | --- | --- |
| RM-001-P1 | Scope, calculation contracts and reproducible baseline | Existing source | Planned | RM-001/001 docs merged via PR #3; RM-001/002 all six source/evaluator gates pass, WP3 merged by PR #5; WP4 runtime profile on draft PR #6; compact packaging and remaining decisions/qualification before phase acceptance |
| RM-001-P2 | Reliable everyday date/time entry | P1 | Planned | Define historical civil-time and managed time-data policies |
| RM-001-P3 | Launch calculation capabilities | P1; P2 for civil-time qualification | Planned | WP4 profile merged in PR #6; [WP5.1 Horizons reference data](p1-independent-horizons-fixtures.md) merged in PR #7; WP5.2 numerical comparator/report merged in PR #9; Jupiter/Pluto source attribution complete in merged PR #11; WP5.4 chart coordinate and signed-rate comparison on merged PR #12; independent event timing and wider model accuracy remain open; remaining capability decisions still open |
| RM-001-P4 | Integration with the Aria application | P1; applicable P2/P3 capabilities | Planned | Specify the persistent service and provider-neutral adapter contract |
| RM-001-P5 | Interactive and batch performance | P4; profiling may start earlier | Planned | Approve workloads, deployment hardware and service-level targets |
| RM-001-P6 | First production-qualified engine release | P2–P5 for agreed launch scope | Planned | Define exact-release qualification, packaging and deployment gates |
| RM-001-P7 | Historical range and long-term models | P1; P6 preferred | Planned | Confirm product priority, datasets, calendars and long-term model policy |
| RM-001-P8 | Specialist capabilities and distribution | Relevant qualified foundations | Planned | Select bounded work packages against product demand |

P3 and P4 can overlap once interfaces are stable. P7 is not a launch dependency
unless historical research outside the initial interval is selected as a launch
requirement. Each advertised capability must pass its own gate.

## RM-001-P1 — Scope, conventions and baseline

### RM-001/001 execution deliverables (reviewable, not phase acceptance)

- [Full 29-object and consumer capability matrix](p1-capability-matrix.md) — source-mapped app/engine differences and future fixtures.
- [Proposed calculation contract](p1-calculation-contract.md) — target IDs, centres vs barycentres, time/frame/correction semantics, provider and error contracts.
- [Candidate commercial launch scope and 14 owner decisions](p1-launch-scope-and-decisions.md) — **all decisions Open**; no launch exclusions approved.
- [Qualification baseline and replay record](p1-qualification-baseline.md) — historical October evidence identified, current November source inspection verified; **numerical replay NOT RUN** because this shell has no repository checkout/network/kernel.

The [RM-001/001 prompt](prompts/001-commercial-calculation-contract-and-baseline.md) was delivered via [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3), **merged** at `df96380`; its documentation does not close the broader P1 qualification gate. These documentation deliverables **do not make P1 Done**: owner scope/gates and a new real-kernel replay remain necessary. P1–P8 are still Planned.


Create an authoritative capability inventory shared by the engine team and application integration work. Define the first commercial calculation offering and identify any application capabilities that must initially be unavailable.

Deliverables:

- Current capability matrix, separated from proposed launch scope.
- Body/point registry with canonical IDs, target definitions and source requirements.
- Request/result conventions covering frames, origins, corrections, time scales, units, rates, houses and zodiac.
- Explicit distinction between apparent chart defaults and geometric activation defaults.
- Qualification plan with independent references, justified acceptance limits and unsupported cases.
- Reproducible baseline commands, results and missing-evidence register.
- Prioritised implementation backlog and decision log.
- Read-only inspection of current Aria Astrology backend ephemeris calls and feature dependencies; a **Swiss-to-Aria capability/contract matrix** distinguishing positions, signed rates, chart angles/houses, calculated points, time conversion, batches and events. Record which astrological aspects are already calculated by the application, rather than assuming the ephemeris must reproduce their policy.
- Explicit launch, beta and deferred feature list; each unsupported chart setting must have a specified UI/API behaviour. No cross-repository implementation is authorised by inventory work.
- A written decision on whether the first service will remain Python-only (recommended baseline), the profiling workload and the later Rust proof-of-concept trigger.

Exit: every launch capability has an owner, definition, evidence requirement and delivery phase. No unimplemented feature is labelled supported.

## RM-001-P2 — Civil time and Earth orientation

Make ordinary birth-date input work without requiring users to understand astronomical time scales.

Deliverables:

- A documented pre-1972 civil-time policy, including local mean time and historical timezone limitations where relevant. Do not invent modern UTC for ancient dates.
- Consistent UTC/TT/TDB/UT1 conversion with explicit assumptions and user overrides for specialist inputs.
- Versioned leap-second, timezone and Earth-rotation inputs; controlled updates, expiry behaviour and offline operation.
- Distinguish observed values, modelled values, missing information and uncertainty.
- Keep DST gaps rejected and overlaps explicitly resolved. Preserve historical second offsets where the source supports them.
- Precision policy for charts with unknown time; do not present precise houses for an unknown birth time.

Exit: supported civil dates work end to end, including representative births before 1972. Tests cover leaps, DST changes, expiry, missing data, boundaries and uncertainty warnings. Time-data assumptions remain visible in results.

## RM-001-P3 — Launch calculation capabilities

Implement in small, independently testable increments:

1. Standalone angles/houses API, with ASC/MC rates and documented degeneracy handling.
2. Mean and true lunar nodes, corresponding south nodes, and explicitly defined mean lunar apogee.
3. Vertex, solar-altitude/sect calculation and named Part of Fortune formulas, including rates where mathematically valid.
4. Additional selected house systems: Placidus, Porphyry, Regiomontanus and Campanus. Add others only against demonstrated product demand.
5. A defined Lahiri sidereal mode if included in launch scope, with consistent planetary, angle and house conventions.
6. Selected minor bodies, starting with Chiron and the main asteroids if required. Use verified datasets with per-body date ranges.

Dependencies vary: most house geometry does not need a planetary kernel; Fortune requires the Sun and Moon; sect requires the Sun's geometric horizon relation. Sidereal output needs an explicit frame/ayanamsa convention. These are separate calculations, not arbitrary longitude offsets.

Exit: each feature has mathematical references, provenance, boundary tests and qualification evidence. Undefined polar cases or missing optional data are explicit. The application cannot request an unsupported feature as if it were available.

## RM-001-P4 — Application integration

Recommended initial topology: React application → existing Express API → persistent private Python engine worker/service.

Deliverables:

- Provider-neutral calculation boundary in the existing backend; maintain versioned ChartData, AspectPolicy and ChartAnalysis contracts.
- Persistent workers keeping verified kernels open; controlled startup checks and read-only dataset mounts.
- Typed request/response validation, capabilities endpoint and structured failures.
- Position, chart, batch and bounded-search operations mapped to the existing API.
- Retain per-point availability, provenance, signed rates, sect, house assignment and warnings.
- Cache identity includes dataset, engine version, numerical conventions and all relevant inputs. Presentation settings do not invalidate numerical results.
- Cancellation, stale-response protection, request budgets and private internal network access.
- Integration checks for wheel, position table, aspect matrix, activation curves and clock mode.
- Provider comparison fixtures with matching astronomical conventions, explicit planetary-system barycentre targets versus physical centres, and justified numerical tolerances. Capture the differences rather than claiming byte-for-byte parity.
- A separate authorised change/PR in the Aria Astrology repository when production provider switching is implemented; this roadmap does not itself authorise that code change.

Exit: one accepted snapshot drives all chart views; apparent/geometric semantics remain intact. Saved documents are recalculated deliberately, never silently reinterpreted. Unsupported features are visible rather than hidden behind invented results.

## RM-001-P5 — Performance and capacity

Optimise measured workloads while preserving declared numerical behaviour.

Deliverables:

- Deployment-host baseline and profiler results, with calculation and transport costs separated.
- Reuse time/frame computations, vectorise where appropriate and avoid unnecessary complete correction-pipeline evaluations.
- Bounded background batch jobs, queue limits, cancellation and reusable activation-series caches.
- Clock scheduling that prevents overlapping work, pauses when not needed and does not restart the engine each second.
- Concurrency and soak tests; memory/CPU budgets and recovery from worker failure.
- A decision record on Python-first optimisation and any **Rust native-core proof of concept**: compare representative end-to-end workloads, implementation maintenance cost, memory and numerical agreement; adopt native code only after independent requalification and demonstrated value. The Rust path must not delay a sufficiently performing Python commercial release.

Proposed initial targets, to approve in RM-001-P1: warm single-chart p95 below 250 ms; ten-body 10,000-epoch batch below 10 seconds on the chosen deployment host; stable one-second clock updates at a declared concurrent-user load. These are engineering targets, not current capabilities. Define body count, corrections, rates, cache state, hardware and sample policy for every measurement.

Exit: approved service-level targets pass repeated tests on the intended host. Every numerical optimisation reruns applicable qualification; speed gains cannot silently change accuracy or conventions.

## RM-001-P6 — Production qualification and release

Deliverables:

- Versioned package/release, reproducible deployment configuration and pinned source-data identity.
- Fast tests, full real-kernel qualification, installation smoke tests and application end-to-end tests.
- Separate dependencies for runtime versus development/reference work; complete software/data inventory and redistribution notices for the actual shipped platform.
- Security review of service exposure, validation, request budgets and resource exhaustion.
- Operational health, numerical-error monitoring, controlled data updates and rollback to a qualified Aria version.
- Evidence from the **actual production application build** that every advertised chart/activation route uses the qualified Aria provider, with no hidden dependency on or fallback to the previous provider. This requires authorised changes and verification in the separate application repository.
- Deployment verification and accountable release sign-off. Package publication is optional; a pinned private deployment is acceptable.

Exit: all advertised launch features are qualified in the deployed configuration; required failures fail safely; no runtime path silently invokes an undeclared provider. Application authentication, billing, privacy and asset rights remain separate launch checks.

## RM-001-P7 — Historical range and long-term models

Deliverables:

- Multiple-dataset registry, beginning with long-range JPL DE441 coverage.
- Explicit Julian/Gregorian calendar selection, astronomical year numbering and BCE handling outside standard civil-date library limits.
- Long-term precession, obliquity, sidereal-time and time-conversion policies; review every correction model over its declared range.
- Historical Earth-rotation estimates and clearly communicated uncertainty.
- Per-body coverage and endpoint margins for light-time iterations and numerical derivatives.
- Qualification across centuries, dataset overlaps, source boundaries and extreme dates.

Exit: publish separate supported/qualified intervals for each calculation family. A long-range source file is not by itself evidence of qualified long-range charts. Never extrapolate a short kernel beyond its source interval.

## RM-001-P8 — Specialist capabilities and distribution

Potential independent work packages:

- Return searches, eclipses, occultations, rise/set calculations and selected fixed-star techniques.
- Additional ayanamsas, house systems and minor-body datasets.
- Compact coefficient packs with independently measured position, rate and event-timing error budgets.
- Downloadable date blocks retaining original coefficients where size reduction does not require approximation.
- Browser/native bindings or WebAssembly only after a feasibility and licensing review.
- Public SDK documentation, examples and compatibility policy.

Exit: each package has a clear product need, model definition, source terms, supported range and feature-specific qualification. No speculative size, speed or accuracy claim becomes a release promise without measurement.


## First commercial release boundary

The first paid application does not require every phase to finish. Approve one calculation scope, complete P1–P6 for that scope, and expose only capabilities covered by acceptance evidence.

Go/no-go checklist:

- [ ] Everyday supported birth dates resolve without specialist input.
- [ ] Advertised bodies, points, houses and zodiac modes are implemented and qualified.
- [ ] Target centres, corrections, rates and frame conventions are explicit.
- [ ] Chart views and activation calculations preserve their respective semantics.
- [ ] Missing optional data and undefined houses are represented honestly.
- [ ] Dataset identity, time-data assumptions and engine version accompany results.
- [ ] Performance and concurrency limits are measured on deployment hardware.
- [ ] The actual runtime dependency/data inventory has passed redistribution review.
- [ ] Full qualification and deployed end-to-end evidence refer to the shipped version.
- [ ] A verified application-level provider inventory demonstrates that no production calculation path uses an undeclared ephemeris or fallback.
- [ ] Explicit launch-scope exclusions are honoured in chart settings, saved documents and API errors.
- [ ] A measured Python-versus-native decision exists; a Rust rewrite is not assumed necessary.
- [ ] Monitoring, controlled updates and rollback have been exercised.


## Milestones

| Milestone | Required evidence | Current state |
| --- | --- | --- |
| Development contract agreed | P1 acceptance; owner decisions recorded | Not reached |
| Application pilot | Agreed P2/P3 subset, P4 end-to-end evidence and bounded capacity | Not reached |
| First production-qualified engine release | P1–P6 gates for the agreed offering; actual deployed-version evidence | Not reached |
| Historical research extension | P7 calculation-family qualification and uncertainty policy | Not reached |
| Specialist releases | Selected P8 work packages individually qualified | Not reached |

## Decisions before dependent prompts become Ready

All proposals below remain open unless explicitly recorded as resolved by the owner.

| Decision | Owner | Required by | Current proposal / next action |
| --- | --- | --- | --- |
| First commercial dates, bodies, points, houses and zodiac | Marek | P1 launch contract | Propose a 1900–2100 tropical core; decide which additional current application options must be retained or explicitly unavailable |
| Historical civil time, unknown birth time and Earth-rotation assumptions | Marek; implementer proposes technical policy | P2 | Document observed/modelled data, uncertainty and specialist overrides before implementation |
| Numerical acceptance limits and reference-model conventions | Marek; implementer supplies evidence | P1/P3 | Approve scoped gates; keep model uncertainty distinct from evaluator residuals |
| Integration topology and cross-repository delivery scope | Marek | P4 | Persistent private Python worker/service behind the existing Express API is proposed, not yet mandated; application-repository changes need separate authorisation |
| Python optimisation versus Rust migration | Marek; implementer benchmarks | P5 | Profile and optimise Python first; approve a bounded Rust PoC only if measured constraints require it; native rewrite is not a launch prerequisite |
| Hardware, concurrency and performance targets | Marek | P5 | Review the proposed chart p95 and batch targets using representative workloads |
| Feature additions versus deliberately reduced initial scope | Marek | P3/P6 | Explicit product decision; never silently downgrade saved-chart settings |
| Historical-range launch dependency | Marek | P1/P7 | Defer until after initial release unless historical research makes it essential |
| Release distribution and operational ownership | Marek | P6 | Pinned private deployment can precede public package publication |

## Next planning action

Review [PR #3](https://github.com/DioneGate/ariaephemeris/pull/3) and its [RM-001/001 source/evidence deliverables](p1-capability-matrix.md); seek owner decisions D01–D14 from the [scope/decision register](p1-launch-scope-and-decisions.md), and arrange a network-enabled pinned runner for the [real-kernel replay](p1-qualification-baseline.md). The execution PR is a documentation-only submission and **must not be merged without explicit authorisation**. RM-001-P1 stays Planned until its calculation-contract/baseline gate is accepted; P2–P8 remain Planned.
