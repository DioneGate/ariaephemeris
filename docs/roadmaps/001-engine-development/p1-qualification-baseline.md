# RM-001-P1 — Qualification baseline, replay constraints and reference fixtures

**Recorded:** 2026-11-18 · **Execution mode:** RM-001/001 documentation/evidence, no algorithm changes · **Numerical rerun:** **NOT RUN — checkout and JPL kernel unavailable in this execution environment**. This document distinguishes historical committed qualification, newly inspected repository state and commands actually attempted. No assertion of new passing tests, end-to-end provider parity or production acceptance follows.

See [capability matrix](p1-capability-matrix.md), [calculation contract](p1-calculation-contract.md), [launch decisions](p1-launch-scope-and-decisions.md), [prompt](prompts/001-commercial-calculation-contract-and-baseline.md).

## 1. Exact inspected baseline and reproducibility inputs

| Item | Recorded source/state |
| --- | --- |
| Engine repo/head | `DioneGate/ariaephemeris` `main` [`36a9cec742e8248fdee599b7cf620b2b19d12cc7`](https://github.com/DioneGate/ariaephemeris/commit/36a9cec742e8248fdee599b7cf620b2b19d12cc7), including merged prompt PR #2 |
| Application repo/head | `DioneGate/archetypal-activation` `main` [`4ab5f99f277d9c9a221bcf911a820fd9eda50972`](https://github.com/DioneGate/archetypal-activation/commit/4ab5f99f277d9c9a221bcf911a820fd9eda50972); **read-only** source inspection |
| Engine package | v0.1.0, Python >=3.12, `numpy==2.5.3`, `pyerfa==2.0.1.5`, `jplephem==2.24` ([pyproject.toml](../../../pyproject.toml)) |
| Development/ref deps | `requirements/development.lock`; declared pytest 9.1.1, ruff 0.17.0, mypy 2.4.0, build 1.6.1, jsonschema 4.26.0; historical independent references Skyfield 1.55, SpiceyPy 8.2.0 (CSPICE), SciPy 1.18.1 |
| Kernel manifest | [`src/ariaephemeris/resources/de442s.json`](../../../src/ariaephemeris/resources/de442s.json), dataset `aria-de442-reference-v1`, JPL **DE442 short** `de442s.bsp` |
| Kernel declared size/hash | **32,701,440 bytes**, SHA-256 `54d97562a5b094d298b1b8eafa5a2e17e3e010ce85e1a366d07f003ad159323c` — source manifest only; **not re-verified against an installed kernel in this run** |
| Source/coverage | [Official NAIF `de442s.bsp`](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de442s.bsp); source coverage TDB JD 2396752.5–2506352.5; **qualified operating interval TT 1900-01-01–2100-12-31**, narrower than source interval |
| Time data | Strict pre-1972 civil UTC rejected; leap data expires 2027-06-28 (strict later UTC fails); strict charts require DUT1 or delta-T and topocentric strict additionally xp/yp |
| Existing qualification | [`qualification-0.1.0.json`](../../validation/qualification-0.1.0.json) and [validation narrative](../../validation/README.md), committed **2026-10-10**; **historical passed report**, not current test execution |
| Existing benchmark | [`benchmark-0.1.0.json`](../../validation/benchmark-0.1.0.json), shared-host measurements committed **2026-10-10**; **historical results**, not intended deployment-host SLA |
| Source rules | [AGENTS.md](../../../AGENTS.md), [conventions](../../conventions.md), [architecture](../../architecture.md), [licensing](../../licensing.md), [roadmap](README.md) |

The engine's own historical release report lists Python **3.12.14**, Linux-6.18.44-x86_64, AMD EPYC 9V74, NumPy 2.5.3, PyERFA 2.0.1.5, jplephem 2.24; reference stack Skyfield 1.55, SpiceyPy 8.2.0 and SciPy 1.18.1. This is **not** the present execution host (below).

## 2. Commands actually attempted on 18 November 2026

Observed working environment: **Python 3.13.5**, Linux 6.18.57 x86_64; no checked-out Aria Ephemeris source directory, no `de442s.bsp` in the accessible workspace. Import availability probe found `numpy`, `pytest`, `scipy` and `jsonschema`, but **not** `ariaephemeris`, `erfa`, `jplephem`, `ruff`, `mypy`, `build`, `skyfield` or `spiceypy`. This is a **different, unpinned environment**, so its packages cannot qualify the shipped engine.

| Command/check executed | Actual result | What it proves |
| --- | --- | --- |
| GitHub repository `search_commits`, `fetch_file` on both `main` branches | **PASS — read-only inspection** | Exact repository heads, prompt, source files and historical report/manifest contents were retrieved by connected GitHub access |
| `python -V` | **PASS: Python 3.13.5** | Host interpreter identity only; required pinned dev environment not installed |
| `uname -srmo` | **PASS: Linux 6.18.57 x86_64 GNU/Linux** | Host platform identity |
| `git ls-remote https://github.com/DioneGate/ariaephemeris.git HEAD` | **FAIL: `Could not resolve host: github.com`** | This isolated shell cannot clone the public repository through the network; this is not an engine test failure |
| Local source and kernel file probe | **BLOCKED: missing checkout and kernel** | No real-kernel calculation can run in this host |
| `python -c 'import importlib.util; ...find_spec(... )'` | **PASS: environment inspected**; engine and critical pinned deps absent | Dependency availability only, not numerical validation |
| GitHub historical qualification and benchmark read | **PASS — documentation retrieval** | Earlier measurement values and coverage; does **not** reproduce them |

**Not executed / not claimed as passes** (because no checkout/pinned environment/kernel): `python -m pip install -r requirements/development.lock`, `python -m pip install --no-deps -e .`, `ruff check .`, `ruff format --check .`, `mypy`, `python tools/audit.py`, `pytest -m 'not kernel'`, `python -m build`, `python tools/package_smoke.py`, `ARIA_KERNEL=.artifacts/de442s.bsp pytest`, `tools/datasets/qualify.py`, `qualify_oppositions.py`, and `benchmarks/run.py`. These are **NOT RUN**, not skipped passing cases. The source-retrieval/Markdown validation is independent of them.

**Blocker/owner:** a runner with repository checkout, compatible pinned Python/dependencies and verified JPL kernel is needed for an actual replay. Engineering/release owner should run the commands below and record independent artefact hashes and outcomes before any P1 numerical acceptance or P6 qualification claim. No secrets or personal birth data are necessary.

## 3. Historical qualification results — *not newly reproduced*

The committed [qualification narrative](../../validation/README.md) and report record **4,712** epochs **per each of ten existing supported targets** and **680 events in 39 declared year/type windows** (1900, 2000, 2099). Same-kernel raw states used CSPICE; independent Skyfield paths and chart geometry tests included explicitly matched corrections. Seed `20261010`; source SHA is the manifest hash above.

| Historical metric | Historical observed maximum | Historical gate | Status of this 18 Nov review |
| --- | ---: | ---: | --- |
| Same-target, same-kernel raw position difference | 0.0281328 m | 1 m | Reported passed on 10 Oct; **not rerun** |
| Raw velocity difference | 2.99054e-05 mm/s | 1 mm/s | Reported passed; **not rerun** |
| Matched-convention apparent direction | 4.794e-06 arcsec | 1 arcsec | Reported passed; **not rerun** |
| Matched signed longitude rate | 8.4152e-09 degrees/day | 0.0001 degrees/day | Reported passed; **not rerun** |
| ASC / MC chart angles | 0.000133431 arcsec | 1 arcsec | Reported passed for declared nondegenerate samples; **not rerun** |
| Well-conditioned event timing | 0.0414804 seconds | 10 seconds | Reported passed for 39 declared windows; **not rerun** |
| **Unmodified Skyfield** near-alignment discrepancy | **19.6634 arcsec** | Not part of matched-deflection acceptance | Intentionally documented mismatch; not hidden as passing |

Reference agreement under a deliberately identical target/model does **not** bound physical ephemeris source uncertainty, old birth-time uncertainty, true planet-centre offsets, topocentric EOP error or unsampled dates. A finite 39-window event scan does not prove completeness for arbitrary periods. Topocentric samples and alternate frames were not subjected to all of the broad geocentric gates. No Placidus, nodes, sidereal, Fortune, minor planets, centre/barycentre interchange or P4 application service was qualified by the 0.1.0 report.

### Historical performance — **launch capacity unproven**

| Benchmark | Historical value | Interpretation |
| --- | ---: | --- |
| First calculation with a new engine; OS cache not purged | 0.102 s | Not a reproducible disk-cold startup SLA |
| Warm ten-body median | 77.4 ms | Historical shared-host result; not P5 warm-chart p95 |
| Warm ten-body observed maximum | 121.0 ms | Historical, not a percentile/service call |
| Ten-body, **10,000-epoch batch** | **67.63 seconds** | **FAIL** earlier 2-second provisional batch target and also slower than proposed 10-second P5 target |
| Process peak RSS | ~42.9 MiB | Historical local process; not multi-worker deployment memory |

**Priority**: profile SPK calls, shared time/frame work, complete apparent correction, Python per-point object construction, serialisation, transport and cache/queue overhead on the target host before considering Rust. No Rust PoC or speed improvement has been performed. [Roadmap P5](README.md) requires approved workloads and measured concurrency.

## 4. Required independent fixture programme — proposed, NOT executed

Use synthetic or public factual timestamps/places only, without personal chart or user data. Fixture IDs are referenced in [the capability matrix](p1-capability-matrix.md).

| Fixture | Inputs / case | Expected validation method / result | Blocker or special policy |
| --- | --- | --- | --- |
| **F01** — dataset/time limits | TT at 1900-01-01, 2000-01-01, 2100-12-31 and immediately outside operating interval; separate UTC tests in supported years | Explicit inside/outside result, source target and immutable manifest, no out-of-range clamping | TT boundary and UTC/EOP validity are distinct; use exact split Julian dates |
| **F02** — ordinary local birth | `Europe/London` at a documented DST fold and gap; ordinary 2000 chart with supplied observation quality | Fold requires explicit earlier/later; gap rejected; resolved UTC offset/version visible | IANA/Temporal vs Python timezone data may differ; pin versions |
| **F03** — corrections / rate | Same Sun/Moon/Mercury UTC/TT epoch, apparent chart request versus native true-position activation; station cases | Independent CSPICE state + Skyfield/standard transformations, match *exact* aberration/deflection pipeline and TT-day signed rates | Never assume native `TRUEPOS` equals Aria geometric before explicit comparison |
| **F04** — houses/angles | Synthetic locations on equator, mid-latitudes and high latitudes near polar degeneracy; Equal and Whole Sign | Independent horizon/ecliptic intersections and cusp-number/antipode checks; null rate or undefined polar case must remain explicit | Placidus and ASC/MC rates not implemented as public qualified APIs |
| **F05** — historical/time quality | 1960 local birth, 1972 transition, strict UTC after 2027-06-28; unknown/imprecise event-time source | Pre-1972 and expired strict UTC produce declared error or approved uncertainty policy; unknown time must not get precise houses | P2 owner decision and Earth-rotation model missing; no retroactive modern UTC |
| **F06** — range/cache/performance | 10 bodies × 10,000 epochs plus shorter 512-chunk ranges, changing source hash/modes/targets | Scalar-vs-batch agreement; cache isolation; measured CPU/transport/p50/p95/RSS/concurrency and cancellation on intended host | v0.1.0 historical batch 67.63s; P5 controls SLA |
| **F07** — event roots | Ingress, station and aspect near longitude wrap and reversals, matched reference TT windows 1900/2000/2099 | Dense independent scan + root solve, count/timing and conditioning per declared windows | No global completeness guarantee; tangency/unconditioned roots unqualified |
| **F08** — physical centres vs barycentres | Mars–Pluto at selected epochs with centre SPK/Horizons source distinct from JPL DE442s barycentre | Same epoch/frame/observer/aberration; report per-body separation and rate difference, source uncertainties and coverage | **No physically matched comparison available from current Aria kernel alone**; cannot approve without additional source |
| **F09** — unavailable settings | Request Placidus, Lahiri, minor bodies, eclipse marker, out-of-range times and unknown bodies | Explicit structured unavailable/rejection with canonical ID and no substituted stale/zero result | Unsupported by v0.1.0; do not create placeholder implementations |
| **F10** — lunar/derived models | Mean/true node, south antipode, Lilith mean apogee, Vertex, sect/Fortune day/night | Independent definitions, rates, polar cases, day/night formula, availability and source provenance | Not implemented; requires P3, cannot be qualified in current run |
| **F11** — application integration | Single, reference, transit, bi-wheel, synastry, clock ticks, Time Explorer steps, saved/imported V6 requests and AspectPolicyV2 | One accepted coherent snapshot per layer; no stale result, no unknown provider, saved inputs consciously recalculated, activation model retained | No P4 service/provider changes authorised or run in P1 |

**Sampling discipline:** record seed, timestamps, exact input JSONs, source SHA256, target ID, origin, frame, time conversions, correction modes, observation/EOP quality, expected error/tolerance and algorithm references. Report maxima/RMS/p95 for justified statistics, including known outliers instead of discarding them. Always distinguish *comparison error*, *physical source-model uncertainty*, *approximation error*, *historical civil-time uncertainty* and *search completeness*. A comparison lacking the required physical centre/reference or identical conventions must be marked **not comparable**, not a pass.

## 5. Replay procedure for an authorised, network-enabled runner

**Prerequisites:** clean checkout at the recorded `main` SHA (or update to latest head and document drift), Python >=3.12 with pinned development dependencies, available disk/memory and a deliberate download/verified local installation of the immutable DE442s kernel. Do not commit the kernel or outputs.

```sh
# From the clean ariaephemeris checkout:
python -m pip install -r requirements/development.lock
python -m pip install --no-deps -e .
ruff check .
ruff format --check .
mypy
python tools/audit.py
pytest -m 'not kernel'
python -m build
python tools/package_smoke.py

# Explicit verified data acquisition; check installer output and SHA256
ariaephemeris install-data .artifacts
sha256sum .artifacts/de442s.bsp
# must equal 54d97562a5b094d298b1b8eafa5a2e17e3e010ce85e1a366d07f003ad159323c
ARIA_KERNEL=.artifacts/de442s.bsp pytest
python tools/datasets/qualify.py --kernel .artifacts/de442s.bsp --output .artifacts/qualification.json
python tools/datasets/qualify_oppositions.py --kernel .artifacts/de442s.bsp --output .artifacts/oppositions.json
python benchmarks/run.py --kernel .artifacts/de442s.bsp --output .artifacts/benchmark.json
python tools/datasets/release_report.py --primary .artifacts/qualification.json --oppositions .artifacts/oppositions.json
```

Preserve the full command exit codes and output summaries including skipped tests, pinned versions and artefact hashes. Check reference model/deflection assumptions before comparing to the historical JSON. Kernel-dependent qualification is blocked if dataset hash is absent or mismatched; ordinary unit tests skipping kernel cases are not evidence of passing numerical qualification. **Do not** overwrite historical reports or change code under RM-001/001. Store transient output outside Git, link CI/runner logs in the progress record, and obtain separate authority for any actual implementation fix.

## 6. Result boundary and follow-up

**Verified this increment:** exact committed code/document evidence, target/body registry, application capability and provider mismatches, the pinned JPL manifest, historical qualification/benchmark values, and the inability to replay the kernel on this host. The four P1 documents constitute a *source-based planning and evidence delivery*, **not** newly independently reproduced numerical results.

**Not verified:** real-kernel arithmetic on the current head, same-target application numerical parity, current native source fallback behaviour under real data, complete astronomy provider migration, P5 service performance, live birth-time resolution, licensing of a finished deployed bundle or customer-visible acceptance. These gates remain outstanding. An engineering owner must perform an actual checkout+kernel replay on an appropriate runner before numerics are claimed current or RM-001-P1 can be accepted.
