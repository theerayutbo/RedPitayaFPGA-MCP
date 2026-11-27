# RedPitayaFPGA-MCP

Read-only, **bitstream-aware** FPGA register diagnostics for Red Pitaya, exposed over the Model
Context Protocol. Mock mode is the default and never contacts a board. The companion project
[RedPitayaCore-MCP](https://github.com/theerayutbo/RedPitayaCore-MCP) covers the radio, board health
and calibration.

## Why bitstream-aware

A register address means something only for the bitstream that is loaded. The standard Red Pitaya
v0.94 map does not apply under Pavel Demin's `sdr_transceiver`. Its AXI hub decodes few address
bits, so v0.94 addresses alias onto its configuration register. Some reads also have side effects:
reading the `sdr_transceiver` FIFO port pops RX samples. This server therefore reads only fixed,
documented, side-effect-free status addresses, and only after confirming on the board which
application is running. It never writes.

## Tools

| Tool | What it does |
|---|---|
| `fpga_profile` | Version and mode. No board access. |
| `fpga_sdr_fifo_status` | `sdr_transceiver` RX/TX FIFO fill levels from the status words at 0x41000000 (ch1) and 0x81000000 (ch2). Opens `/dev/mem` O_RDONLY with PROT_READ. Refuses (`gate=closed`) unless the `sdr-transceiver` process is running. Never touches 0x42000000 or 0x82000000. |

An RX fill level near 8192 means samples are being dropped (overrun). A TX fill level of 0 while
transmitting means the DAC is sending zeros (underrun).

## Configuration

| Variable | Meaning |
|---|---|
| `RP_MODE` | `mock` (default) or `live` |
| `RP_HOST` | board IPv4 address (live) |
| `RP_SSH_USER` | needed for live reads |
| `RP_SSH_AUTH` | `key` (default, BatchMode) or `password` (opt-in) |
| `RP_SSH_PASSWORD` / `RP_SSH_USE_FACTORY_DEFAULT=true` | password-mode secret, or the documented factory login (`root`/`root`) |

In password mode the secret reaches OpenSSH through `SSH_ASKPASS` and never appears in argv, files
or logs. Host keys are checked strictly in every mode. The remote side needs `python3` (present on
Red Pitaya OS 2.x).

## Sources

- `sdr_transceiver` address map and status word: pavel-demin/red-pitaya-notes,
  `projects/sdr_transceiver/server/sdr-transceiver.c` (mmap of cfg/sts/fifo), `trx.tcl` (status
  concat of RX read_count and TX write_count), `cores/axi_hub.v` (FIFO read pops data).
- Red Pitaya `monitor` utility documentation: reads and writes via `/dev/mem`, and a warning about
  interference with running applications.

## Licence

MIT. The SSH runner is adapted from RedPitayaCore-MCP (MIT).
