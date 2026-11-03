# RedPitayaFPGA-MCP

Offline FPGA development MCP server extracted from
[RedPitayaCore-MCP](https://github.com/theerayutbo/RedPitayaCore-MCP).

Includes bounded HDL workspace, RTL/XDC editing, Vivado dry-run and opt-in builds,
artifact and report inspection, unapproved manifests and offline ILA Tcl plans.
The original MCP tool names and safety gates are retained. No hardware deployment,
active bitstream verification, MMIO, RF, RX/TX, or board lifecycle tools exist.
FPGA/OS read-only diagnostics and SDR/RX remain in Core-MCP.

## Install

Python 3.11+ required.

```bash
git clone https://github.com/theerayutbo/RedPitayaFPGA-MCP.git
cd RedPitayaFPGA-MCP
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
redpitayafpga-mcp
```

```bash
claude mcp add --scope project --transport stdio redpitaya-fpga -- /absolute/path/to/RedPitayaFPGA-MCP/.venv/bin/redpitayafpga-mcp
```

Configure `RP_PROJECT_ROOT`, `RP_ALLOW_PROJECT_WRITE`, `RP_ALLOW_LOCAL_BUILD`,
`RP_VIVADO_EXECUTABLE` and `RP_BUILD_TIMEOUT` on the MCP server process.
Writes/builds are disabled by default. See [guide](docs/FPGA_DEVELOPMENT.md) and
[security](SECURITY.md). Run tests with `pip install -e '.[dev]'` then `pytest -q`.

The extracted implementation uses the **existing Vivado backend**, not yet
Yosys/Verilator/openXC7. Neither bitstream generation nor a tool exit code
establishes board compatibility, timing closure or hardware safety.
