# Numerical conventions, version 1

All numerical calculations use float64. Longitudes/RA are degrees in [0,360), latitude/declination degrees, distance AU (149597870.700 km), rates degrees per TT day. Raw states are barycentric J2000/ICRS-aligned km and km/day evaluated in TDB. Returned `vector_icrs_au` is the observer-to-target direction/distance before output-frame rotation. Equatorial outputs always use the true equator/equinox of date; `frame` controls the longitude/latitude output only.

## Time

`TimeInput` accepts exactly one ISO `value` or two-part `jd`, an explicit scale (UTC default, TT/TDB/UT1 supported), optional IANA timezone/fold, DUT1 or delta-T. The calendar is proleptic Gregorian; Julian-calendar input is not implemented. TT/TDB use ERFA's geocentric Fairhead–Bretagnon approximation, with topocentre-dependent TDB terms omitted. Split dates retain precision in source evaluation; event searches use a scalar JD with about 40 microsecond granularity near J2000, below their 0.1-second default tolerance.

UTC uses the pinned IERS leap history (matching the installed ERFA table), including actual leap seconds. Pre-1972 civil UTC is rejected. After 2027-06-28, strict UTC fails; non-strict assumes no subsequent leap seconds with a warning. TT/TDB can cover the entire operational interval without inventing UTC. Timezone rules use the operating system IANA database; pin that separately for civil-time reproducibility.

Strict Earth rotation requires user DUT1 with UTC, or delta-T = TT−UT1. UT1 input requires delta-T for TT. Non-strict missing values use the explicitly identified Espenak/Meeus 2006 piecewise polynomial. These values are models, not observed EOP, and no absolute angle-accuracy promise follows from them. Topocentric strict mode also requires xp/yp in arcseconds; non-strict sets missing polar motion to zero with a warning. Small rate differences advance UT1 alongside TT, assuming locally constant supplied EOP.

## Origins, centres and frames

Geocentric observer is target 399, heliocentric observer 10, topocentric observer Earth plus a WGS84 site with IAU Earth orientation. Earth from Earth's origin and Sun from Sun's origin are undefined. Longitude/latitude observer ranges are ±90°/±180°. No atmospheric refraction is applied.

Targets: Sun 10, Moon 301, Mercury 199, Venus 299, Earth 399; Mars 4, Jupiter 5, Saturn 6, Uranus 7, Neptune 8 and Pluto 9 are **planetary-system barycentres**, reported as such. The release qualifies those targets against those same targets, not planet-centre substitutions. No planet-centre error budget or centre-equivalence claim is made.

`icrs` uses identity rotation; `ecliptic_j2000` uses ERFA ecm06 at J2000; `mean_ecliptic_of_date` uses ecm06(TT); default `true_ecliptic_of_date` uses pnm06a followed by the true-obliquity x rotation. This convention matches Skyfield's true ecliptic frame closely, with small differences in its precession/nutation implementation measured separately. IAU 2006 precession, IAU 2000A nutation, GST06A sidereal time are used. Tropical coordinates refer to the equinox.

Geometric mode uses simultaneous states. Apparent mode iterates light-time, applies Sun/Jupiter/Saturn deflection and relativistic observer aberration. Every correction is recorded. Deflection uses finite-source ERFA ld with fixed dlim values: Sun 1e−6, Jupiter 3e−9, Saturn 3e−10. This is a declared numerical extension near alignment, not a prediction of visible images through an occulting body. Unmodified Skyfield has different alignment cutoffs; reference qualification matches this convention explicitly. Heliocentric output requires geometric mode; apparent heliocentric requests raise INVALID_REQUEST. Topocentric direction has independent sample checks but is not covered by the broad geocentric gate.

## Astrology and events

Equal house one begins at ASC and advances 30°; whole-sign house one begins at ASC's sign boundary. MC is independent of house ten. Membership is start-inclusive/end-exclusive. Signs use floor(longitude/30). No angular rounding occurs in the core. Applying aspects decrease the absolute circular residual; separating aspects increase it. Exact/near-static cases are indeterminate. Motion uses a configurable stationary band, not an exact-root claim.

ASC selects the rising intersection of horizon and ecliptic; MC selects the meridian branch above the equatorial horizon. DSC/IC are antipodes. Polar/degenerate intersections raise HOUSE_UNDEFINED, rather than selecting another house system.

Events always use apparent geocentric tropical true-of-date longitude and TT results. Bounded scans are subdivided at detected rate zeros; wrapping and retrograde recrossings are handled. Searches include both endpoints, deduplicate within twice the tolerance, and expose a finite work budget/cancellation. Conditioning is based on local residual slope. Tangential contacts may be recognised without a crossing; timing certification is limited to measured windows and well-conditioned roots. A maximum scan step is an empirical physical-body policy, not a mathematical guarantee for arbitrary functions.
