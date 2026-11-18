# RM-001/002 — Physical planet-centre sources: feasibility evidence and gates

**Date:** 18 November 2026  
**Programme:** [RM-001](README.md), P1 decision D01 / P3 source prerequisite  
**Repository baseline:** Aria Ephemeris `main` at `36a9cec742e8248fdee599b7cf620b2b19d12cc7` (package 0.1.0).  
**Work branch:** `feature/rm-001-002-centre-source-feasibility-20261118`  
**State:** source discovery **documented**; live SPK segment audit / reference calculation **BLOCKED / NOT RUN**. Not production qualification.

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

**Evidence classification:** these are current published text summaries, not a local inspection of the SPK's binary segment records, full source hashes, numerical state vectors, or Horizons/CSPICE agreement. NAIF's `BRIEF` summary coverage may cover many segments; the target's **exact segment continuity/type/frame must be inspected from the actual bytes**.

## Candidate source matrix

| Body | Aria v0.1.0 barycentre | Required physical centre | Candidate satellite SPK (NAIF) | Published `BRIEF` range (ET) | Published MD5 | Work status |
| --- | ---: | ---: | --- | --- | --- | --- |
| Mars | 4 | 499 | `mar099.bsp` (~1.1 GB) | 1600-01-01 to 2600-01-02 | `46f5740f86ec78b978ab96a82f0e42b7` | Target pair and nominal range documented; binary not read |
| Jupiter | 5 | 599 | `jup349.bsp` (~93 MB) | 1799-01-16 to 2199-12-15 | `c7ef9d1829bb39bbbc2ba30d4a5a8a05` | Candidate for initial sample; binary not read |
| Saturn | 6 | 699 | `sat456.bsp` (~115 MB) | 1749-12-12 to 2150-01-08; centre's `BRIEF` range starts 1749-12-30 | `4c66748ca3209d0e66ff29954ab1ee64` | Per-target range needs audit; binary not read |
| Uranus | 7 | 799 | `ura184_part-3.bsp` (~369 MB) | 1600-01-04 to 2399-12-17 | `cf24471fb9037543cdbe168bc0fd4c2e` | Newer URA184 centre target listed; binary not read |
| Neptune | 8 | 899 | `nep105.bsp` (~201 MB) | 1600-01-04 to 2400-01-02 | `2c32f77dd972c1a7d80e0c57d9cde2e9` | Target pair and nominal range documented; binary not read |
| Pluto | 9 | 999 | `plu060.bsp` (~129 MB) | 1800-01-02 to 2199-12-30 | `9e8d40339d583273feb94bbf8c95cae4` | Target pair and nominal range documented; binary not read |

For every row, `aa_summaries.txt` explicitly reports `centre target w.r.t. parent planetary barycentre`. **These candidates appear capable of spanning 1900–2100** according to the published text, but a definitive continuous, supported-segment conclusion is **not yet verified**. JPL's catalogue lists 1900–2100 nominally for other sources too; we favour the candidate solutions above for the starting audit, not as a frozen commercial selection.

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
| F2 — binary compatibility | For every source, real SPK segment IDs/types/frames, complete 1900–2100 centre-only continuity, source SHA-256 pinned | **NOT RUN: binary unavailable** |
| F3 — Jupiter sample | One centre state and velocity = verified DE442s Jupiter barycentre + JUP349 direct offset; numerical values recorded | **NOT RUN: binary unavailable** |
| F4 — independence | CSPICE/Horizons appropriately matched epoch/source comparison with explicit residuals and tolerances | **NOT RUN** |
| F5 — packaging feasibility | Exactly required SPK records, measured size and reproducible compact generation, modified-kernel metadata/credits review | **DESIGN ONLY; no pack built** |
| F6 — regression safety | Audit unit checks and existing `pytest -m 'not kernel'`, lint, type/package checks on real development runner | **Await CI; no new numerical run claimed** |

## Environment and blockers

In the available shell, checked 18 November 2026: no `jplephem` or `spiceypy` dependency installed, no DE442s or supplementary SPK kernels, and `curl -I` to both `naif.jpl.nasa.gov` and `ssd.jpl.nasa.gov` returned **`Could not resolve host`**. Thus this increment **cannot truthfully assert F2–F5 passed**, nor a numerical tolerance, source SHA-256, complete per-segment range or Jupiter-state numeric result. The repo's historical Oct 2026 qualification applies to its original barycentre targets only.

## Next implementation step

1. On an approved network-enabled runner, download **JUP349 first**, validate published MD5, record SHA-256 independently, then run Jupiter audit + verified DE442s sample.
2. Run full six-source audit and independently compare Jupiter against CSPICE with exact source and time conventions.
3. Assess actual centre-only SPK extraction size and redistribution obligations (NAIF requires renamed producer-attributed modified kernels, comments and validation). Avoid a commercial distribution decision until measured.
4. With successful and reviewed evidence, authorise WP2 multi-kernel resolution and WP3 named `planet-centres-v1` calculation profile; preserve the original v0.1.0 barycentre behaviour.

**No engine targets, chart output defaults, Aria Galaxy code, package, release or deployment have been changed by RM-001/002.**
