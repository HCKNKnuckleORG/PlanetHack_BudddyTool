"""
Command validation for remote code execution (RCE) prevention.
Only allow execution of known security testing tools with validated arguments.

References: OWASP A03 Injection, CWE-78 (OS Command Injection)
"""

import re
from typing import Tuple, Optional

# Allowlist of tool names that may be executed (first token of command)
# These are Kali/security testing tools used by PlanetHack
ALLOWED_TOOL_NAMES = frozenset(
    {
        "nmap",
        "nikto",
        "gobuster",
        "feroxbuster",
        "dirb",
        "whatweb",
        "nuclei",
        "sqlmap",
        "hydra",
        "curl",
        "dirsearch",
        "wget",
        "wpscan",
        "ffuf",
        "amass",
        "subfinder",
        "masscan",
        "searchsploit",
        "python3",
        "python",  # for module invocations
    }
)

# Shell metacharacters that enable command injection
_SHELL_META_RE = re.compile(r"[;&|`$(){}!<>\\\n\r]")

# Max command length to prevent DoS
MAX_COMMAND_LEN = 4096


def validate_command_for_execution(cmd: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a command is safe to execute.
    Only allows commands starting with known security tools.
    Rejects shell metacharacters to prevent injection.

    Returns:
        (is_valid, error_message)
    """
    if not cmd or not isinstance(cmd, str):
        return False, "No command provided"

    cmd = cmd.strip()
    if len(cmd) > MAX_COMMAND_LEN:
        return False, f"Command exceeds max length ({MAX_COMMAND_LEN})"

    if _SHELL_META_RE.search(cmd):
        return False, "Command contains forbidden shell characters"

    # First token must be an allowed tool
    parts = cmd.split()
    if not parts:
        return False, "Empty command"

    tool = parts[0].lower()
    # Handle tool paths like /usr/bin/nmap
    if "/" in tool:
        tool = tool.split("/")[-1]

    if tool not in ALLOWED_TOOL_NAMES:
        return False, f"Tool '{tool}' is not in the allowlist for remote execution"

    return True, None
