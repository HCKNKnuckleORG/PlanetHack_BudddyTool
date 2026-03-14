"""
Session Log -- accumulates ALL tool output across the entire session.

Every tool execution (recon phase, module, next-step command) writes its
output here. The session builds a cumulative report and attack recommendations
that grow smarter as more data is collected.
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

from core.report import (
    PARSERS, suggest_next_steps, ReconReport,
)

_SESSIONS_DIR = Path("sessions")


class SessionLog:
    """Persistent, cumulative log of all tool output in a session."""

    def __init__(self, target: str = ""):
        self.target = target
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now()
        self.entries: List[Dict[str, Any]] = []
        self.tool_outputs: Dict[str, str] = {}
        self.findings: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._on_update_callbacks: List[Callable] = []

        _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self._log_path = _SESSIONS_DIR / f"session_{self.session_id}.jsonl"

    def set_target(self, target: str):
        self.target = target

    def on_update(self, callback: Callable):
        """Register a callback that fires after each tool completes."""
        self._on_update_callbacks.append(callback)

    def record_output(self, tool: str, command: str, output: str,
                      exit_code: int = 0, source: str = "recon"):
        """Record a tool's output. Called after every tool finishes."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool,
            "command": command,
            "source": source,
            "exit_code": exit_code,
            "output_length": len(output),
        }

        with self._lock:
            self.entries.append(entry)

            if tool in self.tool_outputs:
                self.tool_outputs[tool] += "\n" + output
            else:
                self.tool_outputs[tool] = output

            parser = PARSERS.get(tool)
            if parser:
                self.findings[tool] = parser(self.tool_outputs[tool])

            self._write_to_disk(entry, output)

        for cb in self._on_update_callbacks:
            try:
                cb(self)
            except Exception:
                pass

    def _write_to_disk(self, entry: dict, output: str):
        """Append entry + output to the session log file."""
        import logging
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
                for line in output.splitlines():
                    f.write(f"  | {line}\n")
                f.write("---\n")
        except Exception as e:
            logging.getLogger(__name__).error(
                "session _write_to_disk failed: %s path=%s", e, self._log_path, exc_info=True
            )

    def get_findings_raw(self) -> Dict[str, Any]:
        """Return raw parsed findings (tool -> parsed data) for module readiness evaluation."""
        with self._lock:
            return dict(self.findings)

    def get_findings_summary(self) -> Dict[str, Any]:
        """Return cumulative findings from all tools run so far."""
        with self._lock:
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

            summary["tools_run"] = list(self.tool_outputs.keys())
            summary["total_entries"] = len(self.entries)

            return summary

    def get_findings_by_tool(self) -> Dict[str, Any]:
        """Return findings grouped by tool for dashboard display. Human-readable structure."""
        with self._lock:
            result: Dict[str, Any] = {}
            tools_to_show = set(self.findings.keys()) | set(self.tool_outputs.keys())
            for tool in sorted(tools_to_show):
                data = self.findings.get(tool)
                if tool == "nmap":
                    ports = (data or {}).get("ports", [])
                    os_info = (data or {}).get("os", [])
                    scan_target = (data or {}).get("scan_target", "")
                    redirect_hostname = (data or {}).get("redirect_hostname", "")
                    result[tool] = {
                        "ports": ports,
                        "os": os_info,
                        "scan_target": scan_target,
                        "redirect_hostname": redirect_hostname,
                        "summary": f"{len(ports)} port(s) open" + (f", OS: {os_info[0][:60]}..." if os_info else ""),
                    }
                elif tool == "whatweb":
                    techs = data if isinstance(data, list) else []
                    result[tool] = {
                        "technologies": techs,
                        "summary": ", ".join(techs[:8]) if techs else "None detected",
                    }
                elif tool == "nikto":
                    items = data if isinstance(data, list) else []
                    result[tool] = {
                        "findings": items[:15],
                        "count": len(items),
                        "summary": f"{len(items)} finding(s)",
                    }
                elif tool in ("gobuster", "feroxbuster", "dirb"):
                    dirs = data if isinstance(data, list) else []
                    result[tool] = {
                        "directories": dirs[:25],
                        "count": len(dirs),
                        "summary": f"{len(dirs)} path(s) discovered",
                    }
                elif tool == "nuclei":
                    items = data if isinstance(data, list) else []
                    crits = [f for f in items if isinstance(f, dict) and f.get("severity") in ("critical", "high")]
                    result[tool] = {
                        "findings": items[:20],
                        "count": len(items),
                        "critical_high": len(crits),
                        "summary": f"{len(items)} total, {len(crits)} critical/high",
                    }
                else:
                    raw_output = self.tool_outputs.get(tool, "")
                    if isinstance(raw_output, str) and len(raw_output) > 500:
                        summary = raw_output[:200] + "... (" + str(len(raw_output)) + " chars)"
                    else:
                        summary = str(data)[:80] + "..." if data and len(str(data)) > 80 else (str(raw_output)[:80] if raw_output else "—")
                    result[tool] = {"raw": data or raw_output, "summary": summary}
            return result

    def get_attack_recommendations(self) -> List[Dict[str, str]]:
        """Return cumulative attack recommendations based on everything collected."""
        with self._lock:
            from core.report import _extract_discovered_hostnames
            discovered = _extract_discovered_hostnames(self.tool_outputs)
            return suggest_next_steps(self.findings, self.target, discovered)

    def build_cumulative_report(self) -> ReconReport:
        """Build a full ReconReport from all accumulated data."""
        with self._lock:
            report = ReconReport(self.target)
            report.start_time = self.start_time
            for tool, output in self.tool_outputs.items():
                report.add_phase_output(tool, output)
            return report

    @staticmethod
    def parse_phase_summary(tool: str, output: str) -> List[str]:
        """Parse a single phase's output and return concise summary lines."""
        parser = PARSERS.get(tool)
        if not parser:
            line_count = len(output.strip().splitlines())
            return [f"{tool.upper()}: {line_count} line(s) of output"]

        parsed = parser(output)
        lines: List[str] = []

        if tool == "nmap":
            ports = parsed.get("ports", [])
            if ports:
                port_strs = [f"{p['port']}/{p['proto']} {p['service']}" for p in ports[:10]]
                lines.append(f"OPEN PORTS: {', '.join(port_strs)}")
            os_info = parsed.get("os", [])
            if os_info:
                lines.append(f"OS DETECTED: {', '.join(os_info[:3])}")
            if not ports:
                lines.append("No open ports found in this scan range")

        elif tool == "whatweb":
            if parsed:
                lines.append(f"TECH STACK: {', '.join(parsed[:8])}")
            else:
                lines.append("No technologies detected")

        elif tool == "nikto":
            if parsed:
                lines.append(f"FINDINGS: {len(parsed)} issue(s)")
                for item in parsed[:5]:
                    lines.append(f"  - {item[:100]}")
            else:
                lines.append("No issues detected")

        elif tool in ("gobuster", "feroxbuster", "dirb"):
            if parsed:
                lines.append(f"DIRECTORIES: {len(parsed)} path(s)")
                for d in parsed[:8]:
                    lines.append(f"  - {d}")
            else:
                lines.append("No directories discovered")

        elif tool == "nuclei":
            if parsed:
                crits = [f for f in parsed if f.get("severity") in ("critical", "high")]
                lines.append(f"FINDINGS: {len(parsed)} total, {len(crits)} critical/high")
                for f in parsed[:5]:
                    lines.append(f"  [{f.get('severity', '?').upper()}] {f.get('name', f.get('template', '?'))}")
            else:
                lines.append("No vulnerabilities detected")

        if not lines:
            lines.append(f"{tool.upper()}: analysis complete")
        return lines

    def get_log_path(self) -> str:
        return str(self._log_path)

    def get_run_history(self) -> List[Dict[str, Any]]:
        """Return a summary of all tools run so far."""
        with self._lock:
            return [
                {
                    "tool": e["tool"],
                    "command": e["command"],
                    "source": e["source"],
                    "time": e["timestamp"],
                    "exit_code": e["exit_code"],
                }
                for e in self.entries
            ]
