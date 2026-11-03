"""Pinned revision and offline ILA plan migrated from RedPitayaCore-MCP."""

from __future__ import annotations

import re
from typing import Any

from .toolchain import tcl_quote
REVISION = "cbecbdd45735a04ad6ccb0094a242a1f820665b8"


def ila_plan(clock_net: str, probes: list[list[str]], depth: int = 1024) -> dict[str, Any]:
    if (
        not 1 <= len(probes) <= 8
        or any(not probe for probe in probes)
        or sum(len(probe) for probe in probes) > 256
    ):
        raise ValueError(
            "Provide 1 to 8 probes, each nonempty, totalling at most 256 exact bit nets"
        )
    names = [clock_net, *(net for probe in probes for net in probe)]
    if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_./\[\]-]{0,255}", net) for net in names):
        raise ValueError("Use exact clock/probe net names, without Tcl expressions or wildcards")
    if type(depth) is not int or depth not in {1024, 2048, 4096, 8192}:
        raise ValueError("ILA depth must be 1024, 2048, 4096 or 8192")

    def selection(net: str) -> str:
        return f"[get_nets -hier -regexp {tcl_quote('^' + re.escape(net) + '$')}]"

    lines = [
        "# Apply only to an open synthesized design before implementation.",
        "# Review probe existence, clock domain, resource use and timing before rebuilding.",
        "create_debug_core rp_ila ila",
        f"set_property C_DATA_DEPTH {depth} [get_debug_cores rp_ila]",
        "set_property port_width 1 [get_debug_ports rp_ila/CLK]",
        f"set rp_clock {selection(clock_net)}",
        'if {[llength $rp_clock] != 1} { error "ILA clock net missing or ambiguous" }',
        "connect_debug_port rp_ila/CLK $rp_clock",
    ]
    for index, probe in enumerate(probes):
        if index:
            lines.append("create_debug_port rp_ila probe")
        lines.extend([f"set rp_probe_{index} {{}}"])
        for net in probe:
            lines.extend(
                [
                    f"set rp_net {selection(net)}",
                    'if {[llength $rp_net] != 1} { error "ILA probe net missing or ambiguous" }',
                    f"lappend rp_probe_{index} [lindex $rp_net 0]",
                ]
            )
        lines.extend(
            [
                f"set_property port_width {len(probe)} [get_debug_ports rp_ila/PROBE{index}]",
                f"connect_debug_port rp_ila/PROBE{index} $rp_probe_{index}",
            ]
        )
    lines.extend(["opt_design", "write_debug_probes -force debug.ltx"])
    return {
        "executed": False,
        "rebuild_required": True,
        "hardware_capture_supported": False,
        "script": "\n".join(lines) + "\n",
        "net_existence_verified": False,
        "note": "ILA insertion changes the design and can change resource use and timing; "
        "this plan neither instruments a live image nor captures real hardware",
    }
