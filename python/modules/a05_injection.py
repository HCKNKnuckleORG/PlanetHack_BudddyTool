"""
A05:2025 Injection
https://owasp.org/Top10/2025/A05_2025-Injection/
SQLi, NoSQLi, OS command, LDAP, XSS, template injection
"""

from .base import BaseModule
from typing import Dict, Any


class A05InjectionModule(BaseModule):
    """OWASP A05:2025 - Injection"""

    def get_info(self) -> Dict[str, str]:
        return {
            "name": "A05 Injection",
            "description": "SQLi, XSS, command injection, SSTI. OWASP Top 10 2025",
            "version": "1.0.0",
            "owasp": "A05:2025",
            "ref": "https://owasp.org/Top10/2025/A05_2025-Injection/",
        }

    def run(self, target: str, **kwargs) -> Dict[str, Any]:
        if not self.validate_target(target):
            return {"error": "Invalid target format"}

        base = (
            target if target.startswith(("http://", "https://")) else f"http://{target}"
        )
        results = {
            "target": target,
            "owasp": "A05:2025 Injection",
            "ref": "https://owasp.org/Top10/2025/A05_2025-Injection/",
            "related_modules": ["sql", "xss", "template_injection"],
            "commands": [
                f"sqlmap -u {base} --batch --level=3 --risk=2",
                f"nuclei -u {base} -tags sqli,xss,ssti -severity critical,high",
            ],
            "checks": [
                "SQL injection (sql module)",
                "XSS reflected/stored (xss module)",
                "SSTI (template_injection module)",
                "Command injection, LDAP injection",
            ],
            "status": "completed",
        }
        self.log_result(results)
        return results
