# Release 0.1.0 validation

**Status: passed · 10 October 2026.** The [machine-readable report](qualification-0.1.0.json) records exact versions, source hash, seeded sample policy, per-body maxima, RMS/p95 errors and event windows. The [benchmark](benchmark-0.1.0.json) records the measured environment. These are empirical implementation-agreement results, not an absolute ephemeris uncertainty guarantee or a continuous error bound.

| Quantity | Measured maximum | Acceptance limit |
| --- | ---: | ---: |
| Same-kernel raw position | 0.0281328 m | 1 m |
| Same-kernel raw velocity | 2.99054e-05 mm/s | 1 mm/s |
| Matched apparent direction | 4.794e-06 arcsec | 1 arcsec |
| Matched longitude rate | 8.4152e-09 deg/day | 0.0001 deg/day |
| Chart ASC/MC | 0.000133431 arcsec | 1 arcsec |
| Tested event times | 0.0414804 seconds | 10 seconds |

All ten supported astrology targets are sampled at 4,712 epochs each, from 1900-01-01 through 2100-12-31 TT: 32-day grid, 2,048 seeded off-grid instants, source polynomial boundaries on both sides and operating endpoints. Raw states use independent CSPICE evaluation in J2000 at identical TDB epochs; differences include evaluator/time-representation rounding. Direction/rate references use independent Skyfield observer, light-time, aberration and frames. Rates use a different differentiation step. Chart geometry uses independent vector-plane intersections with Skyfield GST/obliquity in both hemispheres and latitudes up to ±70°, with the same explicitly supplied delta-T. Equal-house cusp error follows the ASC error; whole-sign boundaries follow the independently tested floor/interval definition. Degenerate charts are errors, not qualified cases.

**Deflection conventions matter.** Unmodified Skyfield uses a different near-alignment cutoff. Its maximum discrepancy in this sample is 19.6634 arcseconds, recorded separately. It also creates artificial derivative spikes at cutoff transitions. The accepted reference replaces only that convention with the independently implemented finite-source vector equation and the same documented limiter. It does not call ERFA ld or Aria positions. The ordinary unmodified Skyfield disagreements are not hidden or counted as accepted implementation error. Agreement with a shared numerical model is distinct from predicting visible light through an occulting body.

The report checks 39 whole-year body/type windows in 1900, 2000 and 2099, with 680 events and matching independently found counts. Cases cover Sun/Moon ingresses, Moon–Sun conjunctions/oppositions, Mercury–Sun 15° aspects and all supported planetary stations. Reference scans are eight times denser and refined with SciPy Brent; Aria uses bounded bisection and rate-extremum subdivisions. Some body/year windows have no stations. Synthetic regressions separately cover recrossings inside a scan interval, tangential contacts, endpoints, wrapping, cancellation, budgets and tiny scan steps.

Timing qualification applies only to well-conditioned events in matching declared windows. Other windows and tangencies return unqualified timing metadata. A finite sampling grid cannot prove that every possible interval contains no hidden roots. Absolute chart accuracy also depends on supplied UT1/polar motion and civil-time accuracy. Barycentres are qualified as barycentres, without a planet-centre substitution claim. Topocentric directions have independent sample tests, rather than the broad geocentric grid gate. Heliocentric/geometric and alternate-frame contracts have integration/mathematical checks, not the same broad apparent gate. Source-model uncertainty is not measured here; no compression is performed.

## Performance

CPU: AMD EPYC 9V74 80-Core Processor; Python 3.12.14 on Linux-6.18.44-x86_64-with-glibc2.39. This was a shared execution environment with qualification work active; repeat on the intended deployment host. New-engine first calculation took 0.102 s without purging the OS page cache. Ten-body warm median was 77.4 ms (maximum 121.0 ms). A chunked 10,000-epoch ten-body batch took **67.63 s**, and peak process RSS was 42.9 MiB.

The provisional 100 ms warm-median target was met; the 2-second batch target was **not met**. Repeated standards/correction evaluation and Python result construction need profiling/optimisation before high-throughput claims. Compact packs and their size/accuracy remain planned.

## Reproduce

Use Python 3.12 with `requirements/development.lock`, install editable with `--no-deps`, and install the checksum-verified dataset explicitly. Exact check commands are in the JSON report and README. Run the primary qualification and the supplementary opposition check, then:

```bash
python tools/datasets/release_report.py --primary .artifacts/release-qualification.json --oppositions .artifacts/oppositions.json
```

The combiner refuses failed/quick stages or mismatched kernel/versions. Missing kernels fail qualification. Ordinary integration skips never count as a pass. Wheel and sdist were installed in clean environments and all documented CLI examples executed; licence payloads and source-term hashes were checked. Fast CI and real-kernel CI are separate, and publication remains manual. Upstream legal notices are retained byte for byte; whitespace checks exclude those preserved inputs.
