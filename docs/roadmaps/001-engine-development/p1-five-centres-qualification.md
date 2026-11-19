# RM-001/002 WP3 — Five additional physical planet-centre SPK sources

**Date:** 18 November 2026 · **PR:** [#5](https://github.com/DioneGate/ariaephemeris/pull/5) (draft, unmerged)  
**Engine base:** Aria Ephemeris main `03af9337d073dbe424b534de829619cc6a4e301e` (merged Jupiter PR #4).  
**Evidence:** [Pinned-source GitHub Actions run #44410508647](https://github.com/DioneGate/ariaephemeris/actions/runs/44410508647), **all five matrix jobs succeeded**; [fast CI #44410508459](https://github.com/DioneGate/ariaephemeris/actions/runs/44410508459) **passed**.  
**Machine-readable retained summary:** [p1-five-centres-evidence.json](p1-five-centres-evidence.json), extracted from five individual run artifacts. Full sample vectors are available as the run's uploaded JSON evidence artifacts (subject to GitHub retention).

## Completed source and evaluator gates

The initial [five-source discovery run #44410136973](https://github.com/DioneGate/ariaephemeris/actions/runs/44410136973) downloaded the original NAIF candidate files, verified their published MD5 checksums and recorded observed SHA-256. That first run was **not** a precommitted SHA-256 validation. The hashes were subsequently pinned in [planet-centre-source-manifest.json](planet-centre-source-manifest.json), and a **separate** run #44410508647 repeated the download, checked both published MD5 and committed SHA-256, audited real binary segments, composed centre states with verified Aria DE442s, and compared with CSPICE.

| Planet | Actual source | Bytes | Centre/parent | Direct segments | Coverage gaps | Independent CSPICE samples | Largest position residual (m) | Largest velocity residual (mm/s) |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: |
| Mars | `mar099.bsp` | 1,227,574,272 | 499/4 | 2 (type 2, frame 1) | None | 11 | 0.011408 | 0.000001199 |
| Saturn | `sat456.bsp` | 120,824,832 | 699/6 | 2 (type 2, frame 1) | None | 11 | 0.004566 | 0.0000000285 |
| Uranus | `ura184_part-3.bsp` | 386,885,632 | 799/7 | 2 (type 2, frame 1) | None | 11 | 0.003216 | 0.00000000690 |
| Neptune | `nep105.bsp` | 210,456,576 | 899/8 | 2 (type 2, frame 1) | None | 11 | 0.002739 | 0.00000000513 |
| Pluto | `plu060.bsp` | 135,207,936 | 999/9 | 2 (type 2, frame 1) | None | 11 | 0.002231 | 0.0000000168 |

**All five passed** the proposed sample-based *same-source evaluator agreement* limits of **1 metre** (barycentric geometric position) and **1 mm/s** (velocity). Each binary contains **two continuous direct planet-centre-relative-to-system-barycentre SPK segments**, whose frame/type is compatible with the existing Aria SPK reader. The tested interval is Aria's 1900–2100 **TT numerical window approximated as TDB with a one-second boundary guard**, not a civil UTC birth-date qualification.

### Direct segment detail (JD TDB)

| Planet | First direct segment | Second direct segment |
| --- | --- | --- |
| Mars | 2305447.5–2447575.5 (index 5) | 2447575.5–2670691.5 (index 2) |
| Saturn | 2360232.5–2456928.5 (index 89) | 2456928.5–2506338.5 (index 88) |
| Uranus | 2305450.5–2446278.5 (index 11) | 2446278.5–2597626.5 (index 5) |
| Neptune | 2305450.5–2447830.5 (index 2) | 2447830.5–2597642.5 (index 3) |
| Pluto | 2378497.5–2456293.5 (index 11) | 2456293.5–2524591.5 (index 5) |

## Reproducible qualification method

- [`tools/datasets/qualify_planet_centres.py`](../../../tools/datasets/qualify_planet_centres.py) operates on one physical planet per job; [workflow](../../../.github/workflows/planet-centre-qualification.yml) runs a matrix of Mars, Saturn, Uranus, Neptune and Pluto and uploads **only JSON**, never the original kernels.
- A verified DE442s base supplies barycentric states of the **planetary-system barycentre**. The candidate satellite kernel supplies only the **direct planet-centre offset relative to that barycentre**. The calculation composes **position and velocity at the same TDB epoch**, not the satellite file's potentially different barycentre solution.
- CSPICE/SpiceyPy independently evaluates the same JPL source data, loading the satellite first and DE442s last to give DE442s target precedence. Tests include 1900/2100 numerical boundaries, selected intervening dates, J2000 and samples on either side of the internal centre-segment join. For each sampled epoch the report retains the source segment index, state vectors and position/velocity residuals.
- The first run verified the [NAIF published MD5 digest list](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/aa_checksums.txt); a subsequent separate commit pinned SHA-256 from that first MD5-verified run. In the final run `source_gate_pass: true` for every planet. Every source version is recorded in the [manifest](planet-centre-source-manifest.json).

## Qualification boundary and remaining decisions

Together with the separately completed [Jupiter WP1/WP2 qualification](p1-jupiter-centre-qualification.md), **all six planet-centre sources now satisfy the source-binary-integrity, direct-segment coverage, and same-source CSPICE evaluator gates** for Aria's target numerical interval.

These tests **do not** establish absolute physical ephemeris accuracy; different JPL satellite solutions' dynamical compatibility with the DE442s planetary model; commercial redistribution of compact extracted kernels; geocentric apparent positions, rates and event timing; historic civil-time support; or Aria Galaxy integration. The 11 sample epochs per planet are not a continuous numerical error guarantee, even though the interval coverage itself was inspected continuously from the segment metadata.

**Next separately authorised work:** production multi-kernel resolver and named physical-centres calculation profile, preserving the existing barycentre default and provenance. The compact dataset packaging/attribution and full P3/P4/P6 release gates remain open. **PR #5 remains draft and unmerged** pending owner review; no runtime API, chart calculation default, Aria Galaxy code, publication or deployment changed.
