# Security policy

Offline FPGA development only. No bitstream upload, live MMIO, JTAG, hardware
programming, RF transmission or TX tools exist in this repository.

Local source writes require `RP_ALLOW_PROJECT_WRITE=true`. Real Vivado builds require
`RP_ALLOW_LOCAL_BUILD=true`, an absolute `RP_VIVADO_EXECUTABLE`, and per-call
`acknowledge_trusted_code=true`. HDL, XDC, Tcl, vendor tools and simulation can
execute trusted code: use an isolated host with no board network/USB/JTAG access.

Hashes do not prove board compatibility. Report vulnerabilities privately on GitHub.
