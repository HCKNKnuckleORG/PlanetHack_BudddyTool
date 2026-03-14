"""
A07:2025 Authentication Failures
https://owasp.org/Top10/2025/A07_2025-Authentication_Failures/
Credential stuffing, weak passwords, session fixation
"""

from .base import BaseModule
from .auth import AuthModule
from typing import Dict, Any


class A07AuthenticationFailuresModule(BaseModule):
    """OWASP A07:2025 - Authentication Failures"""

    def get_info(self) -> Dict[str, str]:
        return {
            "name": "A07 Authentication Failures",
            "description": "Credential stuffing, weak auth, session issues. OWASP Top 10 2025",
            "version": "1.0.0",
            "owasp": "A07:2025",
            "ref": "https://owasp.org/Top10/2025/A07_2025-Authentication_Failures/",
        }

    def run(self, target: str, **kwargs) -> Dict[str, Any]:
        if not self.validate_target(target):
            return {"error": "Invalid target format"}

        sub = AuthModule(self.config, self.logger)
        result = sub.run(target, **kwargs)
        result["owasp"] = "A07:2025 Authentication Failures"
        result["ref"] = "https://owasp.org/Top10/2025/A07_2025-Authentication_Failures/"
        result["related_modules"] = ["auth", "brute_force"]
        return result
