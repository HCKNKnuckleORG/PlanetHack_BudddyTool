"""
Module Readiness -- gates module availability based on recon findings.

Each module declares what recon data it needs. When session findings are
available, we compute which modules are "ready" to run.
"""

import re
from typing import Dict, Any, List, Tuple, Callable

_WEB_PORTS = {80, 443, 8080, 8443, 8000, 3000, 5000, 8888, 8444, 9000}
_LOGIN_PATH_KEYWORDS = (
    "/admin",
    "/login",
    "/wp-admin",
    "/dashboard",
    "/panel",
    "/manager",
)


def _port_nums(findings: Dict[str, Any]) -> set:
    nmap = findings.get("nmap") or {}
    ports = nmap.get("ports") or []
    return {p["port"] for p in ports if isinstance(p, dict) and "port" in p}


def _has_web_ports(findings: Dict[str, Any]) -> bool:
    return bool(_port_nums(findings) & _WEB_PORTS)


def _login_dirs(findings: Dict[str, Any]) -> List[Dict]:
    for tool in ("gobuster", "feroxbuster", "dirb"):
        dirs = findings.get(tool) or []
        if not isinstance(dirs, list):
            continue
        login = [
            d
            for d in dirs
            if isinstance(d, dict)
            and any(k in (d.get("path") or "").lower() for k in _LOGIN_PATH_KEYWORDS)
        ]
        if login:
            return login
    return []


def _directories(findings: Dict[str, Any]) -> List[Dict]:
    for tool in ("gobuster", "feroxbuster", "dirb"):
        dirs = findings.get(tool) or []
        if dirs and isinstance(dirs, list):
            return dirs
    return []


def _has_dirs_with_ids(findings: Dict[str, Any]) -> bool:
    """Heuristic: paths like /user/123, /item/42, /api/123."""
    dirs = _directories(findings)
    for d in dirs:
        path = (d.get("path") or "").lower()
        if (
            re.search(r"/\d+/?$", path)
            or "/user/" in path
            or "/id/" in path
            or "/item/" in path
        ):
            return True
    return False


def _is_web_url(target: str) -> bool:
    return (target or "").strip().startswith(("http://", "https://"))


# Module ID -> (condition_fn(finding, target) -> bool, reason when not ready)
_READINESS_RULES: Dict[str, Tuple[Callable[[Dict, str], bool], str]] = {}


def _rule(module_id: str, reason: str):
    def decorator(fn):
        _READINESS_RULES[module_id] = (fn, reason)
        return fn

    return decorator


# Always ready
@_rule("recon", "")
def _recon(findings: Dict, target: str) -> bool:
    return True


# Web modules: need web URL or web ports
def _web(findings: Dict, target: str) -> bool:
    return _is_web_url(target) or _has_web_ports(findings)


for mid in (
    "sql",
    "xss",
    "csrf",
    "open_redirect",
    "clickjacking",
    "file_upload",
    "ssrf",
    "api",
    "business_logic",
    "cache",
    "information_disclosure",
    "fuzzing",
    "rce",
    "template_injection",
    "deserialization",
    "xxe",
    "request_smuggling",
    "session",
    "a02_misconfiguration",
    "a05_injection",
    "a06_insecure_design",
    "a07_auth",
    "a08_integrity",
    "a09_logging",
    "a10_exceptional",
):
    if mid not in _READINESS_RULES:
        _READINESS_RULES[mid] = (
            _web,
            "Need web target (http(s)) or recon showing web ports (80, 443, 8080...)",
        )


# Brute force: SSH, FTP, or login dirs
@_rule("brute_force", "Need SSH (port 22), FTP (port 21), or dirs like /login, /admin")
def _brute_force(findings: Dict, target: str) -> bool:
    ports = _port_nums(findings)
    return 22 in ports or 21 in ports or bool(_login_dirs(findings))


# Auth: web or login dirs
@_rule("auth", "Need web target or login dirs from recon")
def _auth(findings: Dict, target: str) -> bool:
    return _web(findings, target) or bool(_login_dirs(findings))


# Access control / IDOR: web + directories (prefer with IDs)
@_rule("access_control", "Need web target + directory paths (e.g. /user/123)")
def _access_control(findings: Dict, target: str) -> bool:
    if not _web(findings, target):
        return False
    dirs = _directories(findings)
    return bool(dirs)


@_rule("a01_access_control", "Need web target + directory paths (e.g. /user/123)")
def _a01_access(findings: Dict, target: str) -> bool:
    return _access_control(findings, target)


# Supply chain, crypto: minimal requirements (web or any ports)
@_rule("a03_supply_chain", "Need target with recon data")
def _supply_chain(findings: Dict, target: str) -> bool:
    return bool((target or "").strip())


@_rule("a04_crypto", "Need target with recon data")
def _crypto(findings: Dict, target: str) -> bool:
    return bool((target or "").strip())


def evaluate_readiness(
    findings: Dict[str, Any],
    target: str = "",
) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Evaluate which modules are ready based on session findings.

    Returns:
        (ready_module_ids, not_ready_list)
        not_ready_list: [{"id": module_id, "reason": "..."}, ...]
    """
    ready: List[str] = []
    not_ready: List[Dict[str, str]] = []

    for module_id, (condition_fn, reason) in _READINESS_RULES.items():
        try:
            if condition_fn(findings, target):
                ready.append(module_id)
            elif reason:
                not_ready.append({"id": module_id, "reason": reason})
        except Exception:
            not_ready.append({"id": module_id, "reason": "Error evaluating readiness"})

    return (ready, not_ready)
