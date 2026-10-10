# Implemented algorithms and provenance

## SPK and time

jplephem 2.24 evaluates SPK Type 2 Chebyshev position/analytic derivative and Type 3 position/velocity. Aria resolves each target's highest-precedence covering segment recursively through its centre chain. The algorithm follows the [NAIF SPK required reading](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/spk.html), including fallback on earlier segments. Dates are passed as split TDB JDs. Type 3 stored km/s becomes km/day.

ERFA provides UTC→TAI→TT, TT↔TDB (geocentric dtdb), UT1 conversion and IAU standards rotations. See [ERFA source routines](https://github.com/liberfa/erfa/tree/master/src) `utctai`, `taitt`, `dtdb`, `pnm06a`, `ecm06`, `c2t06a`, `gst06a`. ERFA is derived from SOFA with its documented independent terms. Aria retains their notices. Non-strict delta-T polynomials are transcribed from [NASA's Espenak/Meeus publication](https://eclipse.gsfc.nasa.gov/SEcat5/deltatpoly.html), restricted to 1900–2149; they are not modern EOP predictions.

## Apparent positions and rates

From observer state o(t), iterate τ = |r(t−τ)−o(t)|/c, c = 299792.458 km/s, with at most 12 iterations and 1e−12-day change tolerance. Source padding covers retarded time and derivative offsets. Deflection uses ERFA `ld` with finite source/deflector geometry for Sun, Jupiter and Saturn and bounded closest light-path approach. Its fixed dlim values are 1e−6, 3e−9 and 3e−10 respectively. For unit ray p, deflector-to-observer e, deflector-to-source q, the added unit vector is (2GM/(c²r max(q·(q+e),dlim))) [(p·q)e−(p·e)q]. The limiter defines the alignment convention, including non-observable rays through a body; no physical imaging claim is made there. Aberration uses ERFA `ab`, observer barycentric velocity/c, source unit direction and observer–Sun distance. Atmosphere and planetary-centre corrections are excluded. These conventions are independently compared with [Skyfield's astrometric/apparent pipeline](https://rhodesmill.org/skyfield/positions.html), adapted to the same finite-source deflection limiter by a separately implemented vector equation in `tools/reference/skyfield_match.py`. It does not call ERFA ld or Aria positions. Skyfield still supplies its own light-time, aberration and frame pipeline. Unmodified Skyfield discrepancies near alignment are separately recorded.

For geometric output v, dv/dt from kernel velocities plus dR/dt frame motion, longitude derivative is (x y′ − y x′)/(x²+y²), converted to degrees/day. Apparent correction derivatives use the five-point centred formula [f(−2h)−8f(−h)+8f(h)−f(2h)]/(12h), h=0.001 TT day, on circular offsets about the central longitude. The step and truncation error are checked against independent Skyfield differences with another step. This numerical derivative is an explicit implementation choice, not a claim of a fully analytic apparent-state derivative.

## Chart geometry

These formulas are Aria's independent spherical derivation, not a translation of a third-party astrology engine. Set θ = GST06A(TT,UT1)+east longitude, φ=geodetic latitude, ε=true obliquity. In true equatorial axes use zenith z=(cosφ cosθ, cosφ sinθ, sinφ), east e=(−sinθ,cosθ,0), ecliptic normal n=(0,−sinε,cosε). ASC is the direction z×n selected by positive dot with e; MC is e×n selected toward the upper meridian. Rotate to ecliptic axes and apply atan2. Aria's closed-form equations are independently tested against this vector-plane construction using Skyfield's sidereal time and obliquity. DSC=ASC+180°, IC=MC+180°. Degenerate norms/east orientation and poles are rejected.

Equal cusps: c[k]=(ASC+30k) mod360. Whole-sign cusps: c[k]=(30 floor(ASC/30)+30k) mod360, k=0..11. House assignment uses circular intervals [c[k],c[k+1]); sign index=floor(λ/30). Aspect separation is |wrap180(λa−λb)|; orb is |separation−angle|. Applying iff residual×residual derivative<0; separating iff >0; near exactness or low rate gives indeterminate.

## Event search

Sample at no more than min(request step,0.25)/4 days. Locate relative-longitude rate sign changes with bounded bisection and subdivide longitude brackets at those extrema. Unwrap each local phase continuously; enumerate 30° ingress targets or both branches of aspect angle; refine each crossing by bisection. Add exact/near-tolerance endpoints and recognised grazing aspect extrema; deduplicate. Report residual, iterations, bracket width and slope conditioning. Bisection is bounded by machine resolution and configured iteration limits.

Seeded grids, denser independently scanned Skyfield functions and SciPy Brent refinement test physical-event completeness in declared windows. This procedure cannot formally exclude arbitrarily many oscillations hidden within a scan cell; it is qualified empirically for the supported bodies, not as a universal root-finding theorem. Synthetic regressions test wrap, recrossing, tangency, budget and cancellation behaviour.
