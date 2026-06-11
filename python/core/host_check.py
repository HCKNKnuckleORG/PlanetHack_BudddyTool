"""
Host Check -- pre-recon validation for CTF/HTB/THM boxes.

Detects HTTP redirects to unresolvable hostnames, checks /etc/hosts,
and offers to add missing entries. Also finds subdomains in tool output.
"""

import re
import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from utils.helpers import is_ip_address

HOSTS_FILE = Path("/etc/hosts")


def read_hosts_file() -> Dict[str, List[str]]:
    """Parse /etc/hosts and return {ip: [hostname, ...]} mapping."""
    mapping: Dict[str, List[str]] = {}
    if not HOSTS_FILE.exists():
        return mapping
    try:
        for line in HOSTS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                ip = parts[0]
                hostnames = parts[1:]
                mapping.setdefault(ip, []).extend(hostnames)
    except PermissionError:
        pass
    return mapping


def hostname_in_hosts(
    hostname: str, hosts_map: Optional[Dict[str, List[str]]] = None
) -> Optional[str]:
    """Check if hostname is in /etc/hosts. Returns the IP if found, None otherwise."""
    if hosts_map is None:
        hosts_map = read_hosts_file()
    hostname_lower = hostname.lower()
    for ip, names in hosts_map.items():
        if hostname_lower in [n.lower() for n in names]:
            return ip
    return None


def can_resolve(hostname: str) -> bool:
    """Check if a hostname resolves via DNS or /etc/hosts."""
    try:
        socket.getaddrinfo(hostname, None, socket.AF_INET)
        return True
    except (socket.gaierror, OSError):
        return False


def check_http_redirect(target: str, timeout: int = 5) -> Optional[str]:
    """
    Make an HTTP request to the target IP and check if it redirects
    to a hostname (common on THM/HTB boxes with vhost routing).

    Returns the redirect hostname if found, None otherwise.
    """
    if not is_ip_address(target):
        return None

    try:
        import urllib.request
        import urllib.error

        url = f"http://{target}"
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "PlanetHack/1.0")

        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            final_url = resp.geturl()
        except urllib.error.HTTPError as e:
            final_url = e.headers.get("Location", "")
        except urllib.error.URLError:
            return None

        if final_url and final_url != url:
            parsed = urlparse(final_url)
            host = parsed.hostname
            if host and not is_ip_address(host) and host != target:
                return host

    except Exception:
        pass

    try:
        result = subprocess.run(
            [
                "curl",
                "-sIL",
                "-o",
                "/dev/null",
                "-w",
                "%{url_effective}",
                "--max-time",
                str(timeout),
                f"http://{target}",
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 2,
        )
        final_url = result.stdout.strip()
        if final_url:
            parsed = urlparse(final_url)
            host = parsed.hostname
            if host and not is_ip_address(host) and host != target:
                return host
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    return None


_HOSTNAME_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9.-]{0,61}[a-zA-Z0-9])?$")
_INJECTION_RE = re.compile(r"[\n\r\t\x00;|&$`]")


def _validate_hosts_entry(ip: str, hostnames: List[str]) -> Tuple[bool, str]:
    """Validate ip and hostnames to prevent injection into /etc/hosts."""
    if not is_ip_address(ip):
        return False, "Invalid IP address"
    if _INJECTION_RE.search(ip):
        return False, "IP contains invalid characters"
    for h in hostnames:
        if not h or not isinstance(h, str):
            return False, "Invalid hostname"
        h = h.strip().lower()
        if _INJECTION_RE.search(h):
            return False, f"Hostname contains invalid characters: {h!r}"
        if len(h) > 253:
            return False, "Hostname too long"
        if not _HOSTNAME_RE.match(h):
            return False, f"Invalid hostname format: {h!r}"
    return True, ""


def add_to_hosts_file(ip: str, hostnames: List[str]) -> Tuple[bool, str]:
    """
    Add IP + hostnames to /etc/hosts using sudo tee.
    Returns (success, message). Validates input to prevent injection.
    """
    if not hostnames:
        return False, "No hostnames to add"

    ok, err = _validate_hosts_entry(ip.strip(), hostnames)
    if not ok:
        return False, err

    ip_clean = ip.strip()
    hostnames = [
        h.strip().lower() for h in hostnames if isinstance(h, str) and h.strip()
    ]
    if not hostnames:
        return False, "No valid hostnames to add"

    hosts_map = read_hosts_file()
    existing = hosts_map.get(ip_clean, [])
    already = [h for h in hostnames if h.lower() in [e.lower() for e in existing]]
    new_hosts = [h for h in hostnames if h.lower() not in [e.lower() for e in existing]]

    if not new_hosts:
        return True, f"Already in /etc/hosts: {', '.join(already)}"

    try:
        line = f"{ip_clean}    {' '.join(new_hosts)}\n"
        result = subprocess.run(
            ["sudo", "tee", "-a", "/etc/hosts"],
            input=line,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, f"Added to /etc/hosts: {ip_clean} -> {', '.join(new_hosts)}"
        else:
            return False, f"Failed: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, "Timed out waiting for sudo"
    except Exception as e:
        return False, f"Error: {e}"


def extract_hostnames_from_output(output: str) -> List[str]:
    """Extract potential hostnames/subdomains from tool output for /etc/hosts."""
    hostname_re = re.compile(
        r"(?:https?://)?([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z]{2,})+)"
    )
    found = set()
    for match in hostname_re.finditer(output):
        hostname = match.group(1).lower()
        if hostname.endswith((".thm", ".htb", ".local", ".ctf", ".box", ".lab")):
            found.add(hostname)
    return sorted(found)


def run_preflight_check(target: str, preset: str = "full") -> Dict:
    """
    Run all pre-recon checks. Returns a dict with:
    - redirect_hostname: hostname the target redirects to (or None)
    - hosts_ok: whether the hostname resolves
    - hosts_ip: IP mapped in /etc/hosts (or None)
    - needs_hosts_update: bool
    - all_hosts_entries: current /etc/hosts mapping for this IP
    - message: human-readable summary
    """
    result: Dict[str, Any] = {
        "target": target,
        "preset": preset,
        "redirect_hostname": None,
        "hosts_ok": True,
        "hosts_ip": None,
        "needs_hosts_update": False,
        "all_hosts_entries": [],
        "message": "",
        "warnings": [],
    }

    hosts_map = read_hosts_file()

    if is_ip_address(target):
        result["all_hosts_entries"] = hosts_map.get(target, [])

        redirect_host = check_http_redirect(target)
        if redirect_host:
            result["redirect_hostname"] = redirect_host
            mapped_ip = hostname_in_hosts(redirect_host, hosts_map)
            if mapped_ip:
                result["hosts_ip"] = mapped_ip
                result["hosts_ok"] = True
                result["message"] = (
                    f"Target redirects to {redirect_host} (mapped to {mapped_ip} in /etc/hosts)"
                )
            elif can_resolve(redirect_host):
                result["hosts_ok"] = True
                result["message"] = (
                    f"Target redirects to {redirect_host} (resolves via DNS)"
                )
            else:
                result["hosts_ok"] = False
                result["needs_hosts_update"] = True
                result["message"] = (
                    f"Target redirects to {redirect_host} which does NOT resolve. Add to /etc/hosts."
                )
                result["warnings"].append(
                    f"HTTP redirect detected: {target} -> {redirect_host}\n"
                    f"This hostname cannot be resolved. You need to add it to /etc/hosts:\n"
                    f'  echo "{target}    {redirect_host}" | sudo tee -a /etc/hosts'
                )
        else:
            result["message"] = "No redirect detected. Target responds directly on IP."

    else:
        if not can_resolve(target):
            mapped_ip = hostname_in_hosts(target, hosts_map)
            if not mapped_ip:
                result["hosts_ok"] = False
                result["needs_hosts_update"] = True
                result["message"] = (
                    f"Hostname {target} does not resolve and is not in /etc/hosts."
                )
                result["warnings"].append(
                    f"Cannot resolve {target}. If this is a CTF box, add it to /etc/hosts:\n"
                    f'  echo "<TARGET_IP>    {target}" | sudo tee -a /etc/hosts'
                )
            else:
                result["hosts_ip"] = mapped_ip
                result["message"] = (
                    f"Hostname {target} resolves via /etc/hosts -> {mapped_ip}"
                )
        else:
            result["message"] = f"Hostname {target} resolves OK."

    if (
        preset in ("htb", "ctf")
        and is_ip_address(target)
        and not result["all_hosts_entries"]
    ):
        result["warnings"].append(
            f"CTF preset selected but {target} has no /etc/hosts entries. "
            f"Many CTF boxes require hostname mapping for vhost routing."
        )

    return result
