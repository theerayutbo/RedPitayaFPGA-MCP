from __future__ import annotations

import asyncio

import pytest

from redpitayafpga_mcp.config import Settings, ssh_password_for
from redpitayafpga_mcp.fifo import (
    ALLOWLIST,
    FIFO_STATUS_COMMAND,
    parse_fifo_status,
    read_fifo_status,
)
from redpitayafpga_mcp.server import TOOLS, build_server


def test_parse_two_channels():
    r = parse_fifo_status("ch1_sts=196613\nch2_sts=8000\n")  # ch1: tx 3, rx 5; ch2: rx 8000
    assert r["available"] is True
    assert r["channels"]["ch1"] == {
        "status_word": 196613,
        "rx_fill": 5,
        "tx_fill": 3,
        "rx_near_overrun": False,
    }
    assert r["channels"]["ch2"]["rx_near_overrun"] is True


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "ch1_sts=1",
        "ch1_sts=1\nch3_sts=2",
        "ch1_sts=-1\nch2_sts=1",
        "ch1_sts=99999999999\nch2_sts=1",
        "rx=1\ntx=2",
        "ch1_sts=4294967295\nch2_sts=0",
    ],
)
def test_parse_rejects_untrusted_or_implausible(bad):
    assert parse_fifo_status(bad)["available"] is False


def test_gate_closed_means_nothing_was_read():
    r = parse_fifo_status("gate=closed")
    assert r["available"] is False and "not running" in r["reason"]


def test_program_is_read_only_and_never_touches_fifo_ports():
    cmd = FIFO_STATUS_COMMAND
    assert cmd in ALLOWLIST
    for forbidden in (
        "O_RDWR",
        "O_WRONLY",
        "PROT_WRITE",
        "0x42000000",
        "0x82000000",
        "0x40000000",
        "0x80000000",
        ".write(",
        "monitor",
        ">",
    ):
        assert forbidden not in cmd
    assert "O_RDONLY" in cmd and "PROT_READ" in cmd and "sdr-transceiver" in cmd
    assert cmd.index("sdr-transceiver") < cmd.index("/dev/mem")  # gate before any mapping


async def test_live_without_ssh_user_is_unavailable():
    r = await read_fifo_status(Settings(mode="live", host="192.0.2.10"))
    assert r["available"] is False


def test_password_mode_requires_explicit_choice():
    with pytest.raises(ValueError):
        Settings(mode="live", host="192.0.2.10", ssh_user="root", ssh_auth="password")
    cfg = Settings(
        mode="live",
        host="192.0.2.10",
        ssh_user="root",
        ssh_auth="password",
        ssh_use_factory_default=True,
    )
    assert ssh_password_for(cfg) == "root" and "root'" not in repr(cfg).split("ssh_user")[0]


def test_tools_are_exactly_the_allowlist_and_read_only():
    server = build_server(Settings())
    tools = asyncio.run(server.list_tools())
    assert {t.name for t in tools} == TOOLS
    assert all(t.annotations is not None and t.annotations.readOnlyHint for t in tools)
