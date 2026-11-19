# WP5.1 — Frozen independent Horizons reference fixtures

**Acquired:** 19 November 2026 UTC · **Source:** [NASA/JPL Horizons API](https://ssd.jpl.nasa.gov/api/horizons.api) · **Evidence set:** [horizons-reference-v1.json](../../../data/fixtures/horizons/horizons-reference-v1.json) and [12 original responses](../../../data/fixtures/horizons/raw/)  
**WP5.1 scope:** external reference **acquisition only**, not Aria numerical comparison.

## Result

**300 independently sourced records** = 6 physical centres × 25 JD epochs per planet × 2 independent measurement modes. Each mode has one complete Horizons query per planet. Acquired source text is SHA-256-pinned, retained alongside exact request parameters/URLs and API signatures, then parsed to numerical values. A separate offline verifier checks every original response and every derived fixture.

| Layer | Horizons convention | Actual recorded quantity |
| --- | --- | --- |
| Geometric | Physical body centre vs Earth geocentre (399); ICRF `REF_PLANE=FRAME`; `VEC_CORR=NONE`; TDB JD | 3-component position (km) and velocity (km/s) |
| Apparent | Physical body centre vs Earth geocentre (399); ICRF; `QUANTITIES='45'`; airless; observer `TIME_TYPE=TT` | Inertial apparent RA/Dec (degrees), corrected per Horizons' model |
| Time and selection | `TLIST_TYPE=JD`, 18 stratified dates and 7 targeted dates including centre-segment join ±0.04 day | 25 numeric JDs per body per mode, always within 1900–2100 |
| Authenticity | Original API result retained verbatim; SHA-256 computed independently over its UTF-8 bytes | Exact URLs, response signatures, source headers and record counts |

**Do not treat equal numeric TT and TDB JDs as exactly the same moment.** WP5.2 must convert to a common physical instant before pairwise comparisons. Inertial RA/Dec must also be transformed using an explicitly matched, independently implemented frame convention before comparison to tropical ecliptic longitude.

## Horizons' actual source solution labels

The Horizons server's source assignments **are not necessarily the data combinations used by Aria** (Aria combines DE442s with original JPL satellite centre offsets). The labels below were extracted from the **original captured Horizons headers**, not guessed from a catalogue.

| Target (NAIF) | Target source in Horizons header | Observer/other reported source labels | Aria's centre offset source |
| --- | --- | --- | --- |
| Mars (499) | `mar099` | `DE441` | `mar099.bsp` |
| Jupiter (599) | `jup365_merged` | `jup365_merged`, `DE441` in apparent header | `jup349.bsp` |
| Saturn (699) | `sat441l` | `DE441` | `sat456.bsp` |
| Uranus (799) | `ura184_merged` | `ura184_merged`, `DE441` in apparent header | `ura184_part-3.bsp` |
| Neptune (899) | `nep098_merged` | `nep098_merged`, `DE441` in apparent header | `nep105.bsp` |
| Pluto (999) | `plu060_merged` | `DE441` | `plu060.bsp` |

An apparent-coordinate difference between Aria and this dataset may be a **different ephemeris solution or correction convention**, rather than an implementation bug. In WP5.2, report both any direct residual and a separate classification of source-model/reference convention differences. **Do not widen a tolerance automatically to obtain a pass.**

## Reproducibility and boundaries

The public API was queried **sequentially**, one request at a time. Downloaded reference text and SHA-256 are now immutable versioned inputs for all future comparisons. Query timestamps and the API response signature are stored for every request. The reference-acquisition script is explicitly networked; the verification script and normal tests are **offline**.

[Official Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html) defines both table types, output time scales and quantity selection. [Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html) describes inertial apparent RA/Dec quantity 45, including light-time, deflection and aberration. [NASA/JPL API policy](https://ssd-api.jpl.nasa.gov/doc/) requires considerate serial access; archived fixtures prevent unnecessary repeated calls.

**WP5.1 has not calculated an Aria-versus-Horizons residual**; no target is described as physically accurate to an asserted tolerance, and the sampled fixtures are not a guarantee for all dates. Full apparent tropical coordinates, longitude rates, events/stations and numerical acceptance belong to WP5.2–WP5.4. No Aria runtime, app provider or deployment was altered.

## Usage by WP5.2

Read the immutable structured fixture JSON, verify the original source-response SHA-256 values, align actual TT/TDB instants and reference frames, classify source-model differences, and *then* apply independently approved tolerances. Reject missing/ambiguous source metadata or any unreviewed source refresh.
