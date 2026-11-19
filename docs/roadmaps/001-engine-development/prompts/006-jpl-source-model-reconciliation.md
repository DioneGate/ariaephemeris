# RM-001/006 — Reconcile Horizons and Aria Jupiter/Pluto source models

| Field | Value |
| --- | --- |
| Date and authorisation | 19 November 2026 — owner requested source-model reconciliation and assessment of defensible commercial accuracy limits |
| Roadmap | [RM-001](../README.md), P3/P6 scientific validation prerequisite |
| Starting point | [WP5.2 independent comparison](../p1-external-horizons-comparison.md) merged via PR #9 |
| Implementation branch | `feature/rm-001-006-jpl-source-model-reconciliation-20261119` |
| PR | [#11](https://github.com/DioneGate/ariaephemeris/pull/11), **draft/unmerged** |
| Prompt status | **Done — bounded source attribution merged at `0b5d6d6`; independent absolute physical accuracy and commercial release remain unqualified** |

## Objective and contract

Independently attribute the two largest WP5.2 **geometric source-model discrepancies**, Jupiter **14.82 km** and Pluto **40.91 km**, to Earth-barycentric, planetary-system-barycentric and direct planet-centre-offset contributions at identical physical TDB instants. Prevent the incorrect interpretation that differing named physical-centre SPKs automatically imply mismatched centre trajectories. Quantify source consistency, preserve exact provenance and distinguish numerical implementation correctness from JPL model or absolute physical accuracy.

**No change** to existing Aria algorithms, source selection, release, public API, Aria Galaxy, profile defaults or original SPK binaries.

## Verified source baseline

- Original WP5.1 300 Horizons references and WP5.2 [measured comparison report](../../../validation/wp5-2-horizons-comparison.json), already frozen and SHA-256 verified.
- Original Aria JPL [DE442s](../../../../src/ariaephemeris/resources/de442s.json) and [six physical-centre SHA-pinned data identities](../../../../src/ariaephemeris/resources/planet-centres.json).
- [JPL JUP349 NAIF documentation](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/jup349.cmt) states physical Jupiter (599) was inherited **from JUP365**, and DE442 planetary barycentre data was merged separately. Hence JUP349 vs JUP365 label is *not* evidence of different 599/5 offsets.
- [JPL PLU060 NAIF documentation](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/plu060.cmt) states Pluto (999) and DE440 system barycentre/observer trajectories were merged. Horizons currently reports `plu060_merged` with **DE441** in its source headers; the exact Horizons-selected model must be retained, not silently assumed equal to every embedded SPK record.

## Scope

1. Acquire 200 new independently sourced official Horizons states: Jupiter and Pluto, 25 original WP5.1 TDB epochs each, direct parent-centre relative to Earth, parent relative to SSB, Earth relative to SSB, and physical centre relative to SSB. Preserve eight raw text responses, query URLs, exact 3D vector conventions, source labels and SHA-256.
2. Verify all responses/derived states offline and fail closed on missing, corrupt, wrong target/centre/time or mismatched source values. Never substitute Aria output as a source reference.
3. Recompute original WP5.2 geometric Jupiter/Pluto states with the **exact original SHA-pinned Aria kernels**, not a new planetary model. For all 50 samples, evaluate the exact vector decomposition:

   `(Aria centre − Aria Earth) − (Horizons centre relative to Earth) = [Aria parent geo − Horizons parent geo] + [Aria centre−parent offset − Horizons effective centre−parent offset]`.

   Further split the parent term into planetary SSB and Earth SSB model differences plus independently measured Horizons path/source-selection inconsistency.
4. Record position and velocity components, norms, RMS/p95/max and original WP5.2 fixture IDs; assert exact vector identity closure and source profile integrity, including conservative numerical tolerance for decimal Horizons text.
5. Produce a cited measurement report quantifying **which component dominates**, checking whether physical offsets are consistent, and proposing **separately labelled engineering/product acceptance criteria**. Do not claim independent absolute astronomical uncertainty from a 25-date sample or multiple JPL models.
6. Maintain a separate draft PR and progress evidence. No user authorisation to merge or change default model was provided for this request.

## Observed measured result (source reconciliation)

The complete [machine-readable decomposition](../../../validation/wp5-3-jpl-source-attribution.json) gives the following 25-epoch maxima:

| Metric | Jupiter | Pluto |
| --- | ---: | ---: |
| Original geocentric physical-centre difference | 14.816885 km | 40.913480 km |
| Planetary-system SSB barycentre difference | 14.895411 km | 41.226676 km |
| Earth SSB model difference | 0.483490 km | 0.483490 km |
| **Effective physical-centre offset difference** | **0.248 mm** | **1.908 mm** |
| Query-path/source-chain inconsistency | no more than 0.244 mm | no more than 1.216 mm |

Every one of the 50 original discrepancy vectors was reconstructed from independently sourced reference components to better than **0.5 mm position residual**. Per-epoch signed vectors, including velocity, are retained; independent maxima must **not** be added as scalar budgets. These values are a model-difference attribution, not absolute error bounds.

## Acceptance and outstanding gates

- [x] 200 separately acquired Horizons states archived with original raw SHA-256, exact request/response headers and source labels.
- [x] 50 original WP5.2 geometric residuals reconstructed algebraically; explicit planetary barycentre, Earth, physical-offset and query-chain contributions.
- [x] No numerical change to Aria engine, no change to barycentre/physical profile defaults or SPK identities; no false commercial physical uncertainty claim.
- [x] [Fast CI #44481431302](https://github.com/DioneGate/ariaephemeris/actions/runs/44481431302) **PASS** (Ruff, mypy, audit, non-kernel tests, build and package smoke); [frozen-source integrity #44481431375](https://github.com/DioneGate/ariaephemeris/actions/runs/44481431375) **PASS**; [real JPL-source attribution #44481431478](https://github.com/DioneGate/ariaephemeris/actions/runs/44481431478) **PASS**, including **byte-for-byte regeneration** of the frozen numeric evidence. The existing full-kernel pytest passed in the separately running baseline qualification job; its longer historical qualifier is tracked separately and is **not** claimed complete here.
- [ ] Owner review of source-model attribution, proposed external product agreement gate and broader six-planet release qualification.
- [x] Owner independently merged [PR #11](https://github.com/DioneGate/ariaephemeris/pull/11) at [`0b5d6d6`](https://github.com/DioneGate/ariaephemeris/commit/0b5d6d661e5796a7d74889dcffc323741707c1bd); this bounded source-attribution implementation is Done. Release and parent P3/P6 scientific acceptance remain **unapproved**.

**Technical result versus commercial claim:** Jupiter and Pluto centre offsets are independently consistent to millimetre levels on the frozen date sample. The major 14–41 km differences derive principally from **different planetary barycentre trajectories**, with a sub-kilometre Earth reference contribution. This removes the apparent centre-offset defect hypothesis but **does not** establish that either ephemeris gives absolute planet locations within a validated physical uncertainty.

## Files and reproducibility

- [Measured report](../p1-jpl-source-reconciliation.md)
- [200 original source-component fixtures](../../../../data/fixtures/horizons/model-components/jpl-model-components-v1.json)
- [One-shot acquisition](../../../../tools/datasets/acquire_horizons_model_components.py)
- [Offline integrity verification](../../../../tools/datasets/verify_horizons_model_components.py)
- [Numerical attribution](../../../../tools/datasets/attribute_jpl_source_models.py)
- [Synthetic source-decomposition tests](../../../../tests/unit/test_horizons_source_attribution.py)
- [Real-kernel scientific attribution workflow](../../../../.github/workflows/jpl-model-attribution.yml)

The independent-source query workflow must be switched to **manual-only** after data acquisition; tests and routine CI must not silently mutate the frozen JPL fixtures. Subsequent source upgrades require new versions and fresh evidence.
