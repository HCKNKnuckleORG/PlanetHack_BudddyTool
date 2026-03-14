"""
Recon Plan Builder - Generates phased reconnaissance tool plans for Kali Linux
Supports Python tools (nmap, nikto, etc.) and optional Go scanner.
"""

import re
import shlex
from pathlib import Path  # used for hidden_configs wordlist
from typing import Dict, Any, List, Optional

from utils.helpers import is_ip_address, validate_url, extract_domain


_SHELL_META_RE = re.compile(r'[;&|`$(){}!<>\\\n\r]')


def _sanitize_for_shell(value: str) -> str:
    """Quote a value for safe shell interpolation. Rejects shell metacharacters."""
    if _SHELL_META_RE.search(value):
        raise ValueError(f"Target contains forbidden characters: {value!r}")
    return shlex.quote(value)


def normalize_target(target: str, use_https: bool = False) -> Dict[str, str]:
    """
    Normalize target input to host and base URL for web tools.
    
    Args:
        target: IP address, domain, or full URL
        use_https: If True, use https:// for web URLs; else http://
        
    Returns:
        Dict with 'host' (IP or domain), 'base_url' (http(s)://...), 'is_ip'
    """
    target = target.strip()
    scheme = "https" if use_https else "http"
    
    if validate_url(target):
        # Full URL provided
        domain = extract_domain(target)
        return {
            "host": domain or target,
            "base_url": target if target.startswith(("http://", "https://")) else f"{scheme}://{target}",
            "is_ip": is_ip_address(domain or target) if domain else False,
        }
    
    if is_ip_address(target):
        return {
            "host": target,
            "base_url": f"{scheme}://{target}",
            "is_ip": True,
        }
    
    # Assume domain
    return {
        "host": target,
        "base_url": f"{scheme}://{target}",
        "is_ip": False,
    }


def build_recon_plan(
    target: str,
    config: Optional[Any] = None,
    preset: str = "full",
) -> List[Dict[str, Any]]:
    """
    Build a phased reconnaissance plan using Kali Linux tools.
    
    Args:
        target: IP address, domain, or URL
        config: Optional Config object or dict with tool paths and wordlists
        preset: 'full' (all phases), 'htb' (CTF box), 'web' (web app focus)
        
    Returns:
        List of phase dicts: {phase, purpose, tool, command, available}
    """
    raw_config = getattr(config, "config", config) if config else {}
    normalized = normalize_target(target)
    host = _sanitize_for_shell(normalized["host"])
    base_url = _sanitize_for_shell(normalized["base_url"])
    
    # Kali default paths
    tools = raw_config.get("tools", {})
    kali = tools.get("kali", {})
    wordlist_dir = kali.get("wordlist_dir", "/usr/share/wordlists")
    gobuster_wordlist = shlex.quote(kali.get("gobuster_wordlist", f"{wordlist_dir}/dirb/common.txt"))
    
    nmap_cfg = tools.get("nmap", {})
    nmap_path = shlex.quote(nmap_cfg.get("path", "nmap"))
    
    phases = []

    # Phase 0 (Go scanner) removed: was redundant with nmap and required a custom
    # binary that often fails. Nmap handles port scanning on Kali.

    # Phase 1: Host discovery / port scan (nmap)
    # - htb/web: top 1000 ports (faster, VM-friendly). full: all ports (slow, heavy).
    if preset in ("full", "htb", "web"):
        nmap_ports = "-p-" if preset == "full" else "-F"  # -F = top 100 ports, fast
        if preset == "htb":
            nmap_ports = "-p 21,22,80,443,445,139,8080,8443,3000,5000,8000,3306,5432"  # common CTF
        elif preset == "web":
            nmap_ports = "-p 80,443,8080,8443,8000,3000"
        phases.append({
            "phase": 1,
            "purpose": "Host discovery / port scan",
            "tool": "nmap",
            "command": f"{nmap_path} -sC -sV {nmap_ports} {host}",
            "available": None,
        })
    
    # Phase 2: Web tech fingerprinting (HTB too — needed for CTF tech stack)
    if preset in ("full", "web", "htb"):
        phases.append({
            "phase": 2,
            "purpose": "Web technology fingerprinting",
            "tool": "whatweb",
            "command": f"whatweb -v {base_url}",
            "available": None,
        })
    
    # Phase 3: Web vulnerability scan
    if preset in ("full", "web"):
        phases.append({
            "phase": 3,
            "purpose": "Web vulnerability scan",
            "tool": "nikto",
            "command": f"nikto -h {base_url}",
            "available": None,
        })
    
    # Extensions for backup/config/hidden files (Discovering Hidden Information)
    _exts = "php,bak,old,txt,env,json,sql,tar,gz"
    # Phase 4: Directory / file discovery (prefer gobuster, fallback feroxbuster, then dirb)
    if preset in ("full", "htb", "web"):
        threads = 50 if preset == "full" else 20  # lighter for CTF/web to avoid VM overload
        gobuster_cmd = f"gobuster dir -u {base_url} -w {gobuster_wordlist} -t {threads} -x {_exts}"
        ferox_cmd = f"feroxbuster -u {base_url} -w {gobuster_wordlist} -t {threads} -x {_exts}"
        dirb_cmd = f"dirb {base_url} {gobuster_wordlist}"
        phases.append({
            "phase": 4 if preset in ("full", "web") else 3,
            "purpose": "Directory / file discovery (incl. backup/config extensions)",
            "tool": "gobuster",
            "command": gobuster_cmd,
            "fallbacks": [
                {"tool": "feroxbuster", "command": ferox_cmd},
                {"tool": "dirb", "command": dirb_cmd},
            ],
            "available": None,
        })

    # Phase 4b: Hidden & config file discovery (wordlist of sensitive paths)
    _hidden_wl = Path(__file__).parent / "data" / "hidden_configs.txt"
    if preset in ("full", "htb", "web") and _hidden_wl.exists():
        hidden_wl_quoted = shlex.quote(str(_hidden_wl))
        gobuster_hidden_cmd = f"gobuster dir -u {base_url} -w {hidden_wl_quoted} -t {threads} -x {_exts}"
        ferox_hidden_cmd = f"feroxbuster -u {base_url} -w {hidden_wl_quoted} -t {threads} -x {_exts}"
        phases.append({
            "phase": 5 if preset in ("full", "web") else 4,
            "purpose": "Hidden & config file discovery (.git, backup, config, .env)",
            "tool": "gobuster",
            "command": gobuster_hidden_cmd,
            "fallbacks": [
                {"tool": "feroxbuster", "command": ferox_hidden_cmd},
            ],
            "available": None,
        })
    
    # Phase 5: Vulnerability templates (nuclei)
    # Limit scope to avoid VM freeze: critical/high only, rate limit, silent
    if preset in ("full", "web"):
        nuclei_opts = "-severity critical,high -silent -rl 30"
        phases.append({
            "phase": 5,
            "purpose": "Vulnerability template scan",
            "tool": "nuclei",
            "command": f"nuclei -u {base_url} {nuclei_opts}",
            "available": None,
        })
    
    # Renumber phases sequentially
    for i, p in enumerate(phases, 1):
        p["phase"] = i
    
    return phases
