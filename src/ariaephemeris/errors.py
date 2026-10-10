# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Public machine-readable failures."""


class AriaError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": str(self)}
