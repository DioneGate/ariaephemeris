# RM-001/002 — Jupiter centre WP1/WP2 qualification evidence

**Execution date:** 18 November 2026  
**Scope:** Jupiter physical centre (NAIF ID **599**) relative to Jupiter system barycentre (NAIF ID **5**); **not** six-planet coverage or commercial release approval.  
**Code/workflow branch:** `feature/rm-001-002-centre-source-feasibility-20261118` (draft [PR #4](https://github.com/DioneGate/ariaephemeris/pull/4)).  
**Source manifest:** [jupiter-source-manifest.json](jupiter-source-manifest.json).

## 1. Verified files

| Input | Check | Observed result | Evidence |
| --- | --- | --- | --- |
| Aria DE442s, `de442s.bsp` | Existing SHA-256 and file size from `datasets.verify()` | SHA-256 `54d97562a5b094d298b1b8eafa5a2e17e3e010ce85e1a366d07f003ad159323c`; 32,701,440 bytes per manifest | Existing verified Aria data installation, actual audit sample |
| JPL `jup349.bsp` | Official published MD5 | `c7ef9d1829bb39bbbc2ba30d4a5a8a05` — **matched** | NAIF `aa_checksums.txt`; [discovery workflow](https://github.com/DioneGate/ariaephemeris/actions/runs/44402646337) |
| JPL `jup349.bsp` | Full source SHA-256 | `a8f682fd0f156db47ee9672e0276f0842eb70d3ade8533fed59e38b6d5032971`; 97,525,760 bytes | Observed during MD5-verified discovery and committed separately to [the source manifest](jupiter-source-manifest.json); pinned workflow verifies it independently on re-download |

**Trust chain:** the first workflow obtained JUP349 directly from NAIF and checked its independently published MD5, then reported SHA-256. The second GitHub workflow revision verifies that **previously recorded and committed** SHA-256 as well as the published MD5. A digest alone does not prove the astronomical model is physically correct.

## 2. Actual Jupiter SPK segments and coverage

The jplephem binary inspector found **two direct** `599 wrt 5` segments:

| Source segment index | SPK type | Frame | Start JD TDB | End JD TDB |
| ---: | ---: | ---: | ---: | ---: |
| 29 | 2 | 1 (J2000/ICRF-compatible) | 2378146.5 | 2450464.5 |
| 28 | 2 | 1 (J2000/ICRF-compatible) | 2450464.5 | 2524576.5 |

The segments meet at JD 2450464.5 and produce **no coverage gaps** across Aria's audited operational window `[2415020.499988426, 2488434.500011574]` JD TDB, including a one-second time-scale guard at each boundary. This is an observed binary coverage result for the **direct Jupiter offset only**, not a statement about other planets or historic UTC support.

## 3. J2000 composed centre state

At TDB JD **2451545.0**, the auditable calculation used:

```text
JUP349 Jupiter-centre displacement relative to system barycentre (km):
   +41.0591355377    -44.1323925761    -20.2454383413
JUP349 offset velocity (km/day):
    -1.9529514475     +6.5894678317     +3.1398209543

Aria DE442s Jupiter-system barycentre state + JUP349 direct offset =
Jupiter physical-centre barycentric position (km):
   +597499917.830364  +408990268.242007  +160756264.813738
Jupiter physical-centre barycentric velocity (km/day):
      -682607.322345     +878849.782256     +393336.376705
```

The base barycentre is **always read from checksum-verified Aria DE442s**, not the planetary chain embedded in JUP349. The offset is evaluated at the same TDB epoch in reference frame 1.

## 4. Independent evaluator test (WP2)

The separate `tools/datasets/qualify_jupiter_centre.py` script evaluates **nine TDB instants** (1900/start, 1900+1 day, 1950, J2000, 2020, 2026, 2050, 2100 and end-boundary guard), composing the centre with jplephem/Aria and independently evaluating it with **CSPICE via SpiceyPy**.

CSPICE loads `jup349.bsp` **first** and verified `de442s.bsp` **second** so the shared barycentre target resolves from the intended Aria base kernel. The script separately cross-checks base barycentre, direct offset and composed centre and converts velocity from SPICE km/s to Aria km/day.

| Numerical check | Worst observed difference | Initial evaluator agreement limit | Outcome |
| --- | ---: | ---: | --- |
| Barycentric geometric position | **0.0059855203 metres** | 1 metre | **Pass** |
| Barycentric geometric velocity | **9.54658 × 10⁻⁸ mm/s** | 1 mm/s | **Pass** |

- Initial run: [GitHub Actions #44402646337](https://github.com/DioneGate/ariaephemeris/actions/runs/44402646337) — discovery MD5 check, coverage and nine-epoch CSPICE comparison passed; SHA-256 was recorded but not yet pre-pinned for that run.
- Pinned-source run: [GitHub Actions #44402922404](https://github.com/DioneGate/ariaephemeris/actions/runs/44402922404) — subsequent workflow validates **committed SHA-256** and reruns coverage and CSPICE comparison. The qualification steps passed; use workflow's terminal status when citing its complete CI outcome.
- Audit evidence is uploaded in a **non-SPK** JSON artifact attached to each workflow run, not in the repository or the production application.

**Meaning of 'independent':** this tests two separate computational implementations on the **same source kernels**, not two independent planetary theories. It does **not** establish physical source accuracy, equivalence to a separately configured Horizons solution, apparent/geocentric chart accuracy, interpolation continuity for every instant, or a claim beyond the nine sampled epochs.

## 5. Next actions and exclusions

**Completed for Jupiter:** WP1 acquisition/integrity/direct segment coverage/source identity and sample composition; WP2 nine-point independent evaluator **agreement check** against proposed thresholds.

**Still open:** review candidate JUP349's producing planetary model/comments and compatibility assumptions with DE442s; possible additional test dates near segment boundary/planetary stations; separate commercial-grade numeric acceptance and public interface definition. Repeat source and evaluator qualification for Mars, Saturn, Uranus, Neptune and Pluto in subsequent work packages. Do not mark the entire RM-001/002 or D01 commercial integration *Done* based on Jupiter alone.

**No runtime output change:** `src/ariaephemeris/models.py` target mappings, `Ephemeris`, all Aria Galaxy code, existing barycentre defaults and deployment remain unchanged.
