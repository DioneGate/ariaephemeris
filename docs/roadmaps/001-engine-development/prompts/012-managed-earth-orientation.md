# RM-001/012 — Managed Earth-orientation data

| Field | Value |
| --- | --- |
| Roadmap | [RM-001](../README.md) |
| Phase | RM-001-P2 |
| Generated/reviewed | 2026-11-20 |
| Baseline | main `633939aa6b776493e55fd5f01b8a309176ca9f69`, merged PR #16 |
| Authority | Owner requested implementation; PR delivery, no merge/release/deployment |
| Dependencies | 011 civil policies and pinned leap table; existing ASC/MC and topocentric pipeline |

## Objective and expected behaviour

For explicitly installed and selected modern UTC Earth-orientation data, supply missing DUT1 and polar motion to strict charts/topocentric requests. Return source/quality identity; reject missing, invalid, out-of-range or disallowed predictive data. Preserve explicit caller values and existing behaviour without managed data.

## Verified current state

011 merged as PR #16 at `633939a`; its final PR checks and post-merge fast CI passed. `time.resolve` supports UTC/TT/TDB/UT1 with leap validity and uncertain-time guards. Strict charts currently require supplied DUT1/delta-T, and topocentric requests also require supplied polar motion. No managed EOP loader exists. Dataset installation is explicit; runtime remains offline.

## Scope and exclusions

Use the unchanged IERS Rapid Service/Prediction Centre (USNO) `finals2000A.all`, Bulletin A x/y and UT1−UTC columns. Pin exact bytes, source URL, acquisition date, format identity and leap-table identity. New optional engine/CLI EOP selection, explicit installer, independent source/interpolation/geometry qualification, immutable small original excerpts and recorded evidence. The production table is installed separately, not bundled with the wheel or committed in full.

Do not change planetary kernels, astrological definitions, chart defaults without EOP selection, historical civil policy or application code. Celestial pole offsets dX/dY, Bulletin B/C04 source selection, pre-1973 observed coverage, absolute physical error bounds, interval charts, commercial acceptance and production deployment remain separate.

## Requirements

- Parse and verify original daily A columns and I/P flags, errors, calendar/MJD consistency, finite/range values and ordering. Ignore date-only unavailable rows without extrapolation; fail incomplete/malformed nonblank values. A gap must never be bridged.
- Default to observed IERS rapid values (provisional, not final Bulletin B). Predictions need explicit opt-in and are valid only before first-prediction MJD + 30 days. The validity policy applies to requested epochs, not the host clock; historical observations remain reproducible.
- Interpolate polar motion and **UT1−TAI** linearly in continuous TAI, then restore TT/UTC relations with the pinned leap table. Never interpolate the one-second DUT1 leap discontinuity. Keep exact-node semantics; a last observed node must not implicitly require its predicted neighbour for a point lookup.
- Managed data supplies only missing values. Preserve supplied DUT1/delta-T and individual polar-motion coordinates. Look up only data needed by the requested calculation. Geocentric planetary positions do not require Earth rotation. TT/UT1/historical requests continue to need explicit rotation/polar values; do not invent UTC for them.
- Topocentric finite differences reevaluate managed values at shifted epochs, including observer velocity; require supporting coverage rather than clamping a derivative stencil. Geocentric chart longitude rates do not acquire unrelated EOP coverage requirements.
- Record used offsets, nodes/fraction, separate UT1/polar status, applied fields, dataset/hash and formal errors at source nodes. Keep physical uncertainty null; endpoint formal errors are not a propagated absolute bound. Record that dX/dY are not applied.
- Explicit immutable/atomic install with checksum/size verification, bounded downloads, local source option and rollback by pinned dataset identity. No runtime network, silent update, model fallback or source substitution when configured managed input fails.

## Compatibility and operations

`Ephemeris(..., eop_path=..., allow_predicted_eop=False)` and CLI `--eop` / `--allow-predicted-eop` select the feature. `install-eop` is the only acquisition operation. Constructor arguments and metadata are additive; request schemas are unchanged. Existing explicit values remain valid. No source is discovered from the working directory or silently enabled.

Preserve exact source archives in the operator's controlled artefact store. Upstream live URLs change; a new download that fails the pin is not an update. CI can restore the checksum cache or original-file artefact from a previous successful run. Retention of a CI artefact is finite; local archives remain important. Updates require a new manifest/identity, reviewed prediction window and requalification.

## Acceptance criteria

- Original-source SHA/format and independent parser agreement, exact known A values and leap-second interpolation pass.
- Default prediction denial, mixed supplied/managed values, gap/end/expiry/corruption failures and 011 uncertainty guards pass.
- Real-kernel chart/CLI and topocentric scalar/batch tests agree with matched explicit inputs. Independently sampled topocentric rates agree with separate scalar derivative requests.
- Independent Skyfield source parser/interpolation, vector-plane ASC/MC and observer-state comparisons pass predeclared diagnostics; all measured residuals are retained, not called physical bounds.
- Existing baseline numerical gates, Ruff/format, mypy, source/legal audit, tests, build and clean wheel/sdist smoke pass. Missing optional source tests remain skips, not numerical successes.

## Validation and references

Run repository checks, `tools/datasets/qualify_eop.py` with verified full original source and DE442s, existing `qualify.py` plus supplementary oppositions, full pytest and packaging smoke. Archive compact measured evidence and identify source models/dependencies. Use the official USNO format, IERS product description, ERFA/SOFA time conventions and independently implemented Skyfield parser/geometry. See [managed EOP policy](../../../managed-eop.md).

## Delivery record

Branch `feature/rm-001-012-managed-eop`; prompt In review pending verified acceptance/merge. Record PR/actual results in progress. P2 stays In progress: interval analysis, historical/source coverage and commercial D03/D04 decisions remain open. No merge, publication or deployment is authorised.
