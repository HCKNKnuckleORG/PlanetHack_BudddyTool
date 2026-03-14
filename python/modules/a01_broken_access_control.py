"""
A01:2025 Broken Access Control
https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/
IDOR, privilege escalation, force browsing, CORS misconfig, JWT manipulation
"""

from .base import BaseModule
from .access_control import AccessControlModule
from typing import Dict, Any


class A01BrokenAccessControlModule(BaseModule):
    """OWASP A01:2025 - Broken Access Control"""

    def get_info(self) -> Dict[str, str]:
        return {
            "name": "A01 Broken Access Control",
            "description": "IDOR, privilege escalation, force browsing, CORS, JWT. OWASP Top 10 2025",
            "version": "1.0.0",
            "owasp": "A01:2025",
            "ref": "https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/",
        }

    def run(self, target: str, **kwargs) -> Dict[str, Any]:
        if not self.validate_target(target):
            return {"error": "Invalid target format"}

        # Delegate to access_control module
        sub = AccessControlModule(self.config, self.logger)
        result = sub.run(target, **kwargs)
        result["owasp"] = "A01:2025 Broken Access Control"
        result["ref"] = "https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/"
        result["checks"] = [
            "Force browse to /admin, /api/admin, privileged paths",
            "Modify IDs in URLs (acct=, id=) - IDOR",
            "Check CORS: Origin header tampering",
            "JWT: alg:none, expired tokens, weak secret",
        ]
        return result
