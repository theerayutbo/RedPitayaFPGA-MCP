"""Operator-selected local FPGA workspace/build settings. No hardware transport."""
from __future__ import annotations
import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

def _flag(env: Mapping[str, str], key: str) -> bool:
    value = env.get(key, "false").lower()
    if value not in {"true", "false", "1", "0"}:
        raise ValueError(f"{key} must be true/false or 1/0")
    return value in {"true", "1"}

@dataclass(frozen=True)
class Settings:
    project_root: Path | None = None
    allow_project_write: bool = False
    allow_local_build: bool = False
    vivado_executable: Path | None = None
    build_timeout: float = 300

    def __post_init__(self) -> None:
        if self.project_root is not None and not self.project_root.is_absolute():
            raise ValueError("RP_PROJECT_ROOT must be an absolute local project directory")
        if self.vivado_executable is not None and not self.vivado_executable.is_absolute():
            raise ValueError("RP_VIVADO_EXECUTABLE must be an absolute operator-selected path")
        if not math.isfinite(self.build_timeout) or not 0.1 <= self.build_timeout <= 3600:
            raise ValueError("RP_BUILD_TIMEOUT must be finite, from 0.1 to 3600 seconds")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env
        return cls(
            project_root=Path(env["RP_PROJECT_ROOT"]) if env.get("RP_PROJECT_ROOT") else None,
            allow_project_write=_flag(env, "RP_ALLOW_PROJECT_WRITE"),
            allow_local_build=_flag(env, "RP_ALLOW_LOCAL_BUILD"),
            vivado_executable=Path(env["RP_VIVADO_EXECUTABLE"])
            if env.get("RP_VIVADO_EXECUTABLE") else None,
            build_timeout=float(env.get("RP_BUILD_TIMEOUT", "300")),
        )
