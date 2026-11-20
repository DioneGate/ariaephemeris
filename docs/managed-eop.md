# Managed Earth orientation — RM-001/012

Managed data is optional and explicitly installed/selected. It provides missing DUT1 (UT1−UTC, seconds) and polar motion x/y (arcseconds) for modern UTC charts and topocentric calculations. Without it, the existing explicit DUT1/delta-T/polar-motion contract remains unchanged.

## Install and select

```bash
ariaephemeris install-eop .artifacts/eop
# Or restore the exact original snapshot from your controlled archive:
ariaephemeris install-eop .artifacts/eop --source /path/to/finals2000A.all
ariaephemeris chart --kernel .artifacts/de442s.bsp --eop .artifacts/eop/iers-usno-finals2000a-20261120-v1.all --request examples/chart-eop.json
```

```python
from ariaephemeris import Ephemeris, Observer, PositionRequest, TimeInput

with Ephemeris(
    ".artifacts/de442s.bsp", eop_path=".artifacts/eop/iers-usno-finals2000a-20261120-v1.all"
) as engine:
    chart = engine.chart(
        PositionRequest(TimeInput("2000-01-01T12:00:00Z")),
        Observer(51.5, 0),
    )
    print(chart.angles_deg)
    print(chart.metadata["time"]["quality"]["earth_orientation"])
```

The installer obtains and verifies the original full file, never modifies it, never overwrites an already installed corrupt file and never updates at calculation time. Engine construction verifies the complete selected source. `dataset-info --eop ...` reports the manifest. A later upstream revision must fail the old checksum; restore the pinned archive or deliberately review a new manifest, never replace the expected hash merely to make an install pass. Keep an original archive outside temporary build environments; CI source artefacts have finite retention.

## Pinned source and coverage

Snapshot `iers-usno-finals2000a-20261120-v1`, acquired 20 November 2026, is 3,779,176 bytes with SHA-256 `9f01acb5a8b50465913ad423212d409f309e4a7b9401197a52fe258304417fb0`. Its 20,052 complete daily records cover 2 January 1973 to 26 November 2027; additional date-only placeholders are unavailable data. Observed Bulletin A values end at 19 November 2026, 00:00 UTC; subsequent bracketing intervals can require predicted values.

Default policy rejects needed predictions. `allow_predicted_eop=True` / `--allow-predicted-eop` opts in, warns and labels affected quantities. This version limits predictions to requested epochs **before 20 December 2026, 00:00 UTC**, 30 nominal days after the first prediction. The raw file's longer prediction horizon is not implicitly enabled. Validity is assessed against the requested epoch, preserving historical reproducibility independently of the host clock. Old measurements do not expire just because a new snapshot exists.

There is no extrapolation or clamping. Missing days, endpoints needing unavailable derivative stencils and expired predictions are structured failures even with non-strict astronomical mode. The separate leap-table and engine TT coverage checks still apply. Selecting managed data is not permission to fall back to modelled rotation after an EOP failure.

## Time scales and field precedence

UT1−UTC jumps at a leap second. Aria subtracts TAI−UTC at each source node, interpolates continuous UT1−TAI on the continuous TAI timeline, then restores the appropriate TAI−UTC at the requested epoch. Polar motion uses the same elapsed-SI-second fraction. This avoids a spurious half-second DUT1 drift on a leap day.

A caller's DUT1 or delta-T wins over managed UT1; caller polar coordinates win individually. Missing polar coordinates may be filled independently for topocentric requests. If all required values are supplied, no unrelated managed lookup is made. Geocentric positions do not acquire an EOP dependency merely because a snapshot is installed. Managed lookup requires an actual modern UTC epoch; explicit TT/UT1 and `historical-ut1-v1` requests retain their explicit rotation contract and must supply polar motion when needed. No historical UTC is inferred.

Topocentric rates and observer velocities reevaluate EOP at shifted epochs. Derivative stencils must remain inside permitted source/prediction coverage. Geocentric chart rates shift TT without unrelated Earth-rotation lookups. The existing approximate/unknown-time restrictions remain in force.

## Quality and limits

Original I/P flags are retained as observed/predicted statuses for UT1 and polar motion separately. The I flag denotes IERS rapid Bulletin A values; these are provisional estimates, not a claim of final Bulletin B accuracy. Only needed fields determine whether prediction permission is required.

Output includes dataset/hash, selected daily nodes, TAI interpolation fraction, values, statuses and `applied` fields. Supplied fields are preserved in the request/observer. Formal errors at contributing source nodes are recorded in their original units, not converted into an unverified combined sigma or physical accuracy bound. Absolute Earth-rotation uncertainty remains null. Celestial pole offsets dX/dY and Bulletin B columns are **not applied**; the existing IAU 2006/2000A model remains the frame convention. ASC/MC retain the existing GST plus geodetic latitude/longitude geometry: managed UT1 enters that calculation, but polar motion is applied to topocentric observer states, not to the v1 house/angle geometry. Its independent reference uses the same declared angle convention; this is not a full physical local-horizon accuracy guarantee.

The independent qualification compares all parsed rows with Skyfield 1.55, samples 82 off-grid UTC instants and 246 observer cases, and records DUT1/polar interpolation, vector-plane ASC/MC and WGS84 observer-state differences. Skyfield's observer velocity omits some small derivative terms, so that residual is explicitly retained. These finite, same-source comparisons do not establish physical time accuracy or approve commercial tolerances.

Sources: [USNO product](https://maia.usno.navy.mil/products/bulletin-a.htm), [original source](https://maia.usno.navy.mil/ser7/finals2000A.all), [official column format](https://maia.usno.navy.mil/ser7/readme.finals2000A), [IERS Rapid Service/Prediction Centre](https://www.iers.org/iers/en/organization/productcentres/rapidservicepredictioncentre/rapid). The unchanged format description is archived under `docs/data/`; small unchanged original source lines with provenance are in `data/fixtures/iers/`. Acknowledge the IERS Rapid Service/Prediction Centre (USNO); no endorsement is implied.
