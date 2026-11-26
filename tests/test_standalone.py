from redpitayafpga_mcp.config import Settings
from redpitayafpga_mcp.fpga_tools import FPGAService
from redpitayafpga_mcp.server import build_server


async def test_standalone_offline_surface():
    server = build_server(Settings())
    names = {tool.name for tool in await server.list_tools()}
    assert "rp_fpga_build" in names
    assert "rp_fpga_write_source" in names
    assert "rp_fpga_diagnostics" not in names
    assert not any(name.startswith(("rp_rx_", "rp_tx_", "rp_ps_")) for name in names)
    caps = FPGAService(Settings()).capabilities()
    assert not caps["live_mmio"]
    assert not caps["live_fpga_programming"]
    assert not caps["live_tx"]
