"""
Tool Runner - Execute external Kali tools via subprocess with output streaming
"""

import re
import subprocess
import shutil
import threading
from typing import Callable, Optional, List, Dict
from pathlib import Path

# ANSI escape codes - strip so UI shows plain text (whatweb, nmap, etc. use colors)
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|[\x1b\x9b]")
# Fallback: [1m, [0m etc. when ESC is stripped (e.g. copy/paste, JSON)
_ANSI_LITERAL_RE = re.compile(r"\[[0-9;]+m")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences for clean display in UI."""
    s = _ANSI_RE.sub("", text)
    s = _ANSI_LITERAL_RE.sub("", s)
    return s


def check_tool_available(tool_name: str, tool_path: Optional[str] = None) -> bool:
    if tool_path:
        return Path(tool_path).exists() or shutil.which(tool_path) is not None
    return shutil.which(tool_name) is not None


def resolve_tool_command(phase: dict) -> Optional[str]:
    tool_path = phase.get("tool_path")
    if tool_path and check_tool_available(phase["tool"], tool_path):
        phase["available"] = True
        return phase["command"]
    if check_tool_available(phase["tool"]):
        phase["available"] = True
        return phase["command"]

    for fb in phase.get("fallbacks", []):
        if check_tool_available(fb["tool"]):
            phase["available"] = True
            return fb["command"]

    if phase.get("optional"):
        phase["available"] = False
        return None

    phase["available"] = False
    return None


def run_tool(
    command: str,
    on_output: Callable[[str], None],
    on_complete: Optional[Callable[[int], None]] = None,
    shell: bool = True,
) -> None:
    def _run():
        try:
            proc = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in proc.stdout:
                if line:
                    clean = strip_ansi(line.rstrip()) + "\n"
                    on_output(clean)
            proc.wait()
            if on_complete:
                on_complete(proc.returncode or 0)
        except Exception as e:
            on_output(f"[!] Error: {str(e)}\n")
            if on_complete:
                on_complete(-1)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def run_tools_sequential(
    phases: List[dict],
    on_output: Callable[[str], None],
    on_phase_start: Optional[Callable[[dict], None]] = None,
    on_phase_complete: Optional[Callable[[dict, int], None]] = None,
    on_progress: Optional[Callable[[int, int, dict], None]] = None,
    on_all_complete: Optional[Callable[[Dict[str, str]], None]] = None,
    on_phase_confirm: Optional[Callable[[dict, int, str, Dict[str, str]], bool]] = None,
) -> None:
    """
    Run multiple tool phases sequentially in a background thread.

    Args:
        phases: List of phase dicts from build_recon_plan
        on_output: Callback for output (thread-safe)
        on_phase_start: Optional callback when a phase starts
        on_phase_complete: Optional callback when a phase finishes (phase, exit_code)
        on_progress: Optional callback (current_phase_idx, total_phases, phase)
        on_all_complete: Optional callback with dict of {tool_name: collected_output}
        on_phase_confirm: Optional callback (phase, exit_code, output, collected_so_far)
                          that BLOCKS until the user confirms. Return True to continue,
                          False to stop.
    """

    def _run():
        total = len(phases)
        collected: Dict[str, str] = {}

        for idx, phase in enumerate(phases):
            cmd = resolve_tool_command(phase)
            if cmd:
                tool_name = phase.get("tool", "unknown")
                phase_buf: list = []

                if on_phase_start:
                    on_phase_start(phase)
                if on_progress:
                    on_progress(idx, total, phase)

                on_output(
                    f"\n[*] === Phase {phase['phase']}: {phase['purpose']} ({tool_name}) ===\n"
                )
                on_output(f"[*] $ {cmd}\n\n")

                done = threading.Event()
                exit_code = [None]

                def on_line(line, _buf=phase_buf):
                    _buf.append(line)
                    on_output(line)

                def on_complete(code):
                    exit_code[0] = code
                    done.set()

                run_tool(cmd, on_line, on_complete)
                done.wait()

                phase_output = "".join(phase_buf)
                collected[tool_name] = phase_output

                if on_phase_complete:
                    on_phase_complete(phase, exit_code[0] or 0)
                if on_progress:
                    on_progress(idx + 1, total, phase)

                if on_phase_confirm:
                    should_continue = on_phase_confirm(
                        phase, exit_code[0] or 0, phase_output, collected
                    )
                    if not should_continue:
                        on_output(
                            f"\n[!] === USER STOPPED AFTER PHASE {phase['phase']} ===\n"
                        )
                        break
            else:
                on_output(
                    f"[!] Phase {phase['phase']}: {phase['tool']} not found, skipping\n"
                )

        if on_all_complete:
            on_all_complete(collected)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
