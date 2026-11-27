"""MCP server: read-only FPGA register diagnostics for Red Pitaya (mock by default)."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import __version__
from .config import Settings
from .fifo import read_fifo_status

READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)
TOOLS = frozenset({"fpga_sdr_fifo_status", "fpga_profile"})


def build_server(config: Settings | None = None) -> FastMCP:
    cfg = config or Settings.from_env()
    mcp = FastMCP("redpitaya-fpga")

    @mcp.tool(annotations=READ_ONLY)
    def fpga_profile() -> dict[str, Any]:
        """Server version and mode; no board access."""
        return {
            "version": __version__,
            "mode": cfg.mode,
            "ssh_enabled": cfg.ssh_user is not None,
            "ssh_auth": cfg.ssh_auth,
        }

    @mcp.tool(annotations=READ_ONLY)
    async def fpga_sdr_fifo_status() -> dict[str, Any]:
        """sdr_transceiver RX/TX FIFO fill levels from its status registers. Read-only;
        refuses unless the sdr-transceiver server (so its bitstream) is running; never reads
        FIFO data."""
        if cfg.mode == "mock":
            return {
                "mode": "mock",
                "simulated": True,
                "available": True,
                "channels": {
                    "ch1": {"status_word": 0, "rx_fill": 0, "tx_fill": 0, "rx_near_overrun": False}
                },
            }
        return {"mode": "live", **await read_fifo_status(cfg)}

    return mcp


def main() -> None:
    build_server().run()
