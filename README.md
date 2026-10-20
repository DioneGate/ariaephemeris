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

Time inputs accept explicit UTC, TT, TDB or UT1 and two-part Julian dates. Unresolved DST folds/gaps are rejected. Strict chart calculations require supplied DUT1 or delta-T; strict topocentric calculations also require polar motion. Pre-1972 civil UTC is rejected; use explicit TT or UT1. Future UTC beyond the pinned leap-table expiry is rejected in strict mode. Non-strict assumptions are reported in metadata. See [conventions](docs/conventions.md).

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
