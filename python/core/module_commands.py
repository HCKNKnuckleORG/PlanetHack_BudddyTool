"""
Default shell commands per module for payload editing.
Used when user wants to run a custom/modified command instead of the module's Python logic.
"""

import shlex
from typing import Optional
from urllib.parse import urlparse

from utils.helpers import validate_url


def _base_url(target: str) -> str:
    t = (target or "").strip()
    if t.startswith(("http://", "https://")):
        return t
    return f"http://{t}"


def _host(target: str) -> str:
    t = (target or "").strip()
    if validate_url(t):
        parsed = urlparse(t)
        return parsed.netloc or t
    if t.startswith("ssh://"):
        return t.replace("ssh://", "").split("/")[0]
    if t.startswith("ftp://"):
        return t.replace("ftp://", "").split("/")[0]
    return t


def _kali_config(config) -> dict:
    raw = getattr(config, "config", config) or {}
    tools = raw.get("tools", {})
    return tools.get("kali", {})


def get_default_command(module_id: str, target: str, config=None) -> str:
    """
    Return the primary suggested shell command for a module + target.
    Used to pre-fill the payload/command field in the UI.
    """
    base = _base_url(target)
    host = _host(target)
    kali = _kali_config(config) or {}
    wd = kali.get("wordlist_dir", "/usr/share/wordlists")
    users = kali.get("users_wordlist", f"{wd}/metasploit/unix_users.txt")
    passes = kali.get("passwords_wordlist", f"{wd}/rockyou.txt")
    gob_wl = kali.get("gobuster_wordlist", f"{wd}/dirb/common.txt")

    defaults = {
        "sql": f"sqlmap -u {shlex.quote(base)} --batch --level=3 --risk=2",
        "xss": f"nuclei -u {base} -tags xss -severity critical,high,medium",
        "a05_injection": f"sqlmap -u {shlex.quote(base)} --batch --level=3 --risk=2",
        "brute_force": f"hydra -L {shlex.quote(users)} -P {shlex.quote(passes)} ssh://{shlex.quote(host)} -t 4",
        "open_redirect": f"nuclei -u {base} -tags redirect -severity info,low,medium",
        "clickjacking": f"nuclei -u {base} -tags clickjacking -severity info,low",
        "csrf": f"nuclei -u {base} -tags csrf -severity info,low",
        "access_control": f"nuclei -u {base} -tags idor,access-control -severity critical,high",
        "a01_access_control": f"nuclei -u {base} -tags idor,access-control -severity critical,high",
        "auth": f"hydra -L {shlex.quote(users)} -P {shlex.quote(passes)} {shlex.quote(base)} http-post-form '/login:user=^USER^&pass=^PASS^:F=incorrect'",
        "file_upload": f"nuclei -u {base} -tags file-upload -severity critical,high,medium",
        "ssrf": f"nuclei -u {base} -tags ssrf -severity critical,high",
        "fuzzing": f"ffuf -u {base}/FUZZ -w {shlex.quote(gob_wl)} -mc 200,301,302,403",
        "api": f"nuclei -u {base} -tags api -severity critical,high,medium",
        "information_disclosure": f"nikto -h {base}",
        "template_injection": f"nuclei -u {base} -tags ssti -severity critical,high",
        "rce": f"nuclei -u {base} -tags rce -severity critical,high",
        "a02_misconfiguration": f"nuclei -u {base} -severity critical,high,medium",
        "a06_insecure_design": f"nikto -h {base}",
        "a07_auth": f"hydra -L {shlex.quote(users)} -P {shlex.quote(passes)} {shlex.quote(base)} http-post-form '/login:user=^USER^&pass=^PASS^:F=incorrect'",
        "a08_integrity": f"nuclei -u {base} -tags sri,checksum -severity info,low",
        "a09_logging": f"nikto -h {base}",
        "a10_exceptional": f"nuclei -u {base} -severity critical,high,medium",
        "gobuster": f"gobuster dir -u {base} -w {shlex.quote(gob_wl)} -t 50",
    }

    return defaults.get(
        module_id, f"# Edit for {module_id} - e.g. nuclei -u {base} -tags ..."
    )
