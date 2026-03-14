"""
Recon Report Generator -- parses tool output, extracts findings,
generates Markdown or HTML reports with recommendations.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from html import escape as html_escape


def _extract_discovered_hostnames(outputs: Dict[str, str]) -> List[str]:
    """Extract lab hostnames (.htb, .thm, .lab, .ctf, .box) from concatenated tool output."""
    try:
        from core.host_check import extract_hostnames_from_output
        combined = "\n".join(outputs.values()) if outputs else ""
        return list(extract_hostnames_from_output(combined))
    except Exception:
        return []


# ── Output Parsers ───────────────────────────────────────────────────────────

def parse_nmap(output: str) -> Dict[str, Any]:
    """Extract open ports, services, OS info, scan target, and redirect hostname from nmap output."""
    ports = []
    os_info = []
    scan_target = ""
    redirect_hostname = ""

    for line in output.splitlines():
        port_match = re.match(
            r'^\s*(\d+)/(tcp|udp)\s+(open|filtered)\s+(.*)$', line
        )
        if port_match:
            ports.append({
                "port": int(port_match.group(1)),
                "proto": port_match.group(2),
                "state": port_match.group(3),
                "service": port_match.group(4).strip(),
            })

        if "OS details:" in line or "Running:" in line or "OS CPE:" in line:
            os_info.append(line.strip())

        # Extract scan target: "Nmap scan report for 10.10.10.5"
        scan_report = re.search(r'Nmap scan report for (\S+)', line, re.I)
        if scan_report:
            scan_target = scan_report.group(1).strip()

        # Extract redirect hostname: "redirect to https://hostname/" or "Did not follow redirect to https://hostname/"
        redirect_match = re.search(r'redirect to (https?://[^\s/]+)', line, re.I)
        if redirect_match:
            redirect_hostname = redirect_match.group(1).strip()
        else:
            redirect_match = re.search(r'Did not follow redirect to (https?://[^\s/]+)', line, re.I)
            if redirect_match:
                redirect_hostname = redirect_match.group(1).strip()

    result: Dict[str, Any] = {"ports": ports, "os": os_info}
    if scan_target:
        result["scan_target"] = scan_target
    if redirect_hostname:
        result["redirect_hostname"] = redirect_hostname
    return result


def parse_whatweb(output: str) -> List[str]:
    """Extract web technologies from whatweb output."""
    output = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]|[\x1b\x9b]", "", output)
    output = re.sub(r"\[[0-9;]+m", "", output)  # [1m, [0m when ESC stripped
    techs = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("http") and "[" not in line:
            continue
        bracket_items = re.findall(r'\[([^\]]+)\]', line)
        for item in bracket_items:
            cleaned = item.strip()
            if cleaned and cleaned not in techs:
                techs.append(cleaned)
    return techs


def parse_nikto(output: str) -> List[Dict[str, str]]:
    """Extract vulnerability findings from nikto output."""
    findings = []
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("+ ") and ":" in line:
            findings.append({
                "detail": line[2:].strip(),
                "severity": "info",
            })
        if re.search(r'OSVDB-\d+', line):
            findings.append({
                "detail": line.lstrip("+ ").strip(),
                "severity": "medium",
            })
    seen = set()
    deduped = []
    for f in findings:
        if f["detail"] not in seen:
            seen.add(f["detail"])
            deduped.append(f)
    return deduped


def parse_gobuster(output: str) -> List[Dict[str, str]]:
    """Extract discovered directories/files from gobuster/feroxbuster/dirb."""
    dirs = []
    for line in output.splitlines():
        line = line.strip()
        dir_match = re.match(r'^(/\S+)\s+.*\(Status:\s*(\d+)', line)
        if dir_match:
            dirs.append({"path": dir_match.group(1), "status": dir_match.group(2)})
            continue
        dir_match2 = re.match(r'^\d+\w?\s+\d+\w?\s+(/\S+)', line)
        if dir_match2:
            dirs.append({"path": dir_match2.group(1), "status": "200"})
            continue
        found = re.match(r'^(https?://\S+)\s+\[(\d+)\]', line)
        if found:
            dirs.append({"path": found.group(1), "status": found.group(2)})
    return dirs


def parse_nuclei(output: str) -> List[Dict[str, str]]:
    """Extract findings from nuclei output."""
    findings = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("[INF]") or line.startswith("[WRN]"):
            continue
        parts = re.match(r'^\[([^\]]+)\]\s+\[([^\]]*)\]\s+\[([^\]]*)\]\s+(.*)', line)
        if parts:
            findings.append({
                "template": parts.group(1),
                "protocol": parts.group(2),
                "severity": parts.group(3).lower(),
                "detail": parts.group(4).strip(),
            })
    return findings


PARSERS = {
    "nmap": parse_nmap,
    "whatweb": parse_whatweb,
    "nikto": parse_nikto,
    "gobuster": parse_gobuster,
    "feroxbuster": parse_gobuster,
    "dirb": parse_gobuster,
    "nuclei": parse_nuclei,
}


# ── Recommendation Engine ────────────────────────────────────────────────────

def _resolve_effective_targets(
    findings: Dict[str, Any],
    target: str,
    discovered_hostnames: Optional[List[str]] = None,
) -> tuple:
    """Resolve effective target for IP-based commands and base_url for web commands.
    Uses nmap scan_target/redirect_hostname from output when available.
    Falls back to discovered_hostnames (.thm, .htb, etc.) for web base_url.
    Returns (ip_target, base_url).
    """
    nmap_data = findings.get("nmap", {})
    scan_target = nmap_data.get("scan_target", "")
    redirect_hostname = nmap_data.get("redirect_hostname", "")

    # IP/host for nmap, hydra, enum4linux etc
    ip_target = scan_target or target.strip()
    if not ip_target:
        ip_target = "TARGET_IP"  # placeholder when no target available

    # base_url for web tools (nikto, gobuster, nuclei)
    # 1. Prefer redirect from nmap output
    # 2. Fall back to discovered hostnames (.thm, .htb)
    # 3. Use passed target
    if redirect_hostname:
        base_url = redirect_hostname if redirect_hostname.startswith(("http://", "https://")) else redirect_hostname
    elif discovered_hostnames:
        host = discovered_hostnames[0]
        base_url = host if host.startswith(("http://", "https://")) else f"https://{host}"
    elif target.startswith(("http://", "https://")):
        base_url = target.strip()
    elif target.strip():
        base_url = f"http://{target.strip()}"
    else:
        base_url = f"http://{ip_target}"

    return (ip_target, base_url)


# Recon goals — next steps are tagged so the report supports moving to the next module
GOAL_ASSETS = "Identifying assets"
GOAL_HIDDEN = "Discovering hidden information"
GOAL_SURFACE = "Analysing attack surface"
GOAL_INTEL = "Gathering intelligence"


def suggest_next_steps(
    findings: Dict[str, Any],
    target: str = "",
    discovered_hostnames: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Generate next-step recommendations with executable commands.

    Returns a list of dicts: {reason, command, tool, goal}
    Goal is one of: Identifying assets, Discovering hidden information,
    Analysing attack surface, Gathering intelligence.
    """
    recs: List[Dict[str, Any]] = []
    nmap_data = findings.get("nmap", {})
    ports = nmap_data.get("ports", [])
    port_nums = {p["port"] for p in ports}
    services_str = " ".join(p.get("service", "") for p in ports).lower()

    # Common web ports: HTTP/HTTPS and common dev ports
    _WEB_PORTS = {80, 443, 8080, 8443, 8000, 3000, 5000, 8888, 8444, 9000}
    web_ports = bool(port_nums & _WEB_PORTS)

    ip_target, base_url = _resolve_effective_targets(findings, target, discovered_hostnames)

    if web_ports and "nikto" not in findings:
        recs.append({
            "reason": "Web server detected -- deep scan for vulnerabilities",
            "command": f"nikto -h {base_url}",
            "tool": "nikto",
            "goal": GOAL_SURFACE,
        })
    if web_ports and "gobuster" not in findings and "feroxbuster" not in findings and "dirb" not in findings:
        recs.append({
            "reason": "Web server detected -- enumerate directories and hidden files",
            "command": f"gobuster dir -u {base_url} -w /usr/share/wordlists/dirb/common.txt -t 50 -x php,bak,old,txt,env,json,sql,tar,gz",
            "tool": "gobuster",
            "goal": GOAL_HIDDEN,
        })
    # LFI / file inclusion — suggest when web server is present (common CTF vuln)
    if web_ports:
        recs.append({
            "reason": "Web server detected -- test for LFI (file/page/path/include parameters)",
            "command": f"nuclei -u {base_url} -tags lfi -severity info,low,medium,high,critical",
            "tool": "nuclei",
            "goal": GOAL_SURFACE,
        })
        recs.append({
            "reason": "Manual LFI test -- try ?file=, ?page=, ?path=, ?doc= with ../../../etc/passwd",
            "command": f"curl -s -o /dev/null -w '%{{http_code}}' \"{base_url}/?page=../../../etc/passwd\"",
            "tool": "curl",
            "goal": GOAL_SURFACE,
        })
    if 22 in port_nums:
        recs.append({
            "reason": "SSH open (port 22) -- brute force with common credentials",
            "command": f"hydra -L /usr/share/wordlists/metasploit/unix_users.txt -P /usr/share/wordlists/rockyou.txt ssh://{ip_target}",
            "tool": "hydra",
            "goal": GOAL_INTEL,
        })
    if 21 in port_nums:
        recs.append({
            "reason": "FTP open (port 21) -- check for anonymous access and list files",
            "command": f"nmap --script ftp-anon,ftp-bounce,ftp-syst -p 21 {ip_target}",
            "tool": "nmap",
            "goal": GOAL_ASSETS,
        })
    if 3306 in port_nums:
        recs.append({
            "reason": "MySQL open (3306) -- test default credentials",
            "command": f"nmap --script mysql-info,mysql-enum,mysql-brute -p 3306 {ip_target}",
            "tool": "nmap",
            "goal": GOAL_ASSETS,
        })
    if 5432 in port_nums:
        recs.append({
            "reason": "PostgreSQL open (5432) -- test default credentials",
            "command": f"nmap --script pgsql-brute -p 5432 {ip_target}",
            "tool": "nmap",
            "goal": GOAL_ASSETS,
        })
    if 445 in port_nums or 139 in port_nums:
        recs.append({
            "reason": "SMB open -- enumerate shares and users",
            "command": f"enum4linux -a {ip_target}",
            "tool": "enum4linux",
            "goal": GOAL_ASSETS,
        })
    if "wordpress" in services_str or any("wordpress" in t.lower() for t in findings.get("whatweb", [])):
        recs.append({
            "reason": "WordPress detected -- scan for plugin/theme vulnerabilities",
            "command": f"wpscan --url {base_url} --enumerate vp,vt,u --api-token YOUR_TOKEN",
            "tool": "wpscan",
            "goal": GOAL_SURFACE,
        })
    if "apache" in services_str:
        recs.append({
            "reason": "Apache detected -- check version CVEs and misconfigurations",
            "command": f"nmap --script http-apache-server-status,http-apache-negotiation -p 80,443 {ip_target}",
            "tool": "nmap",
            "goal": GOAL_SURFACE,
        })
    if "nginx" in services_str:
        recs.append({
            "reason": "Nginx detected -- test for path traversal and misconfigurations",
            "command": f"nuclei -u {base_url} -tags nginx",
            "tool": "nuclei",
            "goal": GOAL_SURFACE,
        })

    dirs = findings.get("gobuster", []) or findings.get("feroxbuster", []) or findings.get("dirb", [])
    login_dirs = [d for d in dirs if any(k in d.get("path", "").lower() for k in
                  ("/admin", "/login", "/wp-admin", "/dashboard", "/panel", "/manager"))]
    if login_dirs:
        login_url = login_dirs[0]["path"]
        if not login_url.startswith("http"):
            login_url = f"{base_url}{login_url}"
        recs.append({
            "reason": f"Login page found at {login_dirs[0]['path']} -- brute force credentials",
            "command": f"hydra -L /usr/share/wordlists/metasploit/unix_users.txt -P /usr/share/wordlists/rockyou.txt {login_url} http-post-form '/login:user=^USER^&pass=^PASS^:F=incorrect'",
            "tool": "hydra",
            "goal": GOAL_INTEL,
        })

    nuclei_data = findings.get("nuclei", [])
    crit_high = [f for f in nuclei_data if f.get("severity") in ("critical", "high")]
    if crit_high:
        templates = ",".join(set(f["template"] for f in crit_high[:5]))
        recs.append({
            "reason": f"Nuclei found {len(crit_high)} critical/high issue(s) -- re-scan focused templates",
            "command": f"nuclei -u {base_url} -t {templates} -severity critical,high",
            "tool": "nuclei",
            "goal": GOAL_SURFACE,
        })

    if web_ports:
        recs.append({
            "reason": "Deep scan with all nuclei vulnerability templates",
            "command": f"nuclei -u {base_url} -severity critical,high,medium",
            "tool": "nuclei",
            "goal": GOAL_SURFACE,
        })
        recs.append({
            "reason": "Fuzz for hidden parameters and injection points",
            "command": f"ffuf -u {base_url}/FUZZ -w /usr/share/wordlists/dirb/common.txt -mc 200,301,302,403",
            "tool": "ffuf",
            "goal": GOAL_HIDDEN,
        })
        recs.append({
            "reason": "Test for SQL injection (forms, query params) with nuclei",
            "command": f"nuclei -u {base_url} -tags sqli -severity info,low,medium,high,critical",
            "tool": "nuclei",
            "goal": GOAL_SURFACE,
        })
        recs.append({
            "reason": "Fuzz LFI parameter names (then test ?PARAM=../../../etc/passwd manually)",
            "command": f"ffuf -u {base_url}/?FUZZ=../../../etc/passwd -w /usr/share/wordlists/SecLists/Discovery/Web-Content/burp-parameter-names.txt -mc 200,500 -fs 0",
            "tool": "ffuf",
            "goal": GOAL_HIDDEN,
        })

    if not recs:
        recs.append({
            "reason": "No significant findings -- expand scope with a full port + UDP scan",
            "command": f"nmap -sU -sS -p- --min-rate 1000 {ip_target}",
            "tool": "nmap",
            "goal": GOAL_ASSETS,
        })

    return recs


def suggest_next_steps_text(
    findings: Dict[str, Any],
    target: str = "",
    discovered_hostnames: Optional[List[str]] = None,
) -> List[str]:
    """Flat text version for Markdown/HTML report output (includes goal)."""
    steps = suggest_next_steps(findings, target, discovered_hostnames)
    return [
        f"[{s.get('goal', 'Next step')}] {s['reason']}  -->  `{s['command']}`"
        for s in steps
    ]


# ── Report Generator ─────────────────────────────────────────────────────────

class ReconReport:
    """Collects phase output and generates analysis reports."""

    def __init__(self, target: str, preset: str = "full"):
        self.target = target
        self.preset = preset
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.phase_outputs: Dict[str, str] = {}
        self.findings: Dict[str, Any] = {}

    def add_phase_output(self, tool: str, output: str):
        self.phase_outputs[tool] = output

    def finalize(self):
        self.end_time = datetime.now()
        for tool, output in self.phase_outputs.items():
            parser = PARSERS.get(tool)
            if parser:
                self.findings[tool] = parser(output)

    def get_findings_summary(self) -> Dict[str, Any]:
        """Return a structured summary of key findings for UI display."""
        self.finalize()
        summary: Dict[str, Any] = {}

        nmap_data = self.findings.get("nmap", {})
        ports = nmap_data.get("ports", [])
        if ports:
            summary["ports"] = ports
        os_info = nmap_data.get("os", [])
        if os_info:
            summary["os"] = os_info

        whatweb = self.findings.get("whatweb", [])
        if whatweb:
            summary["technologies"] = whatweb

        nikto = self.findings.get("nikto", [])
        if nikto:
            summary["vulnerabilities"] = nikto[:20]

        for tool_name in ("gobuster", "feroxbuster", "dirb"):
            dirs = self.findings.get(tool_name, [])
            if dirs:
                summary["directories"] = dirs[:30]
                break

        nuclei = self.findings.get("nuclei", [])
        if nuclei:
            summary["nuclei"] = nuclei

        return summary

    def get_next_steps(self) -> List[Dict[str, str]]:
        """Return executable next-step recommendations."""
        self.finalize()
        discovered = _extract_discovered_hostnames(self.phase_outputs)
        return suggest_next_steps(self.findings, self.target, discovered)

    def generate_markdown(self) -> str:
        self.finalize()
        discovered = _extract_discovered_hostnames(self.phase_outputs)
        recs = suggest_next_steps_text(self.findings, self.target, discovered)
        duration = (self.end_time - self.start_time).total_seconds()

        lines = [
            f"# PlanetHack Recon Report",
            f"",
            f"## Recon objectives (feed next modules)",
            f"- **Identifying assets** — Ports, hosts, tech stack.",
            f"- **Discovering hidden information** — Dirs, backups, configs.",
            f"- **Analysing attack surface** — Vulns, misconfigs.",
            f"- **Gathering intelligence** — Data for exploitation.",
            f"",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| Target | `{self.target}` |",
            f"| Preset | {self.preset} |",
            f"| Date | {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} |",
            f"| Duration | {duration:.0f}s |",
            f"| Phases | {len(self.phase_outputs)} |",
            f"",
        ]

        # Parsed findings
        nmap_data = self.findings.get("nmap", {})
        ports = nmap_data.get("ports", [])
        if ports:
            lines.append("## Open Ports and Services")
            lines.append("")
            lines.append("| Port | Proto | State | Service |")
            lines.append("|------|-------|-------|---------|")
            for p in ports:
                lines.append(f"| {p['port']} | {p['proto']} | {p['state']} | {p['service']} |")
            lines.append("")

        os_info = nmap_data.get("os", [])
        if os_info:
            lines.append("## OS Detection")
            lines.append("")
            for o in os_info:
                lines.append(f"- {o}")
            lines.append("")

        whatweb = self.findings.get("whatweb", [])
        if whatweb:
            lines.append("## Web Technologies")
            lines.append("")
            for t in whatweb:
                lines.append(f"- {t}")
            lines.append("")

        nikto = self.findings.get("nikto", [])
        if nikto:
            lines.append("## Vulnerability Scan (Nikto)")
            lines.append("")
            for f in nikto[:30]:
                lines.append(f"- [{f['severity'].upper()}] {f['detail']}")
            lines.append("")

        for tool_name in ("gobuster", "feroxbuster", "dirb"):
            dirs = self.findings.get(tool_name, [])
            if dirs:
                lines.append(f"## Discovered Paths ({tool_name})")
                lines.append("")
                lines.append("| Path | Status |")
                lines.append("|------|--------|")
                for d in dirs[:50]:
                    lines.append(f"| {d['path']} | {d['status']} |")
                lines.append("")
                break

        nuclei = self.findings.get("nuclei", [])
        if nuclei:
            lines.append("## Nuclei Findings")
            lines.append("")
            lines.append("| Severity | Template | Detail |")
            lines.append("|----------|----------|--------|")
            for f in nuclei:
                lines.append(f"| {f['severity'].upper()} | {f['template']} | {f['detail']} |")
            lines.append("")

        lines.append("## Recommendations / Next Steps")
        lines.append("")
        for i, r in enumerate(recs, 1):
            lines.append(f"{i}. {r}")
        lines.append("")

        lines.append("---")
        lines.append(f"*Generated by PlanetHack // HCKNKnuckle // {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")

        return "\n".join(lines)

    def generate_html(self) -> str:
        self.finalize()
        discovered = _extract_discovered_hostnames(self.phase_outputs)
        recs = suggest_next_steps_text(self.findings, self.target, discovered)
        duration = (self.end_time - self.start_time).total_seconds()

        h = html_escape

        parts = [
            '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '<title>PlanetHack Recon Report</title>',
            '<style>',
            ':root{--bg:#0a0a0a;--panel:#0d1117;--fg:#00ff41;--cyan:#00ffff;--mag:#ff00ff;',
            '--yellow:#ffff00;--red:#ff0040;--dim:#00aa28;--border:#004d14;}',
            '*{margin:0;padding:0;box-sizing:border-box;}',
            'body{background:var(--bg);color:var(--fg);font-family:"Courier New",monospace;padding:30px;line-height:1.6;}',
            'h1{color:var(--cyan);font-size:20px;margin-bottom:16px;letter-spacing:2px;}',
            'h2{color:var(--mag);font-size:15px;margin:24px 0 10px;border-bottom:1px solid var(--border);padding-bottom:4px;}',
            'table{border-collapse:collapse;width:100%;margin-bottom:16px;}',
            'th{background:var(--panel);color:var(--cyan);text-align:left;padding:6px 12px;font-size:12px;border:1px solid var(--border);}',
            'td{padding:6px 12px;border:1px solid var(--border);font-size:12px;}',
            'ul,ol{padding-left:24px;margin-bottom:14px;}',
            'li{margin-bottom:4px;font-size:13px;}',
            '.meta{color:var(--dim);font-size:11px;margin-top:30px;border-top:1px solid var(--border);padding-top:8px;}',
            '.sev-critical,.sev-high{color:var(--red);font-weight:bold;}',
            '.sev-medium{color:var(--yellow);}',
            '.sev-info,.sev-low{color:var(--dim);}',
            '</style></head><body>',
            '<h1>[ PLANETHACK RECON REPORT ]</h1>',
            '<p style="color:var(--dim);font-size:12px;margin-bottom:16px;">'
            'Recon objectives: <strong>Identifying assets</strong> (ports, tech) &rarr; '
            '<strong>Discovering hidden information</strong> (dirs, backups) &rarr; '
            '<strong>Analysing attack surface</strong> (nikto, nuclei) &rarr; '
            '<strong>Gathering intelligence</strong> for next modules.</p>',
            '<table>',
            f'<tr><th>Target</th><td>{h(self.target)}</td></tr>',
            f'<tr><th>Preset</th><td>{h(self.preset)}</td></tr>',
            f'<tr><th>Date</th><td>{self.start_time.strftime("%Y-%m-%d %H:%M:%S")}</td></tr>',
            f'<tr><th>Duration</th><td>{duration:.0f}s</td></tr>',
            f'<tr><th>Phases</th><td>{len(self.phase_outputs)}</td></tr>',
            '</table>',
        ]

        nmap_data = self.findings.get("nmap", {})
        ports = nmap_data.get("ports", [])
        if ports:
            parts.append('<h2>Open Ports and Services</h2><table>')
            parts.append('<tr><th>Port</th><th>Proto</th><th>State</th><th>Service</th></tr>')
            for p in ports:
                parts.append(f'<tr><td>{p["port"]}</td><td>{p["proto"]}</td><td>{p["state"]}</td><td>{h(p["service"])}</td></tr>')
            parts.append('</table>')

        whatweb = self.findings.get("whatweb", [])
        if whatweb:
            parts.append('<h2>Web Technologies</h2><ul>')
            for t in whatweb:
                parts.append(f'<li>{h(t)}</li>')
            parts.append('</ul>')

        nikto = self.findings.get("nikto", [])
        if nikto:
            parts.append('<h2>Vulnerability Scan (Nikto)</h2><ul>')
            for f in nikto[:30]:
                sev_cls = f"sev-{f['severity']}"
                parts.append(f'<li><span class="{sev_cls}">[{h(f["severity"].upper())}]</span> {h(f["detail"])}</li>')
            parts.append('</ul>')

        for tool_name in ("gobuster", "feroxbuster", "dirb"):
            dirs = self.findings.get(tool_name, [])
            if dirs:
                parts.append(f'<h2>Discovered Paths ({h(tool_name)})</h2><table>')
                parts.append('<tr><th>Path</th><th>Status</th></tr>')
                for d in dirs[:50]:
                    parts.append(f'<tr><td>{h(d["path"])}</td><td>{d["status"]}</td></tr>')
                parts.append('</table>')
                break

        nuclei = self.findings.get("nuclei", [])
        if nuclei:
            parts.append('<h2>Nuclei Findings</h2><table>')
            parts.append('<tr><th>Severity</th><th>Template</th><th>Detail</th></tr>')
            for f in nuclei:
                sev_cls = f"sev-{f['severity']}"
                parts.append(f'<tr><td class="{sev_cls}">{h(f["severity"].upper())}</td><td>{h(f["template"])}</td><td>{h(f["detail"])}</td></tr>')
            parts.append('</table>')

        parts.append('<h2>Recommendations / Next Steps</h2><ol>')
        for r in recs:
            parts.append(f'<li>{h(r)}</li>')
        parts.append('</ol>')

        parts.append(f'<div class="meta">Generated by PlanetHack // HCKNKnuckle // {self.end_time.strftime("%Y-%m-%d %H:%M:%S")}</div>')
        parts.append('</body></html>')

        return "\n".join(parts)

    def save(self, fmt: str = "md", output_dir: str = "reports") -> str:
        """Save report to file. Returns the file path."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_target = re.sub(r'[^a-zA-Z0-9._-]', '_', self.target)[:40]

        if fmt == "html":
            content = self.generate_html()
            path = out / f"recon_{safe_target}_{ts}.html"
        else:
            content = self.generate_markdown()
            path = out / f"recon_{safe_target}_{ts}.md"

        path.write_text(content, encoding="utf-8")
        return str(path)
