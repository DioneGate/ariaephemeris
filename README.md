# Aria Ephemeris

Aria is an offline Python library for JPL-based planetary positions and initial astrology calculations. Its Apache-2.0 licence permits use in a closed-source commercial astrology suite. The calculation engine contains no Swiss Ephemeris code, wrapper or Astrodienst data.

Version 0.1.0 implements Sun, Moon, Mercury, Venus and the Mars–Pluto system barycentres, apparent/geometric positions, geocentric/heliocentric/topocentric origins, batch calculations, angles, equal and whole-sign houses, configurable aspects and bounded ingress/aspect/station searches. Target IDs and all conventions are included in results. Earth is available as a heliocentric body.

The pinned full-precision DE442 short kernel is 32,701,440 bytes. Operations cover **1900-01-01 through 2100-12-31 TT**; UTC and Earth-rotation data have narrower validity. See [measured qualification](docs/validation/README.md) before interpreting accuracy claims. Empirical reference agreement does not establish absolute astronomical accuracy or a continuous mathematical error bound.

## Install and run

Python 3.12 or later is required. From this repository:

```bash
python -m pip install .
ariaephemeris install-data .artifacts
ariaephemeris positions --kernel .artifacts/de442s.bsp --request examples/positions.json
ariaephemeris chart --kernel .artifacts/de442s.bsp --request examples/chart.json
ariaephemeris batch --kernel .artifacts/de442s.bsp --request examples/batch.json
ariaephemeris aspects --kernel .artifacts/de442s.bsp --request examples/aspects.json
ariaephemeris events --kernel .artifacts/de442s.bsp --request examples/events.json
ariaephemeris dataset-info --kernel .artifacts/de442s.bsp
```

Only `install-data` contacts the source, explicitly downloads the pinned kernel and verifies its SHA-256. Supply `--source /path/to/de442s.bsp` to install from an existing file. All calculations then work offline; no personal chart data is sent to a service. JSON requests may also come from stdin with `--request -`. Invalid requests return structured error JSON to stderr and exit code 2.

```python
from ariaephemeris import Ephemeris, Observer, PositionRequest, TimeInput

with Ephemeris(".artifacts/de442s.bsp") as engine:
    request = PositionRequest(TimeInput(jd=(2451545.0, 0.0), scale="TT", delta_t_seconds=64.0))
    positions = engine.positions(request)
    chart = engine.chart(request, Observer(51.5, -0.1), house_system="whole_sign")
    print(positions.to_dict())
    print(chart.angles_deg)
```

Time inputs accept explicit UTC, TT, TDB or UT1 and two-part Julian dates. Unresolved DST folds/gaps are rejected. Strict chart calculations require supplied DUT1 or delta-T; strict topocentric calculations also require polar motion. Pre-1972 civil UTC is rejected by default; use explicit TT/UT1 or opt in to the versioned historical civil-to-UT1 approximation. IANA timezone rules use checksum-pinned tzdata 2026.6 (2026f), independently of the host database. Approximate/unknown times retain quality metadata and cannot produce precise houses/angles. See [civil-time policies](docs/time-policies.md). Future UTC beyond the pinned leap-table expiry is rejected in strict mode. Non-strict assumptions are reported in metadata. See [conventions](docs/conventions.md).

## Opt-in physical planet-centres (WP4 preview)

The original `reference` calculation profile remains the **default**, including its explicitly identified Mars–Pluto **system barycentres**. The separate `planet-centres-v1` profile uses physical centres for Mars (499), Jupiter (599), Saturn (699), Uranus (799), Neptune (899) and Pluto (999). Its numerical source profile and observed dataset SHA-256 are recorded in every physical-profile response. **This profile has not been approved for commercial release.**

Download the **original** relevant JPL satellite SPK files from the [NAIF source directory](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/) separately, retain their original filenames/comments, and provide their local paths explicitly. The engine verifies each file's exact byte count and SHA-256 against the versioned `resources/planet-centres.json` manifest; it does not download new data during calculations. For a complete default all-bodies chart, all six files are required (around 2.18 GB in total); missing physical-centre sources are an error, never a barycentre fallback.

For example, once the pinned original JUP349 source is installed:

```python
from ariaephemeris import Ephemeris, PositionRequest, TimeInput

t = TimeInput(jd=(2451545.0, 0.0), scale="TT")
with Ephemeris(
    ".artifacts/de442s.bsp",
    centre_kernels={"jupiter": ".artifacts/planet-centres/jup349.bsp"},
) as e:
    result = e.positions(PositionRequest(t, bodies=("jupiter",), profile="planet-centres-v1"))
    assert result.bodies[0].target_id == 599
    print(result.metadata["physical_centre_sources"]["jupiter"]["source_sha256"])
```

The same opt-in profile is accepted by `positions`, `positions_batch`, `chart`, `raw_state(..., profile="planet-centres-v1")`, and event searches via `EventRequest(profile="planet-centres-v1")`. For the CLI, repeat `--centre-kernel BODY=FILE` for each required source and set `"profile": "planet-centres-v1"` in the JSON request. A partial source installation is possible for targeted testing, but requests requiring an omitted body **fail explicitly**. None of these options changes the default provider or Aria Galaxy.

For independent external comparison of the opt-in physical-centre profile, see the [WP5.4 tropical longitude, latitude and signed-rate qualification report](docs/roadmaps/001-engine-development/p1-wp54-tropical-coordinate-qualification.md). It uses 186 externally anchored geocentric apparent chart cases, including stations and zodiac ingresses, but **does not yet qualify a commercial accuracy guarantee**; this is [draft PR #12](https://github.com/DioneGate/ariaephemeris/pull/12), not a published release.

A separate [WP5.5 event-time comparison](docs/roadmaps/001-engine-development/p1-wp55-independent-event-timing.md) measures 22 independently sourced JPL Horizons planetary stations, tropical ingresses, conjunctions and oppositions. Original JPL reference samples and additional ±15-second source checks confirm each **observed** root crossing neighbourhood, but **not global event discovery, absolute observational time uncertainty or commercial release accuracy**. The evidence is on [PR #13](https://github.com/DioneGate/ariaephemeris/pull/13) and does not change the production event algorithm.

The source files have passed checksum/segment and same-source CSPICE evaluator checks. **Independent physical-model uncertainty, overall chart accuracy, data redistribution, commercial performance, and application parity remain separate gates.** See [numerical conventions](docs/conventions.md) and [RM-001 source results](docs/roadmaps/001-engine-development/p1-centre-source-feasibility.md).

## Current limits

Sidereal ayanamsas, lunar nodes/apogees, minor bodies, additional houses, eclipses, compact packs, HTTP and browser/native runtimes are planned. They are not approximated by placeholders. Compact pack size targets remain unmeasured. Apparent longitude rates use a documented, independently checked five-point derivative of the complete correction pipeline; geometric rates use source velocity and frame motion.

Event searches split brackets at rate extrema, include endpoints and report conditioning, budgets and cancellation. The reference report records tested completeness windows; arbitrary intervals are not guaranteed complete by a formal proof. Ill-conditioned contacts carry no universal timing guarantee.

## Development roadmap

See the [roadmap register](docs/roadmaps/README.md) for phased development plans,
status conventions and reusable templates. The first roadmap covers
[engine development and commercial application readiness](docs/roadmaps/001-engine-development/README.md).
Its phases remain Planned; delivery prompts will be created when requested.

## Development and licences

```bash
python -m pip install -r requirements/development.lock
python -m pip install --no-deps -e .
ruff check .
ruff format --check .
mypy
pytest -m 'not kernel'
ARIA_KERNEL=.artifacts/de442s.bsp pytest
python tools/datasets/qualify.py --kernel .artifacts/de442s.bsp --output .artifacts/qualification.json
python tools/datasets/qualify_oppositions.py --kernel .artifacts/de442s.bsp --output .artifacts/oppositions.json
python benchmarks/run.py --kernel .artifacts/de442s.bsp --output .artifacts/benchmark.json
python -m build
```

Missing kernels explicitly skip ordinary integration tests and **do not** qualify a release. The dedicated qualification command fails if its kernel is missing or any gate fails. CI separates those outcomes.

Redistributors retain [LICENSE](LICENSE), relevant [NOTICE](NOTICE), modification notices and applicable third-party/data terms. No compulsory UI badge is imposed. Apache-2.0 permits commercial use by both the author and others. Earlier MIT grants remain effective and are preserved. See [licensing](docs/licensing.md) and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES).

Further documentation: [specification](docs/specification.md), [implementation prompt](docs/implementation-prompt.md), [architecture](docs/architecture.md), [algorithms](docs/algorithms/README.md), [contributing](CONTRIBUTING.md), [changelog](CHANGELOG.md).
