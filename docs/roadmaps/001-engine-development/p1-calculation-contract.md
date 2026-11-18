# RM-001-P1 — Proposed commercial calculation contract (not an implemented API)

**Recorded:** 18 November 2026. **Scope:** contract proposal for Aria Ephemeris v0.1.0 (`main` `36a9cec`) and the existing Aria Galaxy application (`main` `4ab5f99`). **Decision state: Open.** Nothing below authorises or proves a provider swap, changes the actual schema or changes the app's numerical conventions.

Related: [capability matrix](p1-capability-matrix.md) · [launch decisions](p1-launch-scope-and-decisions.md) · [qualification baseline](p1-qualification-baseline.md) · [RM-001/001](prompts/001-commercial-calculation-contract-and-baseline.md).

## 1. Contracts already implemented

- **Engine** [models.py](../../../src/ariaephemeris/models.py), [engine.py](../../../src/ariaephemeris/engine.py) and [conventions.md](../../conventions.md): `TimeInput`, `PositionRequest`, `PositionsResult`, `ChartResult`, `EventRequest`, explicit JPL target IDs, frames, origins, rates and structured `AriaError`. No persistent HTTP service or application provider bridge exists.
- **Application series** [EphemerisAdapter](https://github.com/DioneGate/archetypal-activation/blob/4ab5f99f277d9c9a221bcf911a820fd9eda50972/frontend/main-app/src/engine/ephemeris/contracts.ts), [adapter](https://github.com/DioneGate/archetypal-activation/blob/4ab5f99f277d9c9a221bcf911a820fd9eda50972/frontend/main-app/src/engine/ephemeris/swephApiAdapter.ts) and [native controller](https://github.com/DioneGate/archetypal-activation/blob/4ab5f99f277d9c9a221bcf911a820fd9eda50972/backend/src/api/controllers/swephController.ts): single/ranged ISO samples with `lon/lat/speedLon`, UTC-labelled Julian days, `major` preset and `truePositions` flag.
- **Application charts** [shared contracts](https://github.com/DioneGate/archetypal-activation/blob/4ab5f99f277d9c9a221bcf911a820fd9eda50972/packages/horoscope/src/contracts.ts), [native chart implementation](https://github.com/DioneGate/archetypal-activation/blob/4ab5f99f277d9c9a221bcf911a820fd9eda50972/backend/src/services/horoscope/chartService.ts), [chart time](https://github.com/DioneGate/archetypal-activation/blob/4ab5f99f277d9c9a221bcf911a820fd9eda50972/backend/src/services/horoscope/time.ts): `ChartRequestV1`, `ChartSnapshotV1`, `ChartCapabilitiesV1`, per-point `DataValue`, `ChartDataV1` and user-visible provenance. V6 saved documents and V2 planet-orb/aspect policies also exist in current code; legacy V1s persist for compatibility.
- **Current app literals**: `ChartCalculationOptionsV1.ephemeris = 'swiss'` and provider/provenance/capabilities `'swiss-ephemeris'`. A future Aria provider **cannot** be represented by spoofing these literal values. Agree a schema/version migration and old-document handling before P4.

## 2. Compatibility classifications

Every row is **one** of: `matches as declared`, `definition differs`, `not implemented`, `unqualified`, or `requires owner decision`. A match in a narrower numerical contract does not mean application feature acceptance.

| Dimension | Existing application behaviour | Existing Aria v0.1.0 behaviour | Classification | Proposed decision/contract |
| --- | --- | --- | --- | --- |
| Sun physical target | Native SE_SUN | SPK 10 Sun | matches as declared | Keep ID 10 and report target |
| Moon physical target | Native SE_MOON | SPK 301 Moon | matches as declared | Keep ID 301 and report target |
| Mercury / Venus | Native physical planet IDs | SPK 199 / 299 physical centres | matches as declared | Preserve target metadata and check frames/modes |
| Mars through Pluto | Native conventional planetary centres (`SE_MARS` … `SE_PLUTO`) | JPL SPK **4,5,6,7,8,9 planetary-system barycentres** | definition differs | Block generic claim of equivalence; approve centres or explicit barycentric display labels with product consequences |
| Range `true_node` / lunar nodes | `major` includes `true_node` and current source falls back to mean constant when missing; chart registry uses `north_node_true` | No lunar nodes | not implemented | No hidden true→mean substitution; explicit canonical alias/error until P3 |
| Current chart provider identity | `ephemeris:'swiss'`, `provider:'swiss-ephemeris'` schema literals | Versioned Aria/JPL manifest | definition differs | New versioned provider identity and truthful provenance |
| Single/range longitudes | HTTP JSON `lon/lat/speed_lon`, preset and point guardrails | Python positions/batch with richer typed metadata | definition differs | Provider-neutral adapter and schema mapping in P4 |
| Horoscope defaults | Tropical, geocentric, **apparent**, Equal, no automatic fallback, sect Fortune | `PositionRequest` default tropical/geocentric/apparent; equal houses exist; Fortune absent | definition differs | Preserve chart-specific defaults; avoid implicit Fortune output |
| Activation defaults | Range `true_positions=true` (native `SEFLG_TRUEPOS`) | Explicit `position_mode='geometric'` or `'apparent'` | unqualified | Treat native flag and Aria geometric as **distinct until tested under matched correction conventions**, not automatically equal |
| Geocentric origin | Native geographic Earth-centred chart | SPK Earth target 399 origin | matches as declared | Qualify coordinates and times, not just name |
| Topocentric origin | Native `set_topo` with location/altitude | WGS84 observer, Earth orientation/polar motion | definition differs | Require agreed EOP policy and observed/modelled uncertainty |
| Heliocentric | Not a ChartRequestV1 option; may exist outside chart API | Aria geometric heliocentric supported | unqualified | No proposed Chart-tab claim without product scope |
| Frame/equinox | Native ecliptic-of-date, sidereal mode optional | `true_ecliptic_of_date` default, ICRS and other frames explicitly defined | unqualified | Record reference frame/obliquity/nutation algorithms and test matching modes |
| Tropical zodiac | Current chart default | Implemented and sampled | matches as declared | Keep explicitly requested tropical mode |
| Lahiri sidereal zodiac | Supported chart setting | Not implemented | not implemented | Hide/block until P3 and independent axiom/frame validation |
| UTC/TT/UT1/TDB | `utc_to_jd` returns TT then UT1 for charts; series returns `jd_ut`; app resolves IANA time | Explicit scales and two-part JD; strict UTC begins 1972, expires 2027-06-28 | definition differs | Versioned, source-qualified time results; no silently estimated historic UTC |
| Gregorian/years | Chart request 0001–2999 proleptic Gregorian | Operational TT 1900-01-01 to 2100-12-31; separate UTC restrictions | definition differs | Replace advertised availability only when UI/backend agree on exact supported input date/time |
| IANA zone, DST gap/fold | Temporal rejects gaps and unresolved overlaps, reports chosen UTC instant/offset | Engine accepts timezone/fold; OS zone data version not pinned | unqualified | Keep precise local-to-instant semantics with controlled tzdata and no repeated historic conversion |
| Unknown/uncertain birth time | Event cast requires an exact resolved instant; saved source can carry uncertainty | No high-confidence unknown-time house mode | requires owner decision | Reject precise houses/angles unless time quality supports them |
| Longitude/latitude | Degrees, longitude [0,360) | Degrees, longitude [0,360) | matches as declared | No chart-render rounding in numerical contract |
| Distances | Chart optional distance AU/rate AU-day; series omits distance | Positions include distance AU and direction vector; raw states km | definition differs | Use explicit fields and nullable missing data |
| Signed longitude rates | Native `SEFLG_SPEED`, degrees/day; angle rates supported in chart | Degree-per-**TT**-day planetary rate; no standalone ASC/MC rate | definition differs | Specify TT-day basis, finite-difference convention, stationary band; retain null for absent angle rates |
| Latitude and distance rates | Chart schema allows nullable degrees/day and AU/day | V0.1.0 `BodyPosition` publishes longitude rate, not corresponding public lat/radial rates | not implemented | Per-field null or qualified implementation; no invented zero |
| ASC/MC/DSC/IC | Valid angles incl. signed rates; DSC/IC antipodes; MC independent of 10th cusp | ASC/MC positions, DSC/IC geometric antipodes in chart; standalone angle rates absent | definition differs | P3 standalone API/rates/degeneracy; app sees null with explanation |
| House cusps | 1–12 Equal/Whole Sign/Placidus; optional explicit-equal fallback | Equal and Whole Sign only, antipode geometry | not implemented | Placidus and fallback policies P3; never accept native Porphyry-on-error silently |
| Sect | Geometric solar centre altitude at/above 0 | No public sect result | not implemented | P3 calculate against true horizon, no refraction |
| Fortune | Day ASC+Moon−Sun; night ASC+Sun−Moon; always-day optional | No Part of Fortune | not implemented | Day/night policy, rates and missing-input semantics P3 |
| Nodes/apogee/Vertex/minor bodies | App registry supports optional points; data-dependent minor bodies | No additional points/minor sources | not implemented | Source/model-by-model P3, optional data unavailability visible |
| Aspects and orbs | Browser's `ChartDataV1` + `AspectPolicyV1/V2` and `ChartAnalysisV1/V2` | Aria has basic aspects (separate algorithm) | requires owner decision | **App remains policy owner**; avoid duplicating or overwriting its profiles/phase rules |
| Activation functions | Browser computes curves, selected kernel/orbs; longitude series is input | Aria supplies positions/batch, not browser activation policy | matches as declared | Keep activation in application; do not add unrequested second evaluator |
| Search/events | Historical catalogue from PostgreSQL; possible chart event features separate | Bounded astronomical ingress/aspect/station event root solver | definition differs | Never equate planetary event root search to the PostgreSQL event catalogue |
| Numerical parity/accuracy | Native dependency/version-dependent results | Existing qualified *same-target*, same-model reference reports | unqualified | New independent matched-convention tests needed for application acceptance |
| Runtime & fallback | Two sweph-backed routes, currently may report source fallbacks | No HTTP service, no fallback to other engine | not implemented | P4 explicit capabilities and P6 verified no-undeclared-provider policy |

## 3. Target and centre registry — proposed authoritative fields

| Canonical body | Aria SPK target | Source target kind | Existing app intent | Contract requirement |
| --- | ---: | --- | --- | --- |
| sun | 10 | Sun physical centre | Sun | Compatible ID, compare correction pipeline |
| moon | 301 | Moon physical centre | Moon | Compatible ID, compare time/ecliptic model |
| mercury | 199 | Mercury physical centre | Mercury | Compatible ID |
| venus | 299 | Venus physical centre | Venus | Compatible ID |
| earth (internal) | 399 | Earth physical centre | Origin/reference | Explicit, not app chart option |
| mars | 4 | Mars-system barycentre | Mars physical centre | **Block as generic 'Mars' until decision** |
| jupiter | 5 | Jupiter-system barycentre | Jupiter physical centre | **Block as generic 'Jupiter' until decision** |
| saturn | 6 | Saturn-system barycentre | Saturn physical centre | **Block as generic 'Saturn' until decision** |
| uranus | 7 | Uranus-system barycentre | Uranus physical centre | **Block as generic 'Uranus' until decision** |
| neptune | 8 | Neptune-system barycentre | Neptune physical centre | **Block as generic 'Neptune' until decision** |
| pluto | 9 | Pluto-system barycentre | Pluto physical centre | **Block as generic 'Pluto' until decision** |

All SPK IDs above come from [E models](../../../src/ariaephemeris/models.py) and [E conventions](../../conventions.md), not a claim of equivalence to the current application's [native sweph body IDs](https://github.com/DioneGate/archetypal-activation/blob/4ab5f99f277d9c9a221bcf911a820fd9eda50972/backend/src/services/horoscope/chartService.ts). No physical planet-centre dataset or correction was added here. A comparison must use an independently established centre target, with exactly matched epochs, observer, frame and correction definition.

## 4. Proposed `AriaCalculationContract/1` (concept only)

This is a *design vocabulary*, **not** an implemented JSON endpoint or existing schema:

| Category | Required fields / invariants |
| --- | --- |
| Request identity | `contractVersion`, `operation` (position/chart/batch/bounded-search), requested body IDs/points, explicit calculation/profile version, source dataset ID; reject unknown IDs/options |
| Time identity | `timeInput` (local civil with IANA/fold or explicit UTC/TT/TDB/UT1), resolved TT and UT1 where relevant, TDB evaluation time, observed/predicted/modelled EOP and leap/tzdata version; keep two-part JD to avoid avoidable rounding |
| Observer | `origin` = geocentric/heliocentric/topocentric; for topocentric: WGS84 lat north+/lon east+/height metres, polar motion or explicitly qualified fallback |
| Numerical options | `frame`/equinox, `zodiac` plus named ayanamsa only if supported, `positionMode` apparent/geometric and correction flags, house system, houseFailurePolicy, stationaryBand; do **not** silently replace options |
| Body identity | For each body `canonicalId`, `spkTargetId`, `targetKind` (physical centre/system barycentre/derived point), `centreId`, source segment/manifest coverage, numerical algorithm/reference version |
| Output units | Longitude/latitude/RA/declination degrees, ecliptic lon in [0,360); distance AU, signed longitude/latitude rate degrees per TT day, distance rate AU per TT day, horizon altitude degrees, observers metres; null when legitimately not known |
| Chart geometry | ASC, MC, DSC/IC; house cusps numbered 1–12; house 1 from ASC for Equal or first sign for Whole Sign; MC not forced onto tenth cusp; polar/degenerate results explicitly unavailable |
| Response identity | `engineVersion`, dataset ID and SHA256, time-data versions/assumptions, requested vs effective options, frame/corrections, per-object availability/warnings, origin/target IDs, qualified operating interval/limits |
| Failure behaviour | Structured invalid input, unsupported body/point/house/zodiac, out-of-range time, missing EOP/kernel, undefined polar geometry, request budget exceeded/cancelled, worker unavailable; do not leak internals |
| Data policy | Pinned offline kernel, immutable computation input, explicit checksum+update/rollback; no runtime downloads or silent provider fallback |
| App domain ownership | `ChartDataV1`, `AspectPolicyV1/V2`, `ChartAnalysisV1/V2`, activation functions, V6 saved documents and account access remain application responsibilities |

**Semantics:** a successful multi-object chart may carry `unavailable` for *optional* points, with a precise code/reason. Missing **required** launch bodies or essential time/house inputs must fail the appropriate request or mark the affected chart geometry unavailable according to the approved request policy. Zero degrees/speed is a real mathematical value, never an absent-data marker. Unsupported date options must be rejected, not clamped; a cached result must never masquerade as a successful new calculation.

**Provider/version decision:** introduce a truthful provider-neutral bridge behind Express at P4; select whether to version `ChartRequestV1`/`ChartSnapshotV1`/`ChartCapabilitiesV1` to V2 or add backwards-compatible discriminants with schema updates. Handle previously stored `ephemeris: 'swiss'` requests and V1–V6 documents explicitly. Do not reinterpret an existing saved document as Aria without a user-approved, traceable recalculation. Preserve snapshot IDs, paired-layer provenance and import validation. Current app V6 stores both requested chart inputs rather than an authoritative portable engine result; that does **not** remove recalculation/version risk.

## 5. Independent validation/acceptance proposal

The following are **proposed reference-comparison starting limits**, derived from the [historical 0.1.0 gate](../../validation/README.md), not newly executed results or owner-approved commercial tolerances:

| Observable | Candidate reference threshold | Comparison conditions / exclusions |
| --- | --- | --- |
| Same-JPL-kernel raw SPK position and velocity | ≤ 1 m position and ≤ 1 mm/s velocity | Same target/centre, kernel hash, epoch/scale, ICRS frame and units. Not a planet-centre comparison if only barycentre data exists |
| Apparent direction | ≤ 1 arcsec | Same frame, observer, light-time, deflection limit and aberration; unmatched standard evaluator can disagree by 19.6634 arcsec in historical near-alignment sample |
| Signed longitude rate | ≤ 0.0001 degree per TT day | Same target/frame/correction mode, derivative definition, stationary cases and source kernel; no blanket guarantee near singularities |
| ASC / MC | ≤ 1 arcsec | Same Earth rotation, obliquity, observer and nondegenerate latitude; no claim at poles or for unknown birth time |
| Well-conditioned event root timing | ≤ 10 s in declared fixture windows | Matching TT event definition, endpoints, brackets and independent root solution; no universal search-completeness claim |
| Planet centre vs barycentre | **No accepted threshold yet** | Independent physical centre source required; quantify actual difference by body/date then obtain owner decision |
| Civil time / timezone, unknown time | **Categorical semantic pass/fail**, not angular tolerance | Reproducible gap/overlap, pre-1972, expiry, EOP quality and explicit user uncertainty |
| Application output (wheel/activation) | **Not set here** | Needs P4 end-to-end parity fixtures, approved UX, distinct chart/activation correction defaults and P5 host performance |

These thresholds measure *evaluator agreement under declared identical models*, not absolute ephemeris accuracy, observational/source-model uncertainty, uncertainty from early birth records or a uniform bound between sampled epochs. Candidate tolerances require approval and may be stricter for aspects, house boundaries or near-station motion.

## 6. Integration/operations contract for P4–P6 (not executed)

Proposed topology: **React → existing Express API → persistent private Python worker/service → verified read-only DE442s dataset**. The Express provider abstraction must cover **both** native horoscope routes and activation series/snapshot routes; the existing frontend `EphemerisAdapter` only covers the latter. A capabilities route must distinguish calculation families, supported options, date/EOP coverage, dataset revision and per-object availability. Any future deployment needs separate application-repository authorisation.

Future transport acceptance: bounded requests/queue/epochs and concurrency, cancellable range/search work, stale response protections in UI, worker startup/health and crash recovery, provenance-aware numerical caches (engine version + kernel hash + target kind + frame + time/EOP/zone version + observer/corrections + exact options), non-sensitive logs, no public raw worker, no secret or personal-data logging, deterministic errors, explicit cutover/rollback, and verified elimination of all undeclared provider/fallback paths. Chart clock 1-second updates and 10k-epoch batches require measured P5 performance, not assumptions based on the 77.4 ms historic warm single-request median.

**Outstanding owner gates:** [launch and decision log](p1-launch-scope-and-decisions.md). Until resolved, this is a reviewable draft contract rather than an approved commercial integration specification.
