"""
A04:2025 Cryptographic Failures
https://owasp.org/Top10/2025/A04_2025-Cryptographic_Failures/
Weak crypto, sensitive data in transit/at rest, deprecated algorithms
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


class A04CryptographicFailuresModule(BaseModule):
    """OWASP A04:2025 - Cryptographic Failures"""

    def get_info(self) -> Dict[str, str]:
        return {
            "name": "A04 Cryptographic Failures",
            "description": "Weak crypto, sensitive data exposure. OWASP Top 10 2025",
            "version": "1.0.0",
            "owasp": "A04:2025",
            "ref": "https://owasp.org/Top10/2025/A04_2025-Cryptographic_Failures/",
        }

    def run(self, target: str, **kwargs) -> Dict[str, Any]:
        if not self.validate_target(target):
            return {"error": "Invalid target format"}

        results = {
            "target": target,
            "owasp": "A04:2025 Cryptographic Failures",
            "ref": "https://owasp.org/Top10/2025/A04_2025-Cryptographic_Failures/",
            "commands": [
                f"nmap --script ssl-enum-ciphers -p 443,8443 {_host(target)}",
                f"testssl.sh {target}",
            ],
            "checks": [
                "Weak TLS (SSLv3, TLS 1.0/1.1)",
                "Passwords/tokens in URLs or logs",
                "Sensitive data without encryption at rest",
                "Weak hashing (MD5, SHA1 for passwords)",
            ],
            "status": "completed",
        }
        self.log_result(results)
        return results
