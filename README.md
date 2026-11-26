# RedPitayaFPGA-MCP

Optional FPGA development extension for [RedPitayaCore-MCP](https://github.com/theerayutbo/RedPitayaCore-MCP).

**Core-first architecture:** Core owns PS software development, device diagnostics, existing PL operation and eventual approved image deployment. FPGA-MCP owns HDL/RTL, FPGA IP, clocks, AXI hardware interfaces, offline simulation, synthesis, implementation, timing reports and bitstream packaging. PS drivers belong to Core even when a custom PL design is needed. RTL simulation also belongs here when it does not require Vivado.

## Install (offline)
```sh
python -m pip install -e '.[dev]'
redpitayafpga-mcp
```

Set RP_PROJECT_ROOT to an operator-selected absolute existing local directory. RP_ALLOW_PROJECT_WRITE and RP_ALLOW_LOCAL_BUILD default to false. Real builds also require RP_VIVADO_EXECUTABLE, explicit per-call trusted-code acknowledgement and a licensed isolated host with no route to the board or device/JTAG access. Dry runs need no Vivado installation. Build status is not timing closure or board compatibility evidence.

The extracted tools support bounded workspace read/write, build planning and jobs, local reports, artifact hashing, unapproved image manifests, offline ILA plans and source-pinned register/hardware proposals. Hardware proposals never execute. The source-pinned SDR map is not a universal map. Live diagnostics and actual PS–PL runtime belong to Core; this server has no board network adapter, live MMIO, programming or TX tool.

## Handoff
Exchange a reviewed versioned manifest with board/part/revision, hashes, register map, ABI, clock/reset assumptions, artifact provenance, validation evidence and driver compatibility. Existing manifest v1 is only a proposal, not approval. Neither project implements approved live loading yet. Do not remove legacy Core FPGA tools until this extraction passes CI and parity review; no simultaneous deployment ownership.

## Provenance
Workspace, toolchain, profile, and FPGA tool code plus unit tests are derived from RedPitayaCore-MCP commit 641c4b4fe2dee56689f0cfb8695c37b478441a32, MIT, with live diagnostics removed and an independent offline configuration/entry point. Tests are provided; actual Vivado and board tests are not claimed.
