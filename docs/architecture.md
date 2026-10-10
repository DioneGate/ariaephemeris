# Architecture

One Python distribution uses a src layout. `Ephemeris` owns a verified, read-only JPL handle and orchestrates request-local computations. `models` and `errors` define contracts; `datasets` owns acquisition/provenance; `sources` wraps jplephem centre chains and segment precedence. `time` resolves scales, `frames` wraps ERFA, `positions` applies Aria's correction pipeline, `astrology` calculates chart geometry, and `events` brackets roots. CLI calls the same API; no runtime downloads or chart logging occur.

Polynomial evaluation is delegated to jplephem, not reimplemented. Standards routines are delegated to PyERFA. Skyfield and CSPICE are validation-only evaluators and do not generate Aria outputs. Source arrays are loaded before concurrent requests; caches and mutable search state are request-local. Do not close an engine while another thread is using it.

Original kernels live under an ignored local `.artifacts/` directory. The `install(directory, source=None)` interface supports local/file-backed artefact storage without a paid cloud service. Manifest hashes are immutable identities. Replacement models must receive new manifests and qualification. Small reports and tiny synthetic kernels are committed; production kernels are not.

Extension boundaries: additional source targets require manifests and coverage tests; other astrology algorithms require independently documented definitions; compact storage requires a decoder passing the reference gates. An HTTP adapter or private UI belongs outside the core. No future public method is represented by a successful dummy result.
