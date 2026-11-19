# RM-001/010 original-source reference

`specification.json` was committed before capture at `df381bdf` and binds the
36 candidate station centres to the JPL-only 009 discovery catalogue. `source.json`
retains 400 new geometric component states and 2,340 airless apparent ICRF rays.
`components.json` retains the four roles at 25 original TDB dates per remaining
planet, with original raw responses, exact queries and SHA-256 identities.

`direct-offset-specification.json`, frozen separately at `a2272bc`, adds 100
physical centre-to-parent vectors in `direct-offset-source.json`. They distinguish
true direct-query offset differences from mixed reference chains. The original
source files are never refreshed. All acquisition is explicit; routine checks
verify and replay the frozen source offline. Original `raw/*.txt` responses and
`raw/*.json` receipts remain intact.

Reference station roots use a continuous C2 cubic spline on each predeclared
JPL-only grid. The initial non-continuous-panel diagnosis is preserved in
`docs/validation/wp57-initial-local-cubic-diagnostic.json` and the complete initial
report in Git commit `221ecf1`. No physical uncertainty bound is inferred from
finite interpolation agreement or source-model differences.

See [scientific interpretation](../../../../docs/roadmaps/001-engine-development/p1-wp57-model-uncertainty.md)
and [machine evidence](../../../../docs/validation/wp57-model-uncertainty.json).
