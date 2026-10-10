# Contributing

Use Python 3.12 and `requirements/development.lock`, then install the repository editable with no dependency changes. Run Ruff, mypy, fast tests and build checks. Changes to numerics must run the real-kernel reference qualification, record the kernel SHA-256, evaluator versions and altered conventions, and update release evidence. Missing data never counts as a reference pass.

Keep request state local and dataset files immutable. Do not commit birth details, secrets, production kernels, downloaded artefacts or generated packs. Write original algorithms from cited independent mathematics; no Swiss code, wrappers or .se1 files. Planned features need defined semantics and reference gates before becoming public APIs. Retain third-party notices and update the exact-version inventory when dependencies change.

New contributions are under Apache-2.0; include SPDX identifiers and preserve the actual copyright holder. Attribution in AUTHORS.md does not transfer ownership. Keep UK English in documentation. Package publication and deployment are manual release decisions, not CI side effects.
