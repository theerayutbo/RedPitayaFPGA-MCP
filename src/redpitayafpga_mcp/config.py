"""Operator settings from the environment. Mock mode is the default and never contacts a board."""

from __future__ import annotations

import ipaddress
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, cast

# Public, documented Red Pitaya OS factory login; used only on explicit opt-in.
RED_PITAYA_FACTORY_PASSWORD = "root"  # noqa: S105  # nosec B105


@dataclass(frozen=True)
class Settings:
    mode: Literal["mock", "live"] = "mock"
    host: str | None = None
    ssh_user: str | None = None
    ssh_port: int = 22
    ssh_auth: Literal["key", "password"] = "key"
    ssh_password: str | None = field(default=None, repr=False)
    ssh_use_factory_default: bool = False
    timeout: float = 5.0

    def __post_init__(self) -> None:
        if self.mode not in {"mock", "live"}:
            raise ValueError("RP_MODE must be mock or live")
        if self.mode == "live" and not self.host:
            raise ValueError("Live mode requires RP_HOST")
        if self.host is not None:
            address = ipaddress.IPv4Address(self.host)
            if address.is_multicast or address.is_unspecified:
                raise ValueError("RP_HOST must be a unicast IPv4 address")
        if self.ssh_user is not None and not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", self.ssh_user):
            raise ValueError("RP_SSH_USER is not a valid user name")
        if not 1 <= self.ssh_port <= 65535:
            raise ValueError("RP_SSH_PORT must be 1-65535")
        if self.ssh_auth not in {"key", "password"}:
            raise ValueError("RP_SSH_AUTH must be key or password")
        password_set = bool(self.ssh_password or self.ssh_use_factory_default)
        if self.ssh_auth == "password" and not password_set:
            raise ValueError(
                "RP_SSH_AUTH=password needs RP_SSH_PASSWORD or RP_SSH_USE_FACTORY_DEFAULT=true"
            )

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env

        def flag(name: str) -> bool:
            return env.get(name, "").strip().lower() in {"1", "true", "yes"}

        return cls(
            mode=cast(Literal["mock", "live"], env.get("RP_MODE", "mock")),
            host=env.get("RP_HOST") or None,
            ssh_user=env.get("RP_SSH_USER") or None,
            ssh_port=int(env.get("RP_SSH_PORT", "22")),
            ssh_auth=cast(Literal["key", "password"], env.get("RP_SSH_AUTH", "key")),
            ssh_password=env.get("RP_SSH_PASSWORD") or None,
            ssh_use_factory_default=flag("RP_SSH_USE_FACTORY_DEFAULT"),
            timeout=float(env.get("RP_TIMEOUT", "5")),
        )


def ssh_password_for(config: Settings) -> str | None:
    """Password for password-mode SSH, or None in key mode. Never log or return it."""
    if config.ssh_auth != "password":
        return None
    if config.ssh_password:
        return config.ssh_password
    return RED_PITAYA_FACTORY_PASSWORD if config.ssh_use_factory_default else None
