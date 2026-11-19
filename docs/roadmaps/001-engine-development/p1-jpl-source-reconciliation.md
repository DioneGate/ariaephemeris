# RM-001/006 — Jupiter and Pluto JPL source-model reconciliation

**Investigation date:** 19 November 2026 · **Status:** numerical source attribution complete at the 25 predeclared epochs per body; **independent absolute accuracy and commercial release certification not complete**.

Reference: [WP5.2 independent Horizons comparison](p1-external-horizons-comparison.md), [frozen 300-case report](../../validation/wp5-2-horizons-comparison.json), [new component model report](../../validation/wp5-3-jpl-source-attribution.json), and [200 new original Horizons component states](../../../data/fixtures/horizons/model-components/jpl-model-components-v1.json).

## Executive finding

**The 14.82 km Jupiter and 40.91 km Pluto discrepancies in WP5.2 are overwhelmingly differences in the *planetary reference ephemeris*, not errors in Aria's physical-centre-to-system-barycentre offset.**

Each planet's effective offset calculated from independent Horizons centre-versus-barycentre vectors agrees with Aria's independently pinned satellite SPK offset to **sub-millimetre (Jupiter)** or **approximately 2 millimetres (Pluto)** across the 25-date sample. Differences in the Earth trajectory are smaller, **at most 0.4835 km** at the sampled times. Most of the geocentric discrepancy originates in the planetary barycentre trajectory: Horizons reports **DE441**, Aria uses **DE442s**. None of these results establishes the absolute observational uncertainty of either JPL ephemeris.

### Measured maximum differences (25 TDB epochs per planet)

| Quantity, max over 25 matched dates | Jupiter | Pluto |
| --- | ---: | ---: |
| Original total Earth-centred physical planet-centre residual | **14.816885 km** | **40.913480 km** |
| Planetary system barycentre position relative to SSB, DE442s versus Horizons' DE441 | **14.895411 km** | **41.226676 km** |
| Earth geocentre position relative to SSB, DE442s versus Horizons | **0.483490 km** | **0.483490 km** |
| Geocentric planetary-system barycentre residual | **14.816884 km** | **40.913481 km** |
| Effective physical-centre-to-barycentre offset residual | **0.000248 m (0.248 mm)** | **0.001908 m (1.908 mm)** |
| Physical offset difference computed solely from SSB-centre and SSB-parent paths | **0.123 mm** | **1.168 mm** |
| Horizons direct planet-centre geocentric query vs independently obtained SSB chain | **0.244 mm** | **1.216 mm** |
| Horizons direct parent geocentric query vs independently obtained SSB chain | **0.181 mm** | **1.066 mm** |
| Original total geocentric velocity difference | **0.00025145 m/s** | **0.00002784 m/s** |
| Effective centre-offset velocity discrepancy | **3.55 × 10⁻¹⁰ m/s** | **3.61 × 10⁻¹⁰ m/s** |

**Interpretation of maxima:** maxima for different components can occur at *different epochs and in different directions*. They **must not** be added as scalar errors. The machine report retains each 3D Cartesian component and reconstructs the residual vector for **every one of 50 matched dates**, with a maximum closure residual below **0.0005 millimetres** of position (and explicit velocity decompositions). The result is an algebraic source-model attribution, not a statistical physical uncertainty estimate.

## Reconciliation method

For a physical planet centre, define at the same Julian Date **TDB** and ICRF frame:

- `A_c`: Aria physical planet-centre position relative to the Solar System barycentre (SSB), from `DE442s + original satellite centre offset`.
- `A_b`: Aria planetary-system barycentre relative to SSB from DE442s.
- `A_e`: Aria Earth centre relative to SSB from DE442s.
- `H_cg`: Horizons physical centre relative to Earth, taken from the **frozen WP5.1 reference response**.
- `H_bg`: Horizons planetary system barycentre relative to Earth from a **new independently sourced** vector query.
- `H_b, H_e, H_c`: separately requested Horizons planetary barycentre, Earth and physical centre relative to SSB.

The total existing measured difference is

```text
Total = (A_c − A_e) − H_cg

      = [ (A_b − A_e) − H_bg ]
      + [ (A_c − A_b) − (H_cg − H_bg) ]

      = geocentric barycentre model difference
      + effective physical-centre offset difference
```

We further break down the geocentric parent difference as

```text
(A_b − A_e) − H_bg
  = (A_b − H_b) − (A_e − H_e)
    + [(H_b − H_e) − H_bg]
```

The final term measures **Horizons path/source-selection consistency**, not physical planet-offset error. We also compare `(H_c − H_e)` directly with `H_cg`. Horizons' separate paths close to 0.2 mm (Jupiter) and 1.2 mm (Pluto) at worst: no kilometre-scale error is attributable to a mistaken query origin or inconsistent target chain.

Both numerical decompositions must reconstruct the **same original frozen WP5.2 residual** within explicit low-level tolerances. The real-kernel workflow verifies the source SHA-256, reference API provenance, all 200 new source vectors and 50 complete decompositions. The individual maximum and RMS/p95 residuals, the model source labels and all components are in the machine-readable report.

## Official source evidence — important distinction

- [NAIF JUP349 kernel comments](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/jup349.cmt) explicitly state that `JUP349` incorporates Jupiter **599 from `JUP365`** and planetary barycentres/Sun/Earth from **DE442**. Therefore the difference in labels `jup349` and `jup365_merged` **does not, by itself, represent a different Jupiter-centre offset model**. Our direct vector comparison confirms sub-millimetre differences in the effective offsets.
- [NAIF PLU060 kernel comments](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/plu060.cmt) state that `PLU060` merges physical Pluto 999 with barycentre/Sun/Earth material from **DE440**, whereas Aria deliberately uses the **DE442s** base for planetary system and Earth trajectories. Horizons reports `plu060_merged` with DE441 in independently requested states; its actual reference-chain source must be treated as **Horizons-selected**, not asserted equivalent to the bundled SPK's embedded DE440.
- [NASA/JPL planetary ephemeris description](https://ssd.jpl.nasa.gov/planets/eph_export.html) describes the numerical JPL DE solution updates and the distinct long-range assumptions of DE441. This is model provenance, not a numerical certificate that DE442s is more accurate for a particular epoch.

**No change of Aria's source kernel is warranted by the Pluto/Jupiter result alone.** Both direct physical-centre offset sources appear consistent with the externally evaluated centre-vs-parent offsets. The geocentric differences are from different planetary/observer ephemerides, not an apparent bug in the offset-composition implementation.

## What accuracy can we defend commercially?

The verified result supports three separate kinds of claims, which must not be confused.

1. **Same-source calculation correctness (existing technical evidence):** WP1–WP3 checked JPL binary integrity, direct segment coverage and independent CSPICE evaluator agreement with Aria's own pinned kernel sources. Existing provisional gates were 1 m position and 1 mm/s velocity; these are **implementation-agreement gates**, not absolute physical uncertainty bounds.
2. **External-source practical chart agreement (empirically measured):** WP5.2 measured apparent-inertial direction differences below **0.004789 arcseconds** across 25 epochs each for six planets; 0/150 exceeded the candidate **1 arcsecond** diagnostic bound. The Jupiter/Pluto geometric differences have now been traced almost entirely to model choice. We propose investigating an external **0.05 arcsecond engineering acceptance envelope** for apparent planetary positions, subject to broad additional stress sampling across dates, closest approaches, JPL segment boundaries and severe corrections. **0.05 arcseconds is proposed, not qualified**; a finite sample gives no continuous guarantee. This is a comparison specification, **not** a claim of true measured astronomical position uncertainty.
3. **Absolute astronomical physical accuracy and final commercial release (open):** JPL observational covariance/data accuracy across 1900–2100, mismatches in source epochs and Earth dynamics, correction conventions (deflection and aberration), and derivative/event behaviour have **not** been given an independently supported uncertainty budget. We cannot defensibly assert “accurate to 0.05″” as an absolute truth statement on today's evidence. Astrology-sensitive boundary cases (sign ingress, exact aspect, planetary station) still need their own time/root and conditioning qualification.

Recommended **separate release gates** before claiming commercial-grade numerical accuracy:

- A fixed, professionally reviewed **product metric** (e.g. apparent zodiacal angle vs matched JPL/IAU model, with explicitly stated source epoch/model, operating interval and signed longitude rate), distinct from observational uncertainty.
- Dense geometric/apparent matched-source and independent-source tests across full operating interval and high-risk epochs; report max/p95/RMS **per planet**, not only one overall sample maximum.
- Quantify frame/correction and source-model disagreement separately. Reconcile the remaining Mars, Saturn, Uranus and Neptune source model differences (Neptune's larger sampled velocity residual deserves attention) before a **six-planet** numerical acceptance.
- Validate stations, zodiac ingresses, oppositions/conjunctions, closest approaches and both sides of kernel segment boundaries, with explicit timing error and conditioning.
- Retain the existing `reference` profile regression; do not silently change the production kernel or model default.

## Status and files

The source-model analysis was implemented on [draft PR #11](https://github.com/DioneGate/ariaephemeris/pull/11), separate from `main`; it changes **source-reconciliation tools, tests, datasets, numerical evidence and documentation only**, not Aria engine runtime or Aria Galaxy. The user requested reconciliation but did **not** separately authorise a merge or production source change. The PR therefore remains **In review / unmerged** until authorised.

- [Independent source acquisition tool](../../../tools/datasets/acquire_horizons_model_components.py)
- [Offline source authenticity verifier](../../../tools/datasets/verify_horizons_model_components.py)
- [Algebraic component comparator](../../../tools/datasets/attribute_jpl_source_models.py)
- [Real-kernel numerical workflow](../../../.github/workflows/jpl-model-attribution.yml)
- [Full decomposed evidence](../../validation/wp5-3-jpl-source-attribution.json)

**Scientific verdict:** **Jupiter and Pluto's source-model discrepancies are quantitatively attributed**. Their physical-centre offsets agree to sub-millimetre/millimetre levels in these independent comparisons. The broader absolute source ephemeris uncertainty and six-planet commercial acceptance remain **open**, not passed.
