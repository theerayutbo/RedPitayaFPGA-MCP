"""Offline FPGA workspace configuration; no device target or transport."""
from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path


def _flag(name: str) -> bool:
    value = os.environ.get(name, "false").lower()
    if value not in {"true", "false", "1", "0"}:
        raise ValueError(f"{name} must be true/false or 1/0")
    return value in {"true", "1"}


@dataclass(frozen=True)
class Settings:
    project_root: Path | None = None
    allow_project_write: bool = False
    allow_local_build: bool = False
    vivado_executable: Path | None = None
    build_timeout: float = 300

    def __post_init__(self) -> None:
        for path in (self.project_root, self.vivado_executable):
            if path is not None and not path.is_absolute():
                raise ValueError("Operator paths must be absolute")
        if not math.isfinite(self.build_timeout) or not 0.1 <= self.build_timeout <= 3600:
            raise ValueError("RP_BUILD_TIMEOUT must be finite, from 0.1 to 3600 seconds")

    @classmethod
    def from_env(cls) -> Settings:
        root = os.environ.get("RP_PROJECT_ROOT")
        exe = os.environ.get("RP_VIVADO_EXECUTABLE")
        return cls(
            project_root=Path(root) if root else None,
            allow_project_write=_flag("RP_ALLOW_PROJECT_WRITE"),
            allow_local_build=_flag("RP_ALLOW_LOCAL_BUILD"),
            vivado_executable=Path(exe) if exe else None,
            build_timeout=float(os.environ.get("RP_BUILD_TIMEOUT", "300")),
        )
