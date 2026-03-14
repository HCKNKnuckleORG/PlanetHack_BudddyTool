"""
A02:2025 Security Misconfiguration
https://owasp.org/Top10/2025/A02_2025-Security_Misconfiguration/
Default creds, verbose errors, unnecessary features, insecure headers
"""

from urllib.parse import urlparse

from .base import BaseModule
from typing import Dict, Any


def _host(target: str) -> str:
    t = target.strip()
    if t.startswith(("http://", "https://")):
        try:
            return urlparse(t).netloc or t
        except Exception:
            return t
    return t


class A02SecurityMisconfigurationModule(BaseModule):
    """OWASP A02:2025 - Security Misconfiguration"""

    def get_info(self) -> Dict[str, str]:
        return {
            "name": "A02 Security Misconfiguration",
            "description": "Default creds, verbose errors, insecure headers. OWASP Top 10 2025",
            "version": "1.0.0",
            "owasp": "A02:2025",
            "ref": "https://owasp.org/Top10/2025/A02_2025-Security_Misconfiguration/",
        }

    def run(self, target: str, **kwargs) -> Dict[str, Any]:
        if not self.validate_target(target):
            return {"error": "Invalid target format"}

        results = {
            "target": target,
            "owasp": "A02:2025 Security Misconfiguration",
            "ref": "https://owasp.org/Top10/2025/A02_2025-Security_Misconfiguration/",
            "commands": [
                f"nmap --script http-security-headers -p 80,443,8080 {_host(target)}",
                f"nikto -h {target if target.startswith('http') else 'http://' + _host(target)}",
                f"whatweb -v {target if target.startswith('http') else 'http://' + _host(target)}",
            ],
            "checks": [
                "Directory listing enabled",
                "Default credentials (admin/admin, root/root)",
                "Verbose error messages",
                "Missing security headers (CSP, X-Frame-Options, HSTS)",
                ".git, backup files in web root",
            ],
            "status": "completed",
        }
        self.log_result(results)
        return results
