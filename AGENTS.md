# AGENTS.md — Aria Ephemeris agent instructions

## Purpose, product and authority

These instructions apply to AI coding agents working in `DioneGate/ariaephemeris`. The objective is to build and maintain **Aria Ephemeris** as an independently developed, accurately qualified, commercially usable astronomical calculation engine for the Aria Galaxy / Aria Astrology application, while keeping it useful as a standalone Python library.

This is a **numerical software and scientific data** project, not an astrology interpretation or UI project. Reuse working code and contracts. Verify claims with reproducible evidence. Preserve source provenance and licensing. Do not fabricate successful tests, performance gains, release readiness or deployment results.

Explicit user/session instructions take precedence. If documentation disagrees with verified code, describe the discrepancy rather than silently choosing. Do not assume discussion or a roadmap constitutes permission to implement code.

## Operating modes and permissions

Determine the requested mode before taking action:

- **Explore / assess:** inspect, explain, compare, recommend; **do not write files**.
- **Roadmap / prompt / documentation:** write only the specifically requested planning or documentation artefacts; **do not implement their proposed code**.
- **Implement:** change scoped code and tests on a dedicated branch and prepare a PR; **do not automatically merge, publish or deploy**.
- **Implement and merge:** merge only with explicit authorisation and passing required checks; record the actual merge evidence.
- **Release / deploy / publish:** requires separately explicit authorisation, including when a workflow would trigger side effects. A merged commit is not proof of a deployed or qualified release.

Never force-push, delete unrelated work, change credentials, modify repository visibility or automate production changes without explicit approval. Changes to the separate Aria Astrology repository require their own authorisation.

## Read first and establish the baseline

1. `README.md`, `docs/specification.md`, `docs/architecture.md`, `docs/conventions.md`, `docs/licensing.md`.
2. `docs/roadmaps/README.md`; for RM-001 read `docs/roadmaps/001-engine-development/README.md`, `progress.md`, and `prompts/README.md`.
3. The exact implementation prompt, if authorised, and `docs/roadmaps/templates/implementation-prompt.md`.
4. Relevant code under `src/ariaephemeris/`, `tests/`, `tools/datasets/`, `benchmarks/`, `schemas/` and the CI workflows.
5. `docs/validation/README.md` plus the exact qualification reports and kernel metadata when making a claim about accuracy or performance.

Verify the target branch and current commit, inspect existing functionality, and preserve newer changes before any implementation. Distinguish source inspection, historical qualification reports, newly executed checks and deployed evidence.

## Roadmaps, prompts and statuses

`docs/roadmaps/README.md` is the governing roadmap convention. RM-001 is already established in `docs/roadmaps/001-engine-development/`; **extend it, never create a duplicate RM-001 or renumber delivered history**.

For a new initiative, create `NNN-short-name/README.md`, `progress.md` and `prompts/README.md` from the existing templates, then register it in the roadmap index. IDs are repository-scoped: `RM-001-P1` for phases and `RM-001/001` for prompts. The same number in Aria Astrology is a different roadmap.

Generate one bounded implementation prompt at a time **only when requested**, using `docs/roadmaps/templates/implementation-prompt.md`. Include:

1. Objective and expected behaviour.
2. Verified current state.
3. Scope and exclusions.
4. Requirements, including numerical definitions and failure modes.
5. Compatibility and operations.
6. Observable acceptance criteria.
7. Actual validation to perform and independent references.
8. Delivery record, including branch/PR and evidence.

Use only **Planned, Ready, In progress, Blocked, In review, Done, Deferred**. The roadmap README owns phase status; the prompt register owns prompt status; progress.md owns evidence. A generated prompt is not implemented. A PR is In review, not Done. Done requires verified acceptance and merge; deployment and published package release are separate.

## Numerical correctness is the primary requirement

- Treat target identity (planet centre **versus planetary-system barycentre**), origin, coordinate frame, equinox/ecliptic, correction model and time scale as first-class, explicit parts of the calculation contract.
- The v0.1.0 baseline is JPL **DE442 short**, operationally qualified for **1900-01-01 through 2100-12-31 TT**; UTC, DUT1/polar-motion and Earth-rotation availability can impose narrower restrictions. Confirm real source coverage and data expiry before changing these statements.
- Do not silently substitute planetary centres for barycentres, invent missing points, clamp invalid dates, extrapolate outside qualified ranges, reuse stale output or silently switch models.
- Keep astronomical evaluation separate from astrological definitions (houses, nodes, points, aspect conventions), application presentation and user interpretation. The Aria Astrology chart-analysis engine owns its configurable aspect profiles; avoid duplicate policy decisions without an approved contract.
- Preserve scalar/batch consistency, signed longitude rates, correct circular-angle handling, event-root conditioning, time-quality metadata and explicit unavailable/undefined results.
- Choose documented independent mathematical references and exact conventions. Keep an algorithm-provenance trail, and version behaviour-changing APIs or numerical conventions.

Scientific qualification must distinguish **agreement with another implementation**, source-model uncertainty, uncertain historical civil time, error added by approximations/compression, and search-completeness limitations. A finite sample is not a continuous error guarantee. Do not compare results under mismatched conventions and label the difference a numerical defect.

## Data, independence and commercial licensing

- Use legally suitable JPL/NAIF sources and Aria-owned implementation; do not copy Swiss Ephemeris source, wrappers, proprietary data or text into this repository or generate derived models from restricted assets.
- Keep JPL datasets installed explicitly, immutable in ordinary calculation, checksum-verified, offline at runtime and identified in output/manifests.
- Maintain applicable `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES`, provenance, source comments, dependency manifests and modification notices. Preserve earlier MIT grants and third-party terms.
- Do not commit downloaded production kernels, temporary generated packs, massive reference artefacts, secrets or personal birth/chart data.
- Treat observed Earth-orientation inputs, predicted/modelled values and missing data distinctly. Strict calculations must fail safely when required time information is unavailable.

## Engineering and performance strategy

- Preserve the supported **Python 3.12+ / NumPy / PyERFA / jplephem** engine and public Python/CLI contracts as the reference starting point; avoid broad rewrites merely to change language.
- **Profile before optimising**: time SPK evaluation, shared time/frame work, apparent corrections, Python allocation/serialisation, service transport and batch scheduling separately.
- Optimise duplicated work, batching, vectorisation, caching and operational budgets first. For Rust/native computation, write a bounded benchmarked proof of concept; adopt a native core only if measured benefits exceed integration and maintenance cost.
- A Rust prototype must preserve public contracts, data metadata and numerical definitions, and must pass independent qualification. Python should remain useful for validation and scientific exploration. **A Rust migration is not a commercial-launch prerequisite.**
- Report benchmark hardware, worker count, source hash, body count, time samples, correction modes, cold/warm cache state, p50/p95/throughput and memory. Proposed targets are not achievements.
- The initial integration is a **persistent private calculation worker/service behind the existing Aria Express API** unless a later approved design changes it. Avoid process-per-request startup, public exposure, unbounded searches and unnecessary external services.

## Development workflow

1. **Inspect** the verified branch/commit, affected source, historical results, relevant roadmap and prompt.
2. **Plan** the smallest useful increment with explicit scope, model decisions, compatibility, risk, failure cases and rollback.
3. **Implement** on a dedicated `feature/`, `fix/` or `docs/` branch. Preserve unrelated work, stable public APIs and exact dataset versions.
4. **Verify** appropriate checks. Typical commands (after installing the pinned development environment):
   - `ruff check .` and `ruff format --check .`
   - `mypy`
   - `python tools/audit.py`
   - `pytest -m 'not kernel'`
   - `python -m build` and `python tools/package_smoke.py`
   - With explicitly installed, checksum-verified dataset: `ARIA_KERNEL=.artifacts/de442s.bsp pytest`
   - For relevant numerical changes: `python tools/datasets/qualify.py --kernel .artifacts/de442s.bsp --output .artifacts/qualification.json` plus relevant supplementary checks.
5. **Review** source/data identity, accuracy, range boundaries, safe errors, security, notices, API compatibility, performance regressions and release artefacts.
6. **Deliver** with a scoped PR, actual commands/results, limitations and updated roadmap evidence. Merge and release only with the relevant authorisation.

Fast CI and **real-kernel qualification** are separate gates. Missing kernels, skipped tests or absent reference data never count as an accuracy pass. Execute tests that are available; state honestly which were not run and why. Use the existing qualification and benchmark scripts rather than asserting success from documentary review.

## Cross-repository integration and commercial release

Aria Astrology uses React/Node/Express and has existing chart-analysis, wheel, aspect-matrix, clock and activation workflows. Use a versioned, provider-neutral adapter; do **not** treat Aria Ephemeris as an automatic drop-in replacement for the application's current provider. Inventory actual calls, preserve chart/activation semantics (including apparent versus geometric calculations) and qualify every advertised body, point, house and date range.

Removing another ephemeris from the commercial application's production runtime requires **separately authorised changes and actual integration evidence in the application repository**. This engine's successful package tests do not prove that removal.

Before claiming commercial readiness, confirm: all declared launch capabilities pass appropriate real-kernel qualification; errors and missing data are explicit; supported date/time policy works end to end; the pinned service is secure and recoverable; performance/concurrency passes on intended hosting; actual shipped software/data terms are reviewed; and the deployed application uses the intended provider without an undeclared fallback.

## Definition of Done and final report

Report exactly what changed, paths, branch/commit/PR, commands actually run, results, kernel/version identity, numeric and timing tolerances, unresolved issues, authorisation boundaries, merge state and separate deployment/release state. Never call a roadmap phase Done from planning work alone.
