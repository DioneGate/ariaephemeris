# RM-002 — Epic: Aria R1.0 on Aria Ephemeris, then Community 1.0

| Field | Value |
| --- | --- |
| Product owner | Marek |
| Last reviewed | 2026-11-28 |
| Baseline | `main` at [`0cbb394`](https://github.com/DioneGate/ariaephemeris/commit/0cbb394) (24 November 2026), package 0.1.0 |
| Progress and evidence | [progress.md](progress.md) |
| Implementation prompts (stories) | [Prompt register](prompts/README.md) |
| Related roadmap | [RM-001 engine development](../001-engine-development/README.md) (historical evidence, capability matrix, decisions D01–D14) |

## Epic statement

> **As** the owner of Aria Galaxy, **I want** every production calculation in the
> application to run on Aria Ephemeris, with no Swiss Ephemeris (SE) code
> or data, **so that** the product has no ephemeris licence cost and the
> engine can be given to the community as an unrestricted, Apache-2.0 project.

Two outcomes, delivered in this order:

1. **Aria R1.0.** Aria Galaxy production uses Aria Ephemeris for all advertised
   chart and activation calculations. SE has been removed from the production
   runtime, and there is no hidden fallback.
2. **Community 1.0.** Aria Ephemeris is a public, documented, installable project
   that external contributors can build, test and extend without private
   knowledge or private infrastructure.

The path is deliberately the **shortest one to R1.0**. Every increment also
leaves a **community dividend**: an artefact that a future public project needs
anyway (public API, reference tests, documentation, CI). That way no R1.0 work
has to be thrown away or redone when the project goes public.

## Relationship to RM-001

RM-001 stays the record of delivered history (prompts 001–013), the
[capability matrix](../001-engine-development/p1-capability-matrix.md) and the
[launch decision register](../001-engine-development/p1-launch-scope-and-decisions.md).
RM-002 does **not** renumber or duplicate that history. It defines the **R1.0 slice**
and the order of work across RM-001's broad phases:

| RM-002 increment | Delivers scope from RM-001 |
| --- | --- |
| P1 | P1 (contract and decisions) |
| P2, P3 | P3 (launch calculation capabilities, items 1–4) |
| P4 | P2 (civil time and Earth orientation, the R1.0 subset) |
| P5 | P5 (performance) |
| P6–P8 | P4 (application integration) |
| P9 | P6 (production qualification and release) |
| P10, P11 | P8 (distribution) and new community scope |

RM-001 phase statuses change only when their own gates are met. RM-002 evidence
may be cited as input to those gates.

## Working language (agile vocabulary)

Proposed vocabulary for planning conversations, issues and the board. The
**status values stay exactly as mandated** by [AGENTS.md](../../../AGENTS.md) and the
[roadmap conventions](../README.md#status-and-evidence). Only the surrounding
vocabulary changes.

| Agile term | Meaning in this repository | Existing artefact / ID |
| --- | --- | --- |
| **Epic** | A large outcome spanning several releases | A roadmap, e.g. **RM-002** |
| **Milestone / release** | A dated or gated, user-visible outcome | **M1–M5** below (R0 Pilot, R1.0, C1.0) |
| **Increment** | A shippable, demonstrable slice, normally one or two sprints | A phase, ID **RM-002-Pn** (ID format unchanged) |
| **Story** | One bounded change, deliverable as one PR | An implementation prompt, ID **RM-002/NNN** |
| **Task** | A step inside a story | A checklist item in the prompt or PR |
| **Spike** | A time-boxed investigation that produces evidence, not features | A prompt marked `Type: Spike` |
| **Backlog** | Recorded scope not yet actionable | Status **Planned** |
| **Definition of Ready (DoR)** | Decisions resolved, dependencies met, acceptance criteria written | Status **Ready** |
| **Definition of Done (DoD)** | Acceptance verified **and** merged; evidence recorded in progress.md | Status **Done** |
| **Icebox** | Consciously postponed, with a revisit trigger | Status **Deferred** |
| **Acceptance criteria** | Observable, testable outcomes, ideally *Given / When / Then* | The prompt's acceptance section |
| **Sprint goal** | The one outcome a sprint must reach | Recorded in progress.md for each sprint |
| **Demo / review** | Showing working software against the acceptance criteria | Evidence row in progress.md |
| **Retrospective** | What to change in the process | A short note in progress.md |
| **MVP / MMP** | Minimum viable versus minimum *marketable* product | Pilot (MVP) versus R1.0 (MMP) |

Suggested story format for future prompts (adopt by changing the prompt template only when authorised):

```text
Story RM-002/NNN — <title>            Increment: RM-002-Pn   Type: Story | Spike
As a <astrologer | Aria Galaxy backend | contributor>, I want <capability>,
so that <value>.
Acceptance (Given/When/Then) · Numerical definition · Independent reference ·
Out of scope · Evidence tier (Pilot-grade | Release-grade)
```

**Two evidence tiers** (proposed in decision E12). These keep the scientific standard
where it matters without slowing every story down:

- **Pilot-grade:** fast tests, an independent reference check on a bounded sample, and
  documented conventions. This is enough to merge and run in the internal pilot.
- **Release-grade:** the full real-kernel qualification of every advertised
  capability on the shipped version. This is required for R1.0 (P9) and for public
  releases (P11).

## Scope and boundaries

**In scope for R1.0** (pending decision E01): the default and commonly used Aria
Galaxy chart objects, Equal, Whole Sign and Placidus houses, the tropical zodiac,
1900–2100 natal and transit charts, the range/activation series, a persistent
private calculation service, and the application adapter and cutover.

**Explicitly out of R1.0** (shown as *unavailable / coming soon*, never approximated):
Chiron and the other minor bodies, sidereal/Lahiri, the eclipse marker, dates
before 1900, houses other than Equal/Whole Sign/Placidus, and browser/native runtimes.

**Preserve:** the Python 3.12+ / NumPy / PyERFA / jplephem reference engine,
existing public Python, CLI and JSON-schema contracts (extend with new versions;
do not break), explicit target identity, scalar/batch consistency, signed rates,
explicit unavailable results, dataset checksums and offline runtime.

**Authority boundaries:** this epic records a plan. It does **not** authorise
implementation, merge, application-repository changes, deployment, package
publication or a change of repository visibility. Each of those needs its own
explicit authorisation (see [AGENTS.md](../../../AGENTS.md)). Changes in the Aria
Galaxy application repository (P7, P8, part of P9) are delivered there, under
separate authorisation.

## Delivery plan

Sizes are relative t-shirt estimates (S ≈ ≤ 1 sprint, M ≈ 1–2, L ≈ 2–3) for
planning only. They are not commitments or measured velocity.

| Increment | Outcome | Depends on | Size | Status | Community dividend |
| --- | --- | --- | --- | --- | --- |
| RM-002-P1 | **Sprint 0 — decisions and green baseline** | — | S | Planned | Public decision log; reproducible CI qualification |
| RM-002-P2 | **Chart points**: nodes, Lilith, angles with rates, Vertex, Fortune, sect | P1 | M | Planned | Reference-tested "how to add a point" pattern |
| RM-002-P3 | **Placidus** and a house-system contract | P1 | S | Planned | Pluggable house-system interface for contributors |
| RM-002-P4 | **Everyday time for real users**: pre-1972 births, future dates, data updates | P1 | M | Planned | Documented time policy and data-update runbook |
| RM-002-P5 | **Batch performance**: a profiling spike, then optimisation | P1 (can run alongside P2–P4) | M | Planned | Public, reproducible benchmark |
| RM-002-P6 | **Calculation service**: a persistent private worker with a capabilities endpoint | P2–P4 contracts stable | M | Planned | `ariaephemeris serve` usable by any app |
| RM-002-P7 | **Pilot**: application adapter plus chart endpoint behind a flag (app repo) | P6 | M | Planned | Provider-neutral adapter contract, published as a schema |
| RM-002-P8 | **Full cutover**: range/activation, caches, saved charts (app repo) | P5, P7 | M | Planned | Integration guide for other applications |
| RM-002-P9 | **Aria R1.0 release gate**: qualification, security and operations; SE removed | P2–P8 | M | Planned | Release-grade qualification process in CI |
| RM-002-P10 | **Community readiness**: governance, contributor experience, CI for forks | Can start after P1; must finish after P9 | M | Planned | — (this *is* the dividend) |
| RM-002-P11 | **Community 1.0 public release**: PyPI, public repo, announcement | P9, P10 | S | Planned | — |

Order of work: P1 → (P2 ∥ P3 ∥ P4 ∥ P5) → P6 → P7 → P8 → P9 → P11. P10 tasks can be
pulled into any sprint with spare capacity. The critical path is
**P1 → P2 → P6 → P7 → P8 → P9**.

---

## RM-002-P1 — Sprint 0: decisions and green baseline

**Goal:** everyone can see what R1.0 contains and what it excludes, and the existing engine is
proven green on a pinned, reproducible runner.

Stories:

1. Record the owner's resolution of decisions **E01–E14** (below) in this README.
2. Run the **real-kernel qualification** (`tools/datasets/qualify.py`, the supplementary
   opposition check, `pytest` with `ARIA_KERNEL`) on the pinned
   `requirements/development.lock` environment. Record the actual results in progress.md.
   The 2026-11-28 ad-hoc fast run used unpinned Python 3.13 and is **not** a baseline.
3. Re-inventory the Aria Galaxy SE call sites (read-only) against the RM-001 matrix at
   app commit `4ab5f99`. Record any drift and the **actual default chart settings and
   usage**: which objects, houses and zodiac users really select.
4. Consolidate the 17 workflows into a documented set: fast CI, real-kernel qualification,
   and manual acquisition/reference jobs.

Acceptance:

- [ ] E01–E14 each have an owner resolution, or an explicit Deferred with its revisit trigger.
- [ ] A real-kernel qualification passes on `main` with the recorded kernel SHA-256 and versions.
- [ ] The R1.0 capability list (one row per advertised object, house system, zodiac mode and
      date policy) is frozen, and every row has an increment and an evidence tier.
- [ ] The workflow inventory is documented. No qualification gate is lost when workflows are consolidated.

## RM-002-P2 — Chart points

**Goal:** the engine returns every R1.0 chart point with explicit definitions, rates and
unavailable reasons.

Stories (each one PR; pilot-grade evidence first, release-grade in P9):

| Story | Definition to specify (E04–E07) | Independent reference |
| --- | --- | --- |
| Mean lunar node, plus south node (+180°) | Published mean-element polynomial; ecliptic and equinox of date; rate is the analytic derivative | A second implementation of the published formula; JPL Horizons Moon osculating elements, used for a sanity range only |
| True (osculating) node, plus south node | Ascending node of the instantaneous geocentric lunar orbit, from the DE Moon state (**h** = **r** × **v**), transformed to the ecliptic of date | JPL Horizons osculating Ω of the Moon about Earth at matched epochs and frame |
| Mean Black Moon Lilith (mean lunar apogee) | Mean-perigee/apogee polynomial from the same lunar theory as the mean node | A second published-formula implementation |
| ASC/MC rates; DSC/IC as explicit outputs | Analytic or matched finite-difference derivative of the existing angle functions; DSC = ASC + 180°, IC = MC + 180° | Independent numerical differentiation |
| Vertex (and Antivertex) | Prime-vertical/ecliptic western intersection; explicit degeneracy rule at extreme latitudes | Independent spherical-trigonometry implementation |
| Sect and Part of Fortune | Sect from the Sun's geometric altitude at the observer; day formula ASC + Moon − Sun, night formula reversed; both "sect-aware" and "always-day" variants named | Hand-computed fixtures plus the independent sect check |

Acceptance:

- [ ] Each point has a public, documented definition (frame, equinox, apparent/geometric,
      rate) in `docs/conventions.md`, plus algorithm provenance in `docs/algorithms/`.
- [ ] Results carry a point ID, definition version and rate, or an explicit `unavailable` with a reason.
- [ ] Scalar/batch consistency, circular wrap at 0°/360°, and boundary tests pass.
- [ ] Unknown or approximate birth time returns no angle-dependent points (Vertex, Fortune,
      angles). This preserves the RM-001/011 behaviour.

## RM-002-P3 — Placidus and the house-system contract

**Goal:** Placidus is available, with explicit behaviour where it is undefined. Adding a further
house system becomes a contributor-sized task.

- A house-system registry (`equal`, `whole_sign`, `placidus`, each with an algorithm version),
  so that adding Porphyry, Koch, Regiomontanus or Campanus later needs no API change.
- Placidus by an iterative semi-arc solution with a documented convergence tolerance.
- Above the polar circles, or wherever the solution does not exist, return an explicit
  `unavailable` with a reason (decision E08). Never substitute another system silently.

Acceptance:

- [ ] Placidus cusps agree with an independent implementation to within the E12 tolerance over a latitude/time grid.
- [ ] Polar and degenerate cases return the documented error or unavailable result.
- [ ] House membership of planets is consistent at cusp boundaries.

## RM-002-P4 — Everyday time for real users

**Goal:** normal users can enter their real birth dates and see current and future transits
without specialist input. Every assumption stays visible in the result.

- **Pre-1972 births:** an application-facing default policy (decision E03). It uses the existing
  versioned historical civil-to-UT1 approximation, with a quality label, instead of rejecting
  the date. Many Aria Galaxy users were born before 1972.
- **Future dates and the clock:** the bundled leap table expires on **28 June 2027**, after which
  strict UTC fails. Define the R1.0 policy for transits, the clock and future charts beyond the
  leap-table and EOP prediction windows (decision E09). Possible approaches are a labelled
  non-strict model, or a scheduled data refresh with expiry alarms.
- **Data-update runbook:** how leap seconds, tzdata and EOP snapshots are refreshed, reviewed,
  released and rolled back. There are no silent runtime updates.

Acceptance:

- [ ] Representative births from 1900, 1950, 1971 and 1972, and current/future transits up to 2100,
      resolve end to end with time-quality metadata.
- [ ] Behaviour at the leap-table expiry is tested and matches E09.
- [ ] The runbook has been exercised once on a non-production copy.

## RM-002-P5 — Batch performance

**Goal:** activation and range workloads meet the E11 targets on the intended host.

1. **Spike (time-boxed):** profile the 10-body × 10,000-epoch batch (historical result
   **67.63 s**). Separate the costs of SPK evaluation, time and frame work, apparent
   corrections, Python object construction and serialisation.
2. **Story:** vectorise and share per-epoch work, and optimise result construction. Do not
   change numerical definitions.
3. **Story:** publish a benchmark covering hardware, worker count, cold/warm cache, p50/p95,
   throughput and memory.

Acceptance:

- [ ] The E11 targets pass in repeated runs on the intended host.
- [ ] Applicable qualification is rerun after optimisation, with no change in results beyond replay tolerance.
- [ ] Python stays the engine (decision E13). A native core is considered only if the measured
      targets are still missed after optimisation.

## RM-002-P6 — Calculation service

**Goal:** a persistent, private worker that Aria Galaxy (and later anyone) can call.

- `ariaephemeris serve`: a long-lived process with kernels opened once, versioned JSON
  request/response schemas, a capabilities endpoint (bodies, points, houses, dates, profiles,
  dataset identity), health/readiness, request budgets, cancellation and structured errors.
- Transport per decision E10. Private network only; no public exposure.
- A container image definition, with data installed at build or deploy time from JPL with
  checksum verification. Kernels are never committed.

Acceptance:

- [ ] Contract tests cover every R1.0 operation: positions, chart, batch and bounded events.
- [ ] Warm-chart latency meets E11 through the service, not only in-process.
- [ ] Startup fails clearly on missing or mismatched data. Restarting a worker loses no correctness.

## RM-002-P7 — Pilot (Aria Galaxy repository, separate authorisation)

**Goal:** the internal pilot (milestone R0). The chart endpoint uses Aria behind a feature flag.

- A provider-neutral calculation boundary in the Express API, using versioned ChartRequest,
  Snapshot and Capabilities contracts with `provider: "aria-ephemeris"` and the dataset and
  engine version (decision E02).
- UI options driven by capabilities: unsupported options are disabled with a clear reason (E14).
- **Shadow comparison** in development: SE and Aria results side by side under *matched*
  conventions. Differences are reported per object. SE is a diagnostic comparator only,
  never the accuracy reference, and its output is never used to derive Aria models.

Acceptance:

- [ ] Wheel, position table and aspect matrix render from Aria for internal users.
- [ ] The shadow-diff report explains every difference above tolerance (convention, target, time model or defect).
- [ ] Apparent chart semantics are preserved (E06).

## RM-002-P8 — Full cutover (Aria Galaxy repository, separate authorisation)

**Goal:** every production calculation route uses Aria.

- The `/ephemeris/latitudes[/range]` series and the activation curves move to the Aria service.
  Geometric/true-position semantics are preserved (E06).
- Remove the silent `true_node` → mean-node fallback. Map `true_node` explicitly to
  `north_node_true`.
- Cache keys include provider, dataset hash, engine version, convention versions and inputs.
- Saved charts (V6 documents) follow the E02 migration policy: stored inputs are kept, results
  are recalculated deliberately, and users are notified.
- Clock mode runs on the persistent service without overlapping requests.

Acceptance:

- [ ] Application end-to-end tests cover wheel, table, aspect matrix, activation curves, Time
      Explorer and clock against Aria.
- [ ] A provider inventory of the production build shows that no route calls SE.

## RM-002-P9 — Aria R1.0 release gate

**Goal:** milestone **R1.0**. Aria Galaxy production runs on a qualified Aria Ephemeris
release, and SE is gone.

- Release-grade qualification of **every** advertised R1.0 capability on the exact shipped
  version and data.
- Security review: private exposure, input validation, request budgets, resource exhaustion.
- Operations: health monitoring, numerical-error alarms, data-update procedure, and a rollback
  to the previous qualified *Aria* release, exercised once.
- SE removal: delete the SE dependency and data from the production build in a separate,
  authorised application release (decision E15). Record the deployed-version evidence.
- Software and data notice review for what is actually shipped (decision E16).

Acceptance: the [RM-001 go/no-go checklist](../001-engine-development/README.md#first-commercial-release-boundary)
is satisfied for the R1.0 scope, with deployed-version evidence.

---

## What remains for the public community project (after R1.0)

The increments above already produce most of what a public project needs: a public API,
reference-tested patterns, a service, benchmarks and qualification in CI. The remaining work
is the following.

### RM-002-P10 — Community readiness

- **Front door:** a public-facing README (what it is, what is qualified, a five-minute
  quick-start, how it differs from other ephemerides), an honest limits section and a docs site.
- **Contributor experience:** a rewritten, friendly `CONTRIBUTING.md` ("pick an issue, add a
  reference test, open a PR"); a human-oriented summary of the scientific rules; issue and PR
  templates; and labelled **good-first-issue** stories, for example Porphyry, Koch, Regiomontanus
  and Campanus houses, ayanamsas, and asteroid datasets.
- **Governance:** `CODE_OF_CONDUCT.md`, `SECURITY.md` (vulnerability reporting),
  `GOVERNANCE.md` / `MAINTAINERS.md`, and the contribution sign-off model (E18).
- **Fork-friendly CI:** fast checks run on external PRs without secrets. Real-kernel
  qualification uses a cached, checksum-verified JPL download, and maintainers trigger it.
- **Stability promise:** SemVer for the Python/CLI/JSON API, plus a versioning policy for
  numerical conventions (a behaviour change means a new convention version).
- **Process weight:** keep `AGENTS.md` for AI agents. Make sure humans are not required to read
  it to contribute.

Acceptance:

- [ ] An external contributor can clone, install, test and submit a change using only public documentation.
- [ ] A sample good-first-issue has been completed end to end by someone other than the maintainer (or in a dry run).

### RM-002-P11 — Community 1.0 public release (separate authorisation)

- Change the repository visibility to public, if it is not already, with owner authorisation.
- Publish to PyPI as `ariaephemeris` 1.0.0 via trusted publishing (check name availability first).
- Release notes, a public qualification summary and an announcement.

Acceptance: a published package installs in a clean environment, `install-data` works from
public JPL sources, and the documented examples run.

### Post-1.0 backlog (Icebox, product-driven)

| Item | Notes |
| --- | --- |
| Chiron (fast-follow candidate, E01) | Needs a JPL small-body SPK, per-body coverage and a qualification gate |
| Ceres, Pallas, Juno, Vesta, Hygiea, Eris | Same pattern as Chiron, once the pattern exists |
| Sidereal (Lahiri, then others) | An explicit ayanamsa definition, not a subtracted offset |
| Research mode, about 1550–2650 | Planets only, JPL DE440/DE442 full, labelled ΔT model, no houses by default (E17) |
| Historical natal charts before 1900 | Calendars (Julian/Gregorian), local mean time, ΔT uncertainty |
| Deep cycles (DE441) | Outer-planet cycle research across millennia |
| Eclipses, returns, rise/set, fixed stars | RM-001-P8 work packages |
| Physical planet centres as default | Already implemented as an opt-in; data size and qualification decision (E05) |

## Milestones

| Milestone | Meaning | Gate |
| --- | --- | --- |
| **M1 — Plan agreed** | Scope and decisions are fixed | P1 accepted |
| **M2 — Engine feature-complete for R1.0** | All R1.0 calculations exist at pilot grade | P2, P3, P4 Done; P5 spike done |
| **M3 — R0 internal pilot** | Internal users see Aria charts | P6, P7 Done |
| **M4 — Aria R1.0** | Production on Aria, SE removed | P8, P9 Done, with deployed evidence |
| **M5 — Community 1.0** | Public project and package | P10, P11 Done |

## Decisions

All decisions are **Open** until the owner records a resolution. The suggestions are the
recommended defaults for the shortest path. "Relates to" points to the
[RM-001 register](../001-engine-development/p1-launch-scope-and-decisions.md).

| ID | Decision | Suggested resolution | Relates to | Needed by | State |
| --- | --- | --- | --- | --- | --- |
| E01 | **R1.0 calculation scope** | Sun–Pluto; mean and true nodes with south nodes; mean Lilith; ASC/MC/DSC/IC with rates; Vertex; Part of Fortune; Equal, Whole Sign and Placidus; tropical only. Minor bodies, sidereal and the eclipse marker are shown as "coming soon". **Chiron** is the first fast-follow, unless P1 usage data shows it is essential for R1.0. | D02, D12 | P1 | Open |
| E02 | **Provider identity and saved charts** | Versioned schemas with `provider: "aria-ephemeris"`, engine version, dataset hash and convention versions. Old `'swiss'` V6 documents keep their inputs, are recalculated on open, and show a one-time notice. Never relabel old results. | D05 | P7 | Open |
| E03 | **Supported birth dates** | 1900-01-01 to 2100-12-31. Pre-1972 civil time uses the existing versioned historical approximation by default in the app, with a quality label. Earlier dates are rejected with a "coming in research mode" message. | D03, D11 | P4 | Open |
| E04 | **Unknown or approximate birth time** | Planets only (the noon convention is labelled), with RM-001/013 sampled ranges. No houses, angles, Vertex or Fortune. | D04 | P2, P4 | Open |
| E05 | **Planet target for R1.0: system barycentre or physical centre** | **Revisit D01 for R1.0:** ship the default `reference` (barycentre) profile, with the target disclosed per result. The Sun and Moon are unaffected. The outer-planet difference is about 0.1″ or less (an order-of-magnitude estimate from published satellite masses and orbits, not a qualification result), far below what astrologers read, and it avoids **about 2.18 GB** of satellite kernels in deployment. Keep `planet-centres-v1` opt-in and make it the default later, once its data size is reduced. If D01 is kept, add data subsetting to P6. | D01 | P1 | Open |
| E06 | **Apparent versus geometric defaults** | Preserve today's semantics: charts are apparent; activation/series are geometric ("true positions"). Mappings are explicit per route. | D06 | P7, P8 | Open |
| E07 | **Point definitions** (nodes, Lilith, Vertex, Fortune) | True node = osculating, from the DE Moon state. Mean node and mean Lilith = cited mean-element polynomials. Fortune = sect-aware by default, with an "always-day" variant matching the current app option. All on the ecliptic and equinox of date, with a definition version in the output. | D02 | P2 | Open |
| E08 | **Placidus where undefined** | Return `unavailable` with a reason above the polar circles. The app offers the user an explicit choice (for example Whole Sign) that is recorded in the chart. Never substitute a system silently. | D12 | P3 | Open |
| E09 | **Future dates beyond the leap-table expiry (2027-06-28) and the EOP prediction window** | Transits, clock and future charts use a labelled non-strict time model (no future leap seconds assumed; modelled ΔT) and carry a quality flag. Release a data refresh at least every six months, with an expiry alarm in monitoring. | D03 | P4 | Open |
| E10 | **Service topology and transport** | A persistent private Python worker behind the existing Express API. A small local HTTP/JSON server (`ariaephemeris serve`) on a private network or Unix socket, one per container, horizontally scaled. No public exposure, no process-per-request. | D08 | P6 | Open |
| E11 | **Performance targets** | Warm chart p95 < 250 ms through the service. A 10-body × 10,000-epoch batch < 10 s. The clock holds 1 Hz without overlap at the declared concurrent-user load. Measured on the intended host; the actual app workloads are recorded in P1. | D10 | P5 | Open |
| E12 | **Acceptance tolerances and evidence tiers** | Adopt the two tiers. Release-grade gates are the RM-001 D07 proposal: raw position 1 m / velocity 1 mm/s, apparent direction 1″, rate 0.0001°/day, angles/cusps 1″, well-conditioned events 10 s, each against an independent reference. The SE shadow-diff is diagnostic, never a gate. | D07 | P1 | Open |
| E13 | **Rust or native core** | Not for R1.0. Reconsider only if the E11 targets are missed after the P5 Python optimisation. | D09 | P5 | Open |
| E14 | **Unsupported options in the UI** | Disable them with "coming soon" and a capability reason. A saved chart that used one shows `unavailable` for that item and keeps the setting. | D12 | P7 | Open |
| E15 | **Cutover and rollback** | Per-endpoint feature flags during the pilot. SE stays in *non-production* builds for shadow comparison only. For R1.0, SE is removed from the production build, and rollback means returning to the previous qualified **Aria** release, not to SE. While SE is still shipped, keep its licence obligations satisfied. | D14 | P7–P9 | Open |
| E16 | **Data distribution and disclosure** | JPL kernels downloaded at build/deploy with checksum verification and never bundled in the wheel. Per-result provenance (dataset, engine, conventions). Shipped-notice review in P9. | D13 | P6, P9 | Open |
| E17 | **Historical range (for example down to 1700)** | **Not in R1.0.** Post-1.0 "research mode" with JPL DE440/DE442 full (about 1550–2650): planets only and a labelled ΔT model. Pre-1900 natal charts and DE441 deep cycles come later. Keep the data registry able to swap kernels from R1.0 onwards. | D11 | P1 (confirm) | Open |
| E18 | **Community model** | Apache-2.0 (already in place); Developer Certificate of Origin sign-off rather than a CLA; Contributor Covenant code of conduct; owner as initial maintainer, adding maintainers by documented nomination. | — | P10 | Open |
| E19 | **Public release and visibility** | Make the repository and package public at milestone M5, after R1.0. Earlier visibility (for example, opening the repo in read-only form at M3) is optional and needs explicit owner authorisation. | — | P11 | Open |
| E20 | **Working vocabulary** | Adopt the agile vocabulary and two evidence tiers above. Keep the mandated status values unchanged. Update the prompt template to the story format when authorised. | — | P1 | Open |

## Progress setup

The sibling [progress.md](progress.md) holds the dated baseline and evidence, and the
[prompt register](prompts/README.md) holds the stories. No stories have been generated
yet. Generate one bounded story (prompt) at a time when the owner requests it.
