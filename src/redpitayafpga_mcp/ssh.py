"""Fixed-command, read-only SSH runner (adapted from RedPitayaCore-MCP, MIT).

Only literal commands from an allowlist can run. Key mode uses BatchMode; opt-in password mode
passes the secret to OpenSSH through SSH_ASKPASS, so it never appears in argv, files or logs.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import shutil
import tempfile
from collections.abc import Iterable
from typing import Any

from .config import Settings, ssh_password_for

MAX_RESPONSE = 65536


def _make_askpass_helper() -> tuple[str, str]:
    """Private 0700 dir with a helper printing $RP_ASKPASS_SECRET (no secret on disk)."""
    askpass_dir = tempfile.mkdtemp(prefix="rpfpga-askpass-")
    helper = os.path.join(askpass_dir, "askpass")
    with open(helper, "w", encoding="ascii") as handle:
        handle.write("#!/bin/sh\nprintf '%s\\n' \"$RP_ASKPASS_SECRET\"\n")
    os.chmod(helper, 0o700)  # nosec B103 - owner-only helper in a private temp dir
    return askpass_dir, helper


async def run_allowlisted(
    config: Settings, command: str, allowlist: Iterable[str]
) -> dict[str, Any]:
    if config.mode != "live" or config.host is None:
        raise ValueError("Hardware access requires explicit live mode and RP_HOST")
    if command not in set(allowlist) or not config.ssh_user:
        raise ValueError("SSH requires an allowlisted command and RP_SSH_USER")
    password = ssh_password_for(config)
    askpass_dir: str | None = None
    env: dict[str, str] | None = None
    if password is None:
        auth = [
            "-o",
            "BatchMode=yes",
            "-o",
            "PasswordAuthentication=no",
            "-o",
            "KbdInteractiveAuthentication=no",
        ]
    else:
        askpass_dir, helper = _make_askpass_helper()
        auth = [
            "-o",
            "BatchMode=no",
            "-o",
            "PreferredAuthentications=password",
            "-o",
            "PubkeyAuthentication=no",
            "-o",
            "KbdInteractiveAuthentication=no",
            "-o",
            "NumberOfPasswordPrompts=1",
        ]
        env = {
            **os.environ,
            "SSH_ASKPASS": helper,
            "SSH_ASKPASS_REQUIRE": "force",
            "DISPLAY": os.environ.get("DISPLAY", "none"),
            "RP_ASKPASS_SECRET": password,
        }
    try:
        process = await asyncio.create_subprocess_exec(
            "ssh",
            "-F",
            "/dev/null",
            "-T",
            "-n",
            "-p",
            str(config.ssh_port),
            *auth,
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            "ClearAllForwardings=yes",
            "-o",
            "PermitLocalCommand=no",
            "-o",
            f"ConnectTimeout={max(1, int(config.timeout))}",
            f"{config.ssh_user}@{config.host}",
            command,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            if process.stdout is None:
                raise RuntimeError("SSH stdout pipe unavailable")
            async with asyncio.timeout(config.timeout + 1):
                output = bytearray()
                while chunk := await process.stdout.read(4096):
                    output.extend(chunk)
                    if len(output) > MAX_RESPONSE:
                        raise ValueError("SSH response too large")
                code = await process.wait()
            return {
                "available": code == 0,
                "exit_code": code,
                "text": output.decode("utf-8", errors="replace").replace("\x00", "").strip(),
            }
        finally:
            if process.returncode is None:
                with contextlib.suppress(ProcessLookupError):
                    process.kill()
                await process.wait()
    finally:
        if askpass_dir is not None:
            shutil.rmtree(askpass_dir, ignore_errors=True)
