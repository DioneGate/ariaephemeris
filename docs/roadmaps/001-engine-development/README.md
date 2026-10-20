# RM-001 — Engine development and commercial application readiness

| Field | Value |
| --- | --- |
| Product owner | Marek / DioneGate |
| Last reviewed | 2026-10-20 |
| Inspected implementation baseline | [`39b25ae`](https://github.com/DioneGate/ariaephemeris/commit/39b25aec9023bcc79172a0f0cf7aed373efafc89), package 0.1.0 |
| Progress and evidence | [progress.md](progress.md) |
| Implementation prompts | [Prompt register](prompts/README.md) |
| Framework | [Roadmap register and conventions](../README.md) |

## Outcome

Develop Aria Ephemeris into a dependable, independently maintained astronomical
calculation platform for the commercial Aria application. Prioritise trustworthy
everyday chart calculations and efficient activation timelines, then expand
techniques, historical coverage and deployment options.

This roadmap records the standalone development plan prepared on 20 October 2026.
It does not start numerical implementation, generate a phase prompt, authorise
a package release or confirm a production deployment.

## Scope and boundaries

- Develop the engine's contracts, time handling, chart capabilities, integration
  boundary, performance, qualification and release process.
- Reuse the existing application contracts and preserve their numerical semantics.
- Accounts, payments, entitlements and personal chart storage remain application
  responsibilities. This roadmap does not authorise changes in the application repository.
- First paid use need not await all long-range or specialist work. Resolve the
  advertised calculation scope before treating optional capabilities as release blockers.
- Existing 0.1.0 features are reusable foundations, not completion of these phases.
- All eight phases below are Planned. No delivery prompt has been generated.
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


## Delivery plan

| Phase | Outcome | Depends on | Status | Next action |
| --- | --- | --- | --- | --- |
| RM-001-P1 | Scope, calculation contracts and reproducible baseline | Existing source | Planned | When requested, generate RM-001/001 for a bounded contract/baseline increment |
| RM-001-P2 | Reliable everyday date/time entry | P1 | Planned | Define historical civil-time and managed time-data policies |
| RM-001-P3 | Launch calculation capabilities | P1; P2 for civil-time qualification | Planned | Prioritise angle rates, nodes and derived points, then selected houses/zodiac/minor bodies |
| RM-001-P4 | Integration with the Aria application | P1; applicable P2/P3 capabilities | Planned | Specify the persistent service and provider-neutral adapter contract |
| RM-001-P5 | Interactive and batch performance | P4; profiling may start earlier | Planned | Approve workloads, deployment hardware and service-level targets |
| RM-001-P6 | First production-qualified engine release | P2–P5 for agreed launch scope | Planned | Define exact-release qualification, packaging and deployment gates |
| RM-001-P7 | Historical range and long-term models | P1; P6 preferred | Planned | Confirm product priority, datasets, calendars and long-term model policy |
| RM-001-P8 | Specialist capabilities and distribution | Relevant qualified foundations | Planned | Select bounded work packages against product demand |

P3 and P4 can overlap once interfaces are stable. P7 is not a launch dependency
unless historical research outside the initial interval is selected as a launch
requirement. Each advertised capability must pass its own gate.

## RM-001-P1 — Scope, conventions and baseline

Create an authoritative capability inventory shared by the engine team and application integration work. Define the first commercial calculation offering and identify any application capabilities that must initially be unavailable.

Deliverables:

- Current capability matrix, separated from proposed launch scope.
- Body/point registry with canonical IDs, target definitions and source requirements.
- Request/result conventions covering frames, origins, corrections, time scales, units, rates, houses and zodiac.
- Explicit distinction between apparent chart defaults and geometric activation defaults.
- Qualification plan with independent references, justified acceptance limits and unsupported cases.
- Reproducible baseline commands, results and missing-evidence register.
- Prioritised implementation backlog and decision log.

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

Exit: one accepted snapshot drives all chart views; apparent/geometric semantics remain intact. Saved documents are recalculated deliberately, never silently reinterpreted. Unsupported features are visible rather than hidden behind invented results.

## RM-001-P5 — Performance and capacity

Optimise measured workloads while preserving declared numerical behaviour.

Deliverables:

- Deployment-host baseline and profiler results, with calculation and transport costs separated.
- Reuse time/frame computations, vectorise where appropriate and avoid unnecessary complete correction-pipeline evaluations.
- Bounded background batch jobs, queue limits, cancellation and reusable activation-series caches.
- Clock scheduling that prevents overlapping work, pauses when not needed and does not restart the engine each second.
- Concurrency and soak tests; memory/CPU budgets and recovery from worker failure.

Proposed initial targets, to approve in RM-001-P1: warm single-chart p95 below 250 ms; ten-body 10,000-epoch batch below 10 seconds on the chosen deployment host; stable one-second clock updates at a declared concurrent-user load. These are engineering targets, not current capabilities. Define body count, corrections, rates, cache state, hardware and sample policy for every measurement.

Exit: approved service-level targets pass repeated tests on the intended host. Every numerical optimisation reruns applicable qualification; speed gains cannot silently change accuracy or conventions.

## RM-001-P6 — Production qualification and release

Deliverables:

- Versioned package/release, reproducible deployment configuration and pinned source-data identity.
- Fast tests, full real-kernel qualification, installation smoke tests and application end-to-end tests.
- Separate dependencies for runtime versus development/reference work; complete software/data inventory and redistribution notices for the actual shipped platform.
- Security review of service exposure, validation, request budgets and resource exhaustion.
- Operational health, numerical-error monitoring, controlled data updates and rollback to a qualified Aria version.
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
| Integration topology and cross-repository delivery scope | Marek | P4 | Persistent private Python worker/service behind the existing Express API is proposed, not yet mandated |
| Hardware, concurrency and performance targets | Marek | P5 | Review the proposed chart p95 and batch targets using representative workloads |
| Feature additions versus deliberately reduced initial scope | Marek | P3/P6 | Explicit product decision; never silently downgrade saved-chart settings |
| Historical-range launch dependency | Marek | P1/P7 | Defer until after initial release unless historical research makes it essential |
| Release distribution and operational ownership | Marek | P6 | Pinned private deployment can precede public package publication |

## Next planning action

When requested, generate the first bounded P1 prompt using the
[implementation prompt template](../templates/implementation-prompt.md).
Its intended outcome is a calculation contract, capability inventory, qualification
plan and safely reproduced baseline—not new astronomical algorithms.

The initial records created here are roadmap administration only. Detailed
capability, launch-scope and qualification documents should be added by their
authorised phase increments; their absence must not be mistaken for completed P1.
