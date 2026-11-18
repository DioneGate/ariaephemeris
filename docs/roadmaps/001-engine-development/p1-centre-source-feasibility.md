# RM-001/002 — Physical planet-centre sources: feasibility evidence and gates

**Date:** 18 November 2026  
**Programme:** [RM-001](README.md), P1 decision D01 / P3 source prerequisite  
**Repository branch base:** Aria Ephemeris `main` at `df96380ee851e3aeac1962ec6010807342f3b7da` (merged PR #3, package 0.1.0; numerical implementation unchanged from the inspected `36a9cec` baseline).  
**Work branch:** `feature/rm-001-002-centre-source-feasibility-20261118`  
**State:** **All six** physical planet-centre candidate SPK sources have passed original-source integrity, direct-segment binary coverage and independent **same-source CSPICE evaluator** checks across selected epochs. Jupiter [WP1/WP2](p1-jupiter-centre-qualification.md); remaining five [WP3](p1-five-centres-qualification.md). **No commercial release or absolute physical-accuracy qualification.**

## Objective and explicit product decision

D01 direction is **physical planet centres for Mars, Jupiter, Saturn, Uranus, Neptune and Pluto** in a future named commercial calculation profile. Keep the original barycentre-based v0.1.0 reference profile and numerical identity intact. This is an owner-approved *direction* from conversation on 18 November, **not** approval of numerical tolerances, centre-source files, release defaults, fallback policies or completion of the wider P1 launch decision register.

The immediate RM-001/002 objective is not to change `BODY_IDS` or replace chart results: find compatible, independently verifiable physical-centre SPK offset data, design a safe composition route using the existing DE442s base, and supply a reproducible offline qualification probe.

## Sources reviewed (18 November 2026)

- Official JPL catalogue, named solutions and nominal ranges: https://ssd.jpl.nasa.gov/sats/ephem/files.html
- Official NAIF inventory and listed sizes: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/
- NAIF `BRIEF` summaries identifying target IDs, reference centres and *summary* coverage: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/aa_summaries.txt
- NAIF published checksums (32-character **MD5**, **not SHA-256**): https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/aa_checksums.txt
- Horizons explanation of centre-offset dependence on satellite solutions: https://ssd.jpl.nasa.gov/horizons/manual.html
- Data-use and modified-kernel responsibilities: https://naif.jpl.nasa.gov/naif/rules.html

**Evidence classification:** original source candidates and MD5 values were discovered from NAIF's published summaries. Actual downloaded files, SHA-256 pins, compatible direct segments, continuous interval coverage and CSPICE same-source evaluator results are established for **all six** in [Jupiter evidence](p1-jupiter-centre-qualification.md) and [WP3 five-source evidence](p1-five-centres-qualification.md). This remains a bounded numerical evaluator test, not independent physical-model accuracy. NAIF's `BRIEF` summary coverage may cover many segments; the target's **exact segment continuity/type/frame must be inspected from the actual bytes**.

## Candidate source matrix

| Body | Aria v0.1.0 barycentre | Required physical centre | Candidate satellite SPK (NAIF) | Published `BRIEF` range (ET) | Published MD5 | Work status |
| --- | ---: | ---: | --- | --- | --- | --- |
| Mars | 4 | 499 | `mar099.bsp` (~1.1 GB) | 1600-01-01 to 2600-01-02 | `46f5740f86ec78b978ab96a82f0e42b7` | **WP3 PASS** — real binary/type/frame/coverage and CSPICE evidence; [record](p1-five-centres-qualification.md) |
| Jupiter | 5 | 599 | `jup349.bsp` (~93 MB) | 1799-01-16 to 2199-12-15 | `c7ef9d1829bb39bbbc2ba30d4a5a8a05` | **WP1/WP2 verified**, pinned 97,525,760-byte SPK, two type-2/frame-1 segments, zero gaps, 9-epoch CSPICE agreement; [evidence](p1-jupiter-centre-qualification.md) |
| Saturn | 6 | 699 | `sat456.bsp` (~115 MB) | 1749-12-12 to 2150-01-08; centre's `BRIEF` range starts 1749-12-30 | `4c66748ca3209d0e66ff29954ab1ee64` | **WP3 PASS** — per-target binary coverage independently audited; [record](p1-five-centres-qualification.md) |
| Uranus | 7 | 799 | `ura184_part-3.bsp` (~369 MB) | 1600-01-04 to 2399-12-17 | `cf24471fb9037543cdbe168bc0fd4c2e` | **WP3 PASS** — real binary/type/frame/coverage and CSPICE evidence; [record](p1-five-centres-qualification.md) |
| Neptune | 8 | 899 | `nep105.bsp` (~201 MB) | 1600-01-04 to 2400-01-02 | `2c32f77dd972c1a7d80e0c57d9cde2e9` | **WP3 PASS** — real binary/type/frame/coverage and CSPICE evidence; [record](p1-five-centres-qualification.md) |
| Pluto | 9 | 999 | `plu060.bsp` (~129 MB) | 1800-01-02 to 2199-12-30 | `9e8d40339d583273feb94bbf8c95cae4` | **WP3 PASS** — real binary/type/frame/coverage and CSPICE evidence; [record](p1-five-centres-qualification.md) |

For every row, `aa_summaries.txt` explicitly reports `centre target w.r.t. parent planetary barycentre`. **The selected direct centre segments have now been confirmed by binary inspection to cover 1900–2100** without gaps in their type-2, frame-1 records (with a small TDB boundary guard). JPL's catalogue lists 1900–2100 nominally for other sources too; we favour the candidate solutions above for the starting audit, not as a frozen commercial selection.

**Alternatives:** `mar099s.bsp` is only 1995–2050 (pilot only); `jup348.bsp` (~57 MB) is an additional candidate; `sat441.bsp` (~631 MB) and `ura184_part-1/2.bsp` are alternatives. `ura184_part-3` has the broader `BRIEF` interval and reports the 799/7 relation. No undocumented assumptions about one solution being more accurate than another have been made.

## Existing Aria source design and implementation constraints

Source inspected on `main`:
- `src/ariaephemeris/models.py`: current `BODY_IDS` uses IDs 4–9 for six barycentres; `BodyPosition` has target and target-kind provenance.
- `src/ariaephemeris/sources/__init__.py`: `Kernel` opens **one** SPK, supports SPK types 2/3 and frame 1, chooses the last matching in-file segment and recursively composes its own internal centre chain.
- `src/ariaephemeris/datasets/__init__.py`: `verify()` checks exactly one built-in DE442s SHA-256 manifest.
- `src/ariaephemeris/positions/__init__.py`: existing barycentre-based geometric and light-time-corrected apparent algorithms call the `Kernel.state()` abstraction.
- `docs/conventions.md`: existing target/provenance/time/frame conventions. v0.1.0 must not be reinterpreted in place.

**Critical rule:** do **not** simply load a complete satellite SPK and call `state(599)` as the new global source. That file may carry its **own** planetary barycentre chain, which can differ from Aria's DE442s. Instead take the direct offset `599 wrt 5` from the selected satellite segment and compose it with **DE442s 5 wrt SSB**. Apply the same to position **and velocity** at the correct TDB epoch, including the retarded epoch in apparent mode. Define, version and independently qualify any resulting model/solution combination.

## Tool delivered in this increment

`tools/datasets/audit_planet_centres.py` is a **local, offline source probe**, with kernel-free contract tests in `tests/unit/test_planet_centre_audit.py`. It:
1. Enumerates only **direct** 499/4, 599/5, 699/6, 799/7, 899/8, 999/9 records.
2. Checks real SPK type/frame against Aria's supported 2/3 and frame 1, and calculates **union coverage** and explicit gaps for the 1900–2100 TDB interval (with a one-second TT/TDB boundary guard).
3. Computes SHA-256 on the supplied local file and compares it against an independently pre-recorded expected hash; absent expected hashes **do not pass** the identity gate.
4. Optionally verifies Aria's base DE442s and produces a *sample* centre state from **base barycentre + direct satellite offset** in km and km/day, choosing a reported segment index. It does **not** claim numerical agreement with JPL Horizons or independent CSPICE.
5. Emits JSON evidence and returns non-zero on missing sources, unsupported coverage or unpinned/mismatching hashes. It never downloads any data or modifies installed kernels.

### Reproduction procedure on a network-enabled, controlled runner

Acquire each file explicitly from the NAIF directory listed above; retain URLs, unmodified file comments and original filename. Verify the **published MD5** for acquisition and calculate SHA-256 locally. Record those observed SHA-256 strings in an approved source manifest. Never use an observed hash as an independently verified expected hash in the *same* audit run.

First run a Jupiter-only data inspection and DE442s-composition sample after recording its independently approved SHA-256:

```bash
python tools/datasets/audit_planet_centres.py \
  --kernel jupiter=.artifacts/planet-centres/jup349.bsp \
  --expected-sha256 jupiter=<independently-approved-64-character-SHA256> \
  --base .artifacts/de442s.bsp \
  --sample-jd-tdb 2451545.0 \
  --output .artifacts/centre-audit-jupiter.json
```

Then repeat with `--kernel`/`--expected-sha256` pairs for **all six planets**, `--require-all`, and `--output .artifacts/centre-audit-all.json`. The **J2000 sample is geometric**, in TDB and ICRF-aligned km/km/day; it is not a geocentric apparent horoscope longitude. The base kernel itself must pass Aria's existing DE442s manifest validation. Keep generated source reports and binaries uncommitted under `.artifacts/`.

Independent oracle step: using **CSPICE** with exactly the same chosen planetary base and centre-offset source, compare barycentric 6-state positions for representative epochs, boundaries and overlapping sources. Compare any publicly served Horizons values only after matching target ID, source model, centre, time scale and corrections. Then add apparent/geocentric checks and quantified tolerances in a separately approved WP3/WP4. A successful probe is **not** proof of physical uncertainty, commercial date support or launch readiness.

## Qualification gates

| Gate | Required observable evidence | Status 2026-11-18 |
| --- | --- | --- |
| F1 — source discovery | Six centre IDs, parent IDs, named kernels, nominal intervals, published checksums and official URLs | **Documented from NAIF text** |
| F2 — binary compatibility | For every source, real SPK segment IDs/types/frames, complete 1900–2100 centre-only continuity, source SHA-256 pinned | **ALL SIX PASS** — [Jupiter](p1-jupiter-centre-qualification.md), [WP3](p1-five-centres-qualification.md) |
| F3 — Jupiter sample | One centre state and velocity = verified DE442s Jupiter barycentre + JUP349 direct offset; numerical values recorded | **PASS — recorded J2000 TDB state** in [qualification evidence](p1-jupiter-centre-qualification.md) |
| F4 — independence | CSPICE/Horizons appropriately matched epoch/source comparison with explicit residuals and tolerances | **ALL SIX pass same-kernel CSPICE evaluator gates** (Jupiter 9 samples, others 11 each); *physical model accuracy and independently modelled Horizons comparisons not established* |
| F5 — packaging feasibility | Exactly required SPK records, measured size and reproducible compact generation, modified-kernel metadata/credits review | **DESIGN ONLY; no pack built** |
| F6 — regression safety | Audit unit checks and existing `pytest -m 'not kernel'`, lint, type/package checks on real development runner | **Fast CI passed** previously; [Jupiter pinned workflow](https://github.com/DioneGate/ariaephemeris/actions/runs/44402922404) **passed**. Further revisions require CI review |

## Environment and blockers

The local command-line shell could not resolve JPL hosts, but **GitHub Actions** obtained and checksum-pinned all six source files, audited direct segment coverage and ran matched-convention CSPICE evaluator comparisons. See [Jupiter](p1-jupiter-centre-qualification.md) and [all five WP3 records](p1-five-centres-qualification.md), including the [successful five-source pinned run](https://github.com/DioneGate/ariaephemeris/actions/runs/44410508647). Absolute physical ephemeris accuracy and model compatibility between all chosen JPL solutions and DE442s remain distinct gates. October v0.1.0 numerical qualifications cover original barycentre targets only.

## Next implementation step

1. **Completed:** downloaded and MD5/SHA-256 pinned JUP349, audited both 599/5 segments and the full operating window, and sampled a DE442s-composed J2000 state.
2. **Completed for all six source/evaluator gates:** Jupiter 9 epochs and five other planets 11 epochs each pass the candidate 1 m / 1 mm/s same-source evaluator thresholds. [WP3 qualification report](p1-five-centres-qualification.md). Independent physical accuracy is not claimed.
3. Assess actual centre-only SPK extraction size and redistribution obligations (NAIF requires renamed producer-attributed modified kernels, comments and validation). Avoid a commercial distribution decision until measured.
4. **Next code workstream (separate authorisation):** implement multi-kernel resolution and the named `planet-centres-v1` calculation profile, preserving original v0.1.0 barycentre behaviour. Production packaging and broader model compatibility/release qualification remain open.

**No engine targets, chart output defaults, Aria Galaxy code, package, release or deployment have been changed by RM-001/002 WP1–WP3.**
