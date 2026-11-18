# RM-001/002 — WP3 physical-centre source qualification: five additional planets

**Date:** 18 November 2026  
**Branch/PR:** [WP3 draft PR #5](https://github.com/DioneGate/ariaephemeris/pull/5), `feature/rm-001-002-wp3-five-centres-20261118`  
**Baseline:** merged Jupiter WP1/WP2 [PR #4](https://github.com/DioneGate/ariaephemeris/pull/4) (`main` `03af9337d073dbe424b534de829619cc6a4e301e`).  
**Current gate:** *Source discovery runs in progress; recorded MD5-derived SHA-256 and CSPICE evidence must be reviewed and SHA-256 pins committed before final source acceptance.*

## Scope

Qualify physical centres for **Mars 499/4, Saturn 699/6, Uranus 799/7, Neptune 899/8 and Pluto 999/9**, extending the separately qualified [Jupiter 599/5](p1-jupiter-centre-qualification.md). Retain original Aria DE442s barycentre source as the controlled common parent for each target. **No engine runtime change** is included in WP3.

Source records are stored in [the five-source candidate manifest](planet-centre-source-manifest.json), with independently published MD5 checksums from [NAIF's `aa_checksums.txt`](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/aa_checksums.txt). Source names and nominal coverage come from [NAIF's `aa_summaries.txt`](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/aa_summaries.txt).

| Planet | Selected source | Centre relative to barycentre | Published MD5 verified | Binary type/frame/1900–2100 coverage | CSPICE evaluator | Pinned SHA-256 replay |
| --- | --- | --- | --- | --- | --- | --- |
| Mars | `mar099.bsp` | 499 / 4 | Pending binary check | Pending | Pending | Pending |
| Saturn | `sat456.bsp` | 699 / 6 | Pending binary check | Pending | Pending | Pending |
| Uranus | `ura184_part-3.bsp` | 799 / 7 | Pending binary check | Pending | Pending | Pending |
| Neptune | `nep105.bsp` | 899 / 8 | Pending binary check | Pending | Pending | Pending |
| Pluto | `plu060.bsp` | 999 / 9 | Pending binary check | Pending | Pending | Pending |

## Reproducible test methodology

- GitHub [five-source matrix workflow](https://github.com/DioneGate/ariaephemeris/blob/feature/rm-001-002-wp3-five-centres-20261118/.github/workflows/planet-centre-qualification.yml) runs each candidate **in a separate job**, with independent failure and small JSON artifact upload; kernels are **not** committed or distributed in artifacts.
- Each job acquires **original NAIF file** and uses a SHA-256 recorded in the source manifest (when present); `qualify_planet_centres.py` verifies NAIF's independently published **MD5** and rejects any mismatching precommitted SHA-256.
- The binary inspector [`inspect_segments`](../../../tools/datasets/audit_planet_centres.py) selects only the direct target-centre SPK pair, **type 2 or 3**, **frame 1**, and tests union coverage over Aria's entire `1900–2100` numerical window with a one-second TT/TDB guard at either end. Other target segments never count as coverage.
- For every sampled TDB epoch, calculate `DE442s barycentre (N wrt 0) + satellite displacement (NNN wrt N)`, including **km/day** velocities. Do not use embedded alternate planetary barycentre records from satellite files.
- Independently evaluate the **same** JPL data with CSPICE/SpiceyPy loaded satellite first, DE442s last; compare position, velocity, each component and composition. Sample operating boundaries, J2000, 1950, 2020, 2026, 2050, 2100 and up to four in-range SPK segment joins (one hour either side).
- Candidate same-source **evaluator agreement** gates: position residual ≤ 1 m, velocity residual ≤ 1 mm/s; code must fail closed on missing coverage, unsupported frame/type, checksum mismatch or nonfinite states. These gates do not establish external physical-source model accuracy.
- First successful discovery run only establishes **published MD5-verified observed SHA-256** and sample agreement. Record SHA-256 in a **separate reviewed commit**, then rerun and require `source_gate_pass=true` before marking source identity qualified. The log and JSON artifact are the immutable evidence.

## Limits and WP4 entry gate

Even if all five source checks pass, this **does not** validate apparent/geocentric horoscope positions, astronomical event times, source-model consistency across different JPL development epochs, true historic civil time or commercial deployment. Those require separately defined P3/P4/P6 gates.

A multi-kernel production resolver, `planet-centres-v1` request profile, provenance/error semantics, full apparent corrections and application provider migration are **outside WP3**. Once all six source/evaluator gates pass, the **next separately authorised work package** can implement the production multi-kernel resolver. Keep existing barycentre behaviour unchanged until explicitly migrated and qualified.
