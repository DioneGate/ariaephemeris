# RM-001/001 — Commercial calculation contract, capability inventory and reproducible baseline

| Field | Value |
| --- | --- |
| Roadmap | [RM-001 — Engine development and commercial application readiness](../README.md) |
| Phase | RM-001-P1 — Scope, calculation contracts and reproducible baseline |
| Generated/reviewed | 2026-11-18 |
| Baseline | Aria Ephemeris `main` [22b8cdf](https://github.com/DioneGate/ariaephemeris/commit/22b8cdfc321dccf05d2683e57728e8e49897f830), package 0.1.0; Aria Galaxy application `main` [4ab5f99](https://github.com/DioneGate/archetypal-activation/commit/4ab5f99f277d9c9a221bcf911a820fd9eda50972) |
| Dependencies | Existing v0.1.0 engine, available application contracts, and read-only access to both repositories. Owner decisions on launch scope, acceptance limits and service topology remain open. |
| Delivery status | **Planned** in the [prompt register](README.md): this document is prepared, not executed. |
| Authority | Prompt preparation only. Future execution needs separate authorisation; no change to the application repository is authorised. |

Read [AGENTS.md](../../../../AGENTS.md), the [RM-001 roadmap](../README.md), [progress evidence](../progress.md) and the [prompt template](../../../templates/implementation-prompt.md) before proceeding. Revalidate the actual heads of both `main` branches at execution; the SHAs above establish the **prompt-authoring baseline**, not a perpetual code freeze. Preserve unrelated and newer work. The task is a bounded **P1 documentation, compatibility and evidence increment**, not implementation of a replacement calculation engine.

## Objective and expected behaviour

Produce a traceable, reviewable contract for Aria Ephemeris as the potential **sole declared astronomical provider** of an explicitly selected commercial Aria Galaxy/Aria Astrology launch scope. Inventory what exists on both sides, document numerical/API differences, propose launch versus beta/deferred boundaries, and reproduce the existing baseline where inputs and tooling are available.

The outcome is an actionable gap/decision register and independently reviewable numerical-qualification plan. **Do not** assert provider compatibility, full P1 completion, release readiness, or accuracy beyond the cited measurements merely because an inventory or prompt exists. No application runtime behaviour changes in this increment.

## Verified current state

### Engine — checked at Aria Ephemeris `22b8cdf`

- `pyproject.toml` packages Python 3.12+ `ariaephemeris` v0.1.0 with NumPy, PyERFA and jplephem; `README.md`, `src/ariaephemeris/engine.py` and `models.py` expose offline Python/JSON CLI positions, batch, chart, aspects and bounded events.
- `src/ariaephemeris/models.py` provides Sun, Moon, Mercury, Venus and **Mars–Pluto planetary-system barycentres**; Earth is an available reference/heliocentric target. `docs/conventions.md` declares actual target IDs, origins, frames, rates and time rules.
- Source is pinned, hash-verified JPL DE442 short; the **operationally qualified** interval is 1900-01-01 through 2100-12-31 TT, not a guarantee of civil-time availability. Pre-1972 civil UTC is rejected; the pinned strict UTC leap table expires 2027-06-28. Strict Earth-rotation/topocentric inputs are required as documented.
- Equal/whole-sign houses and chart axes exist; no public standalone expanded house/angle-rate contract, selected node/apogee/Vertex/Fortune implementations, Placidus, Lahiri, or minor-body coverage is established by v0.1.0.
- `docs/validation/README.md` and `qualification-0.1.0.json` record *historical* agreement sampling (4,712 epochs per supported target and 680 events in 39 windows), not a freshly rerun qualification or physical model-uncertainty bound. Recorded warm ten-body median: 77.4 ms; ten-body 10,000-epoch batch: 67.63 s on a shared host, not the proposed deployment SLA.
- `docs/architecture.md` describes a library and CLI; a persistent private HTTP service and application adapter are **not** currently delivered.

### Application — read-only inspection at `4ab5f99`

- `backend/server.ts`, `backend/src/api/routes/swephRoutes.ts` and `backend/src/api/controllers/swephController.ts` serve `GET /api/v1/health`, `GET /api/v1/bodies`, `POST /api/v1/ephemeris/latitudes` and `/range` through the native sweph module. The range API defaults to Swiss/true positions; its concurrency, cancellation, maximum-points and response metadata must be captured.
- `frontend/main-app/src/engine/ephemeris/contracts.ts` and `swephApiAdapter.ts` provide a client-facing `EphemerisAdapter` for snapshots/series, with `lon`, `lat`, nullable `speedLon`, Julian-day UT metadata and a `major` preset. `seriesCache.ts` includes a provider/flag-sensitive UTC grid cache; inspect all cache identities and consumer call sites.
- `frontend/main-app/src/engine/activation/` derives activation curves from longitude series **in the browser**. This is an application model/policy, not a requirement to replicate those orbs, aspects or activation formulae inside Aria Ephemeris.
- `backend/src/api/routes/horoscopeRoutes.ts` and `backend/src/services/horoscope/chartService.ts` calculate charts directly with sweph; this path is **not** covered just by changing the frontend series adapter.
- `packages/horoscope/src/contracts.ts`, `chartAnalysis.ts` and `registry.ts` define versioned ChartRequestV1 / ChartSnapshotV1 / ChartCapabilitiesV1, ChartDataV1, AspectPolicyV1, ChartAnalysisV1, WheelSettingsV4 and portable documents. In the current schema, `ChartCalculationOptionsV1.ephemeris` is literally `'swiss'` and chart provenance/provider is literally `'swiss-ephemeris'`: an Aria migration **needs an explicit compatible/versioned schema decision**, not fabricated Swiss provenance.
- `docs/horoscope-wheel/data-contract/README.md` declares **tropical, geocentric, apparent, Equal houses, no automatic house fallback, sect-dependent Fortune** as chart defaults. It also supports Lahiri sidereal, Placidus, nodes, mean Lilith, Vertex, Fortune and optional minor bodies; the activation range API has its distinct true-position defaults. Chart dates are accepted under a proleptic-Gregorian 0001–2999 contract with historical DST/UT behaviour that does **not** equal the current engine's civil-time coverage.
- `backend/src/services/horoscope/time.ts` resolves IANA local times with explicit DST gap/overlap handling. Preserve civil-time semantics, local seconds/offsets and unknown-time policy; do not assume a UTC-only API is a drop-in replacement.
- `packages/horoscope/src/registry.ts` declares major planets, minor bodies, calculated points, axes and an eclipse event marker. Registry presence does not prove available numerical data.
- `docs/architecture/current-state.md` describes the historical-event PostgreSQL context separately from astronomical calculation. Do not confuse astronomical event searches with the historical-event catalogue.

Source notes above describe inspected files, **not** executed end-to-end application behaviour. Source links should be retained in deliverables, with line/function anchors where practical. Review new application changes at execution time.

## Scope and exclusions

**In scope — documentation and evidence only:**

1. A read-only source-to-consumer inventory of backend ephemeris and chart entry points, frontend adapters, caches, clock/Time Explorer, bi-wheel/radix/transits/synastry, position table, aspect matrix, saved chart/document pathways and activation series. Mark direct versus inferred call paths.
2. A target/capability matrix distinguishing engine implementation, engine qualification, application feature demand, chosen MVP support, product impact, owner and proposed delivery phase.
3. A proposed common calculation contract: identity, frames, time, units, rates, failures, provenance and feature availability.
4. A proposed commercial launch/beta/deferred matrix and decision log with unresolved owner choices.
5. A repeatable baseline run/check log, with explicit pass/fail/skip/not-run evidence and measured limitations.

**Out of scope:** new astronomical algorithms; new code/tests, endpoints, adapters or schemas; Placidus/nodes/minor-body/historical time implementation; service/container rollout; Python/Rust rewrite or optimisation; licence rework; application repository edits; provider switching or hidden fallback removal; production release/deployment; unapproved live-account or personal chart data access. Do not copy Swiss Ephemeris implementation/source into this repo. If test tooling needs changes, record a follow-up instead of expanding this task.

## Requirements

### R1 — Inventory both ends of the calculation path

Create `docs/roadmaps/001-engine-development/p1-capability-matrix.md` with a row per capability and at least these columns: canonical object/operation, application source/call path, current request/response and semantics, Aria API/source, implemented?, tested/qualified evidence, data/time coverage, mismatch, launch proposal, owner, follow-up phase, and validation fixture. Include the entire application object registry, **not only the ten major planets**; distinguish individually available, data-dependent, unimplemented and undefined points.

Map separately:
- single and ranged geocentric positions; signed rates, true/geometric versus apparent, observer/corrections and cache identity;
- chart calculation/capabilities, houses, axes/rates, house fallback, sect and Fortune, sidereal and optional points;
- birth-time resolution, chart/clock/Time Explorer ranges, Julian-day time scales, history, DST ambiguity, unknown time;
- chart layers, saved-chart/recalculation/provenance, aspect analysis (application-owned) and activation series (application-owned);
- bounded planetary search/events versus the separate PostgreSQL historical-event catalogue.

### R2 — Publish a numerical contract proposal, never an invented equivalence

Create `docs/roadmaps/001-engine-development/p1-calculation-contract.md` with an explicit table for:
- canonical name and physical **target ID/centre vs planetary-system barycentre** (including Mars–Pluto); accepted launch label or blocking mismatch; no silent substitution;
- observer origin, target centre, J2000/ICRS and of-date ecliptic/equinox choices; tropical/sidereal and selected ayanamsa only if supported;
- geometric and apparent flags/correction pipelines, deflection/aberration/light-time and topocentric horizon/sect semantics; chart defaults must remain distinct from activation defaults;
- UTC, UT1, TT, TDB, two-part Julian dates, local/IANA zone and fold/gap semantics, leap/EOP/delta-T input versions, expiry and uncertainty;
- longitude normalisation, latitude, distance AU, signed longitudinal/latitude/radial/ASC/MC rates and units/day basis; retrograde/stationary and absent-rate/null semantics;
- house systems, cusp 1–12 numbering, failure/fallback policies, node true/mean definitions, lunar apogee, Vertex/Fortune and source provenance;
- per-object availability, requested versus effective options, versioned output/provenance, immutable dataset hash/engine version, unsupported/invalid/degenerate errors and data gaps.

For every difference assign one classification: **matches as declared / definition differs / not implemented / unqualified / requires owner decision**. Numerical tolerance proposals must distinguish comparison on the *same target and conventions* from model or civil-time uncertainty. No byte-for-byte parity claims.

### R3 — Define an owner-decision-ready first commercial slice

Create `docs/roadmaps/001-engine-development/p1-launch-scope-and-decisions.md`. Propose a conservative 1900–2100 **tropical core** as a *candidate*, not an approved promise; resolve actual time/rate/centre limits. Group features into **launch**, **beta/optional**, and **deferred** with user-facing disable/error behaviour and saved-document handling. Include a decision table (question, recommendation, alternatives, impact, owner, approval state) covering at minimum:
1. whether the launch must cover current sidereal, Placidus, nodes, Lilith, Fortune, Vertex, minor bodies and chart modes, or may clearly disable those options;
2. how Mars–Pluto barycentre/centre mismatches are handled and qualified;
3. exact supported birth-date/time interval and pre-1972 / unknown-time policy;
4. versioned app provider/provenance contract and saved-chart migration/recalculation semantics;
5. representative accuracy limits, independent references and dataset/version identity;
6. Python-first service topology, workload/hardware/performance gates and a possible future measured Rust PoC;
7. whether wider historical range and specialist techniques are postponed.

Owner decisions remain **Open** unless explicitly approved; their existence must not be presented as sign-off. Identify which choices block P2/P3/P4 and which evidence work can proceed immediately.

### R4 — Reproduce only the existing baseline and document the qualification plan

Create `docs/roadmaps/001-engine-development/p1-qualification-baseline.md` recording checkout SHAs, Python/environment, package and JPL manifest/hash, pinned dependency versions, commands executed, actual outcomes, skips and failures, and comparison against committed historical reports.

Use synthetic/public fixtures (never account data). Define a proposed independent reference fixture set: representative TT/UTC dates inside and at supported boundaries; selected pre-1972 and leap expiry cases; DST overlap/gap; a geographic/equatorial and high-latitude chart; apparent/geometric chart-versus-timeline cases; stations and longitude-rate sign; barycentre/centre side-by-side where independent source targets exist; and unsupported requested options. Mark *comparison impossible or out of scope* rather than inventing outputs or thresholds.

Record the historical reference agreement in `docs/validation/README.md` accurately, including sampled-only limitations, and record the historical **67.63 s** ten-body 10,000-epoch batch as an unmet performance requirement until remeasured on target hardware. P5 should establish actual service-level targets; this prompt must not claim they are achieved.

### R5 — Evidence provenance and risk handling

- Link every matrix row to relevant engine/application code, schema or a labelled proposed requirement. Avoid treating narrative docs as more authoritative than current code.
- Do not infer planet-centre identity from a body label. Document actual physical target and comparison choices.
- Unknown bodies, unsupported house systems, ill-defined polar axes, missing EOP/time data, unsupported date range and unknown rates must have explicit error/unavailable semantics. No zero placeholders, stale positions, silent model substitution or unannounced Equal-house fallback.
- Preserve the application-owned aspect/orb and activation-function policies; Aria Ephemeris must not silently duplicate them.
- Distinguish accepted numerical difference, unqualified calculation, missing feature, deployment failure and UI limitation. No unsupported absolute/continuous error bound or universal event-completeness claim.
- Preserve Apache-2.0, existing MIT grants, all runtime/data licences and JPL provenance. No kernel binaries, private charts, credentials, modified source algorithms or large reference artefacts in Git.

## Compatibility and operations

Propose (do not implement) a provider-neutral calculation boundary in the **existing Aria Express backend**, backed by a private persistent Python worker/service with a pinned, verified read-only JPL kernel. Explicitly document why the frontend `EphemerisAdapter` alone does not cover the native chart service. Track API/version differences and a migration plan for `ChartRequestV1`, `ChartSnapshotV1`, `ChartCapabilitiesV1`, `ChartDataV1`, `AspectPolicyV1`, `ChartAnalysisV1`, saved documents and the activation DTO/cache.

Future integration proposals must address request budgets, cancellation, stale responses, bounded sampling, provenance-aware cache keys, diagnostics, worker restart, partial failures, identity-independent public calculation, privacy and rollback. User accounts, entitlements, personal chart storage and historical-event persistence stay in the application. **No direct runtime/service deployment or cross-repository change is authorised here.**

## Acceptance criteria

- [ ] Deliver the four P1 documents named above, cross-linked from this prompt, and record exact inspected heads and source evidence for both repositories.
- [ ] Inventory all current application astronomy entry points and distinguish frontend position-series adapter, native chart API, clock/Time Explorer and browser activation/aspect ownership.
- [ ] Map the full canonical registry with explicit unavailable/data-dependent/unsupported cases, including centre/barycentre compatibility and selected launch exclusions.
- [ ] Record a versioned calculation-contract proposal covering frames, corrections, time scales, units, rates, houses, errors, dataset/provenance and observer conventions.
- [ ] Capture differences between horoscope **apparent** and activation **true/geometric** defaults; never silently harmonise them.
- [ ] Propose launch/beta/deferred scope, user-visible unsupported-case behaviour, saved-chart compatibility and a decision owner for every outstanding gate.
- [ ] Identify numerical reference methods, fixture categories and *proposed* acceptance thresholds without claiming current parity or unsupported universal accuracy.
- [ ] Record reproducible commands, input hashes and actual pass/fail/skip/not-run outcomes. A missing real kernel must not count as qualification.
- [ ] Capture existing batch-performance shortfall and plan a measured Python-first profiling decision, without a native rewrite as a prerequisite.
- [ ] Preserve all code, generated runtime schemas and public application behaviour unchanged; no app-repo commit, release, deployment or provider switch.
- [ ] Record evidence in `progress.md`; register execution status separately in `prompts/README.md`. Keep RM-001-P1 Planned until the whole phase gate is accepted; do not mark RM-001/001 Done before verified acceptance **and** merge.

## Validation

**Preparation of this prompt (2026-11-18):** GitHub source/contract inspection only. No local tests, real-kernel checks, benchmarking, application integration or deployment were performed to prepare it.

**When separately authorised to execute RM-001/001**, use a clean checkout of the latest confirmed `main`; record the actual SHA before tests. Follow repository `README.md` and `AGENTS.md` and, if prerequisites permit, run:

```sh
python -m pip install -r requirements/development.lock
python -m pip install --no-deps -e .
ruff check .
ruff format --check .
mypy
python tools/audit.py
pytest -m 'not kernel'
python -m build
python tools/package_smoke.py
```

For real-kernel validation, explicitly install or provide the checksum-verified DE442s dataset, recording its hash; **only then** run:

```sh
ARIA_KERNEL=.artifacts/de442s.bsp pytest
python tools/datasets/qualify.py --kernel .artifacts/de442s.bsp --output .artifacts/qualification.json
python tools/datasets/qualify_oppositions.py --kernel .artifacts/de442s.bsp --output .artifacts/oppositions.json
python benchmarks/run.py --kernel .artifacts/de442s.bsp --output .artifacts/benchmark.json
```

Do not commit generated kernel, private data or large output files. A kernel download, licence issue or dependency problem is a recorded **blocker**, not a skipped passing gate. Compare against committed `docs/validation/qualification-0.1.0.json` and `benchmark-0.1.0.json` with identical conventions and honest hardware differences. Record CSPICE/Skyfield/standards-based sources used by existing reports; only requalify applicable measured targets and cases. If execution cannot run some commands, record **not run** with cause and owner. Do not claim successful execution from the planning-document PR.

Check document structure, table coverage, consistent IDs/links, no code changes and no unapproved changes to the application repository. No application build or end-to-end provider-acceptance test is required or implied by this documentation-only P1 increment.

## Delivery record

**Prompt authoring (2026-11-18):** created from the repository template after inspecting Aria Ephemeris `main` `22b8cdf` and Aria Galaxy application `main` `4ab5f99`. This is a planned task description, not an implementation or qualification result. Branch/PR authoring evidence is recorded in `../progress.md` and the prompt register; do not alter source code or app files while preparing this prompt.

**Future execution:** deliver only the agreed P1 documentation/evidence on a separately authorised branch and PR. Include exact tests/results, fixture/dataset identities, owner decisions remaining open, review and merge references. Mark the prompt **In review** once implementation and validation evidence are ready; mark **Done** only after acceptance and merge. A P1 prompt's completion is not the entire RM-001-P1 gate, and neither implies P2–P6 readiness or application deployment.