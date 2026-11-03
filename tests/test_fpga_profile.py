import pytest
from redpitayafpga_mcp.fpga_profile import ila_plan

def test_ila_plan_has_bounded_exact_nets_and_never_programs_hardware():
    planned = ila_plan("clk", [["counter[0]", "counter[1]"], ["valid"]], 1024)
    assert planned["executed"] is False
    assert "create_debug_core" in planned["script"]
    assert "write_debug_probes" in planned["script"]
    assert planned["script"].index("\nopt_design\n") < planned["script"].index("write_debug_probes")
    assert "port_width 2" in planned["script"]
    assert "program_hw" not in planned["script"]
    assert planned["rebuild_required"] is True
    for name in ["clk; exec bad", "[exec bad]", "$secret"]:
        with pytest.raises(ValueError):
            ila_plan(name, [["valid"]], 1024)
    with pytest.raises(ValueError):
        ila_plan("clk", [[]], 1024)
    with pytest.raises(ValueError):
        ila_plan("clk", [["valid"]], 1234)
