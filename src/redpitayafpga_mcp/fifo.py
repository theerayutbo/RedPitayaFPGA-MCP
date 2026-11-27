"""sdr_transceiver FIFO fill levels from its status registers (read-only, bitstream-gated).

Address map of Pavel Demin's sdr_transceiver (red-pitaya-notes, projects/sdr_transceiver):
the server maps cfg at 0x40000000, sts at 0x41000000 and the FIFO port at 0x42000000 for channel 1
(0x80000000 / 0x81000000 / 0x82000000 for channel 2). The 32-bit status word packs the RX FIFO
read_count (low 16 bits) and the TX FIFO write_count (high 16 bits); the FIFOs hold 8192 words.

Safety rules enforced here:
- Only the two status words are read, with /dev/mem opened O_RDONLY and mapped PROT_READ.
- The FIFO ports (0x42000000 / 0x82000000) are NEVER read: a read pops RX samples.
- Nothing is read unless the sdr-transceiver server process is running on the board, because
  these addresses are only defined while its bitstream is loaded; the standard v0.94 map differs.
- Nothing is ever written.
"""

from __future__ import annotations

import re
from typing import Any

from .config import Settings
from .ssh import run_allowlisted

FIFO_DEPTH = 8192
NEAR_FULL = 7680  # 15/16 of the RX FIFO: an overrun is imminent or has happened

# One literal Python program run on the board. It checks the process table before touching
# /dev/mem and prints only key=value lines. It contains no write calls and no FIFO-port address.
_PROGRAM = (
    "import mmap,os,struct\n"
    "names=set()\n"
    "for p in os.listdir('/proc'):\n"
    "    if p.isdigit():\n"
    "        try:\n"
    "            names.add(open('/proc/'+p+'/comm').read().strip())\n"
    "        except OSError:\n"
    "            pass\n"
    "if 'sdr-transceiver' not in names:\n"
    "    print('gate=closed')\n"
    "else:\n"
    "    fd=os.open('/dev/mem',os.O_RDONLY|os.O_SYNC)\n"
    "    for ch,base in (('ch1',0x41000000),('ch2',0x81000000)):\n"
    "        m=mmap.mmap(fd,mmap.PAGESIZE,mmap.MAP_SHARED,mmap.PROT_READ,offset=base)\n"
    "        print(ch+'_sts='+str(struct.unpack('<I',m[0:4])[0]))\n"
    "        m.close()\n"
    "    os.close(fd)\n"
)
FIFO_STATUS_COMMAND = 'python3 -c "' + _PROGRAM.replace('"', '\\"') + '"'
ALLOWLIST = (FIFO_STATUS_COMMAND,)

_LINE = re.compile(r"^(gate=closed|ch[12]_sts=\d{1,10})$")


def parse_fifo_status(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if lines == ["gate=closed"]:
        return {
            "available": False,
            "reason": "sdr-transceiver is not running; registers not read (map would not apply)",
        }
    if len(lines) != 2 or not all(_LINE.match(line) for line in lines):
        return {"available": False, "reason": "unexpected FIFO status output"}
    out: dict[str, Any] = {"available": True, "fifo_depth_words": FIFO_DEPTH, "channels": {}}
    for line in lines:
        key, _, value = line.partition("=")
        word = int(value)
        if word > 0xFFFFFFFF:
            return {"available": False, "reason": "status word out of range"}
        rx, tx = word & 0xFFFF, word >> 16
        if rx > 2 * FIFO_DEPTH or tx > 2 * FIFO_DEPTH:
            return {"available": False, "reason": "fill level implausible for this bitstream"}
        out["channels"][key[:3]] = {
            "status_word": word,
            "rx_fill": rx,
            "tx_fill": tx,
            "rx_near_overrun": rx >= NEAR_FULL,
        }
    out["note"] = (
        "Instantaneous FIFO fill levels. RX near 8192 means samples are being dropped; "
        "TX at 0 while transmitting means the DAC is sending zeros (underrun)."
    )
    return out


async def read_fifo_status(config: Settings) -> dict[str, Any]:
    if config.mode != "live" or not config.ssh_user:
        return {"available": False, "reason": "Live mode with RP_SSH_USER is required"}
    try:
        result = await run_allowlisted(config, FIFO_STATUS_COMMAND, ALLOWLIST)
    except (OSError, TimeoutError, ValueError):
        return {"available": False, "reason": "SSH unavailable, timed out or response too large"}
    if not result.get("available"):
        return {
            "available": False,
            "reason": "remote read failed (python3 or /dev/mem unavailable)",
        }
    return parse_fifo_status(str(result.get("text", "")))
