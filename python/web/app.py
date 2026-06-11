"""
PlanetHack Web UI -- Flask application
"""

import uuid
import time
import random
import threading
import json
import os
import re
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from typing import Dict, Any, Optional


def _safe_download_name(path: str) -> str:
    """Return a header-safe attachment filename derived from a file path."""
    name = os.path.basename(str(path))
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name or "report"

from flask import (
    Flask, render_template, request, jsonify, Response, redirect, url_for,
    send_file, send_from_directory,
)

from core.recon_plan import build_recon_plan
from core.tool_runner import resolve_tool_command, run_tool, run_tools_sequential
from core.report import ReconReport
from core.host_check import run_preflight_check, add_to_hosts_file
from core.session import SessionLog
from modules import MODULE_REGISTRY
from utils.helpers import is_ip_address, validate_url

MOVIE_QUOTES = [
    ("Hack the Planet!", "Hackers"),
    ("Mess with the best, die like the rest.", "Hackers"),
    ("There is no right and wrong. There's only fun and boring.", "Hackers"),
    ("Type 'cookie', you idiot.", "Hackers"),
    ("The password is... swordfish.", "Swordfish"),
    ("Nothing is impossible.", "Swordfish"),
    ("Anybody wanna shut down the DOD?", "Swordfish"),
    ("Follow the white rabbit.", "The Matrix"),
    ("There is no spoon.", "The Matrix"),
    ("I know kung fu.", "The Matrix"),
    ("Welcome to the real world.", "The Matrix"),
    ("Free your mind.", "The Matrix"),
    ("The Matrix has you...", "The Matrix"),
    ("Unfortunately, no one can be told what the Matrix is.", "The Matrix"),
    ("Guns. Lots of guns.", "The Matrix"),
    ("Not like this... not like this.", "The Matrix"),
    ("Do not try and bend the spoon. That's impossible.", "The Matrix"),
]

MODULE_LIST = [
    ("RECON", "recon", "#00ff41"),
    ("SQL INJECTION", "sql", "#00ffff"),
    ("XSS", "xss", "#00ffff"),
    ("OPEN REDIRECT", "open_redirect", "#ffff00"),
    ("CLICKJACKING", "clickjacking", "#ffff00"),
    ("CSRF", "csrf", "#ffff00"),
    ("ACCESS CTRL", "access_control", "#ff00ff"),
    ("AUTH", "auth", "#ff00ff"),
    ("FILE UPLOAD", "file_upload", "#ff00ff"),
    ("BIZ LOGIC", "business_logic", "#ff8800"),
    ("SSRF", "ssrf", "#ff8800"),
    ("DESERIALIZATION", "deserialization", "#ff8800"),
    ("XXE", "xxe", "#ff0040"),
    ("SSTI", "template_injection", "#ff0040"),
    ("RCE", "rce", "#ff0040"),
    ("API SEC", "api", "#00ffff"),
    ("INFO DISC", "information_disclosure", "#00ffff"),
    ("SESSION", "session", "#00ff41"),
    ("SMUGGLING", "request_smuggling", "#00ff41"),
    ("WEB CACHE", "cache", "#00ff41"),
    ("FUZZING", "fuzzing", "#ffff00"),
    ("BRUTE FORCE", "brute_force", "#ff0040"),
]

ASCII_BANNER = r"""
  ██████╗ ██╗      █████╗ ███╗   ██╗███████╗████████╗
  ██╔══██╗██║     ██╔══██╗████╗  ██║██╔════╝╚══██╔══╝
  ██████╔╝██║     ███████║██╔██╗ ██║█████╗     ██║
  ██╔═══╝ ██║     ██╔══██║██║╚██╗██║██╔══╝     ██║
  ██║     ███████╗██║  ██║██║ ╚████║███████╗   ██║
  ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝

  ██╗  ██╗ █████╗  ██████╗██╗  ██╗
  ██║  ██║██╔══██╗██╔════╝██║ ██╔╝
  ███████║███████║██║     █████╔╝
  ██╔══██║██╔══██║██║     ██╔═██╗
  ██║  ██║██║  ██║╚██████╗██║  ██╗
  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
"""

# ── Global session log -- accumulates output from ALL runs ───────────────────

_session_log = SessionLog()

# ── Job store (shared with API blueprint) ─────────────────────────────────────

from web.jobs import create_job as _create_job, get_job as _get_job


# ── Flask App Factory ────────────────────────────────────────────────────────

def create_app(config=None, logger=None):
    from pathlib import Path
    template_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
    )
    app.secret_key = uuid.uuid4().hex

    app.config["PH_CONFIG"] = config
    app.config["PH_LOGGER"] = logger

    # Log uncaught exceptions to errors log (logs/planethack_errors.log)
    # Skip HTTPException (404, 400, etc.) - let Flask handle those normally
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            raise  # Let Flask handle 404, 400, etc. normally
        if logger:
            logger.exception(f"Unhandled exception: {e}")
        return jsonify({"error": "Internal server error"}), 500

    # Register API v1 blueprint (for TypeScript SPA / external consumers)
    from web.api_blueprint import api_v1
    app.register_blueprint(api_v1)

    # CORS for SPA dev server (Vite typically on 5173)
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    def _validate_target(target: str) -> bool:
        target = target.strip()
        if not target:
            return False
        if target.startswith(("http://", "https://")):
            return validate_url(target)
        if is_ip_address(target):
            return True
        if "." in target:
            return True
        return False

    # ── React SPA (default UI when frontend is built) ─────────────────────
    _project_root = Path(__file__).resolve().parent.parent
    _spa_dist = _project_root / "frontend" / "dist"
    _use_spa = (_spa_dist / "index.html").exists()
    if _use_spa and logger:
        logger.info("React SPA build detected: serving TypeScript UI at /")

    @app.route("/assets/<path:filename>")
    def spa_assets(filename):
        """Serve React SPA static assets (JS, CSS)."""
        if _use_spa and (_spa_dist / "assets").exists():
            return send_from_directory(_spa_dist / "assets", filename)
        from flask import abort
        abort(404)

    # ── Routes ───────────────────────────────────────────────────────────

    @app.route("/")
    def home():
        if _use_spa:
            return send_file(_spa_dist / "index.html")
        return render_template(
            "home.html",
            banner=ASCII_BANNER,
        )

    @app.route("/report-history")
    def report_history():
        """Bug bounty report from recon session history."""
        if _use_spa:
            return send_file(_spa_dist / "index.html")
        if logger:
            logger.debug("report_history: loading session findings")
        summary = _session_log.get_findings_summary()
        next_steps = _session_log.get_attack_recommendations()
        history = _session_log.get_run_history()
        findings_by_tool = _session_log.get_findings_by_tool()
        has_data = bool(summary.get("tools_run"))
        return render_template(
            "report_history.html",
            summary=summary,
            findings_by_tool=findings_by_tool,
            next_steps=next_steps,
            history=history,
            has_data=has_data,
            target=_session_log.target,
            log_path=_session_log.get_log_path(),
        )

    @app.route("/recon")
    def recon():
        if _use_spa:
            return send_file(_spa_dist / "index.html")
        return render_template("recon.html")

    @app.route("/recon/preflight", methods=["POST"])
    def recon_preflight():
        """Pre-flight check: detect redirects, validate /etc/hosts."""
        target = request.form.get("target", "").strip()
        preset = request.form.get("preset", "full")
        if not target:
            return jsonify({"error": "No target provided"}), 400
        result = run_preflight_check(target, preset)
        return jsonify(result)

    @app.route("/recon/add-host", methods=["POST"])
    def recon_add_host():
        """Add an entry to /etc/hosts (requires sudo on the server)."""
        data = request.get_json(silent=True) or {}
        ip = data.get("ip", "").strip()
        hostnames = data.get("hostnames", [])
        if not ip or not hostnames:
            return jsonify({"error": "IP and hostnames required"}), 400
        ok, msg = add_to_hosts_file(ip, hostnames)
        return jsonify({"success": ok, "message": msg})

    @app.route("/recon/plan", methods=["POST"])
    def recon_plan():
        target = request.form.get("target", "").strip()
        preset = request.form.get("preset", "full")

        if not target or not _validate_target(target):
            return jsonify({"error": "Invalid target"}), 400

        try:
            phases = build_recon_plan(target, config, preset=preset)
            for phase in phases:
                cmd = resolve_tool_command(phase)
                if not cmd:
                    phase["resolved_cmd"] = phase.get("command", "(tool not found)")
                    phase["tool_available"] = False
                else:
                    phase["resolved_cmd"] = cmd
                    phase["tool_available"] = True
            return jsonify({"phases": phases, "target": target})
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            if logger:
                logger.error(f"Error building plan: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/recon/execute", methods=["POST"])
    def recon_execute():
        data = request.get_json(silent=True) or {}
        phases_data = data.get("phases", [])
        target = data.get("target", "").strip()
        preset = data.get("preset", "full")
        if not target or not _validate_target(target):
            return jsonify({"error": "Invalid target"}), 400
        if not phases_data:
            if logger:
                logger.warning("recon_execute: no phases provided")
            return jsonify({"error": "No phases provided"}), 400

        # Rebuild plan server-side: never trust client-sent resolved_cmd (RCE prevention)
        try:
            phases_data = build_recon_plan(target, config, preset=preset)
            for phase in phases_data:
                cmd = resolve_tool_command(phase)
                phase["resolved_cmd"] = phase.get("command", "(tool not found)") if not cmd else cmd
                phase["tool_available"] = cmd is not None
        except (ValueError, Exception) as e:
            if logger:
                logger.error(f"Error building recon plan: {e}")
            return jsonify({"error": str(e)}), 400

        job_id = _create_job(target=target)
        if logger:
            logger.info(f"recon_execute: job={job_id} target={target} phases={len(phases_data)}")
        job = _get_job(job_id)
        q = job["queue"]

        total = len([p for p in phases_data if p.get("tool_available", False)])

        _session_log.set_target(target)

        def _run():
            collected: Dict[str, str] = {}
            phase_idx = 0
            for phase in phases_data:
                cmd = phase.get("resolved_cmd")
                available = phase.get("tool_available", False)
                if not cmd or not available:
                    q.put(f"[!] Phase {phase.get('phase', '?')}: {phase.get('tool', '?')} not found, skipping\n")
                    continue

                tool_name = phase.get("tool", "unknown")
                phase_buf: list = []
                phase_idx += 1

                progress_msg = f"event: progress\ndata: {phase_idx}|{total}|{tool_name}|{phase.get('purpose', '')}\n\n"
                q.put(("__progress__", progress_msg))

                q.put(f"\n[*] === Phase {phase.get('phase', '?')}: {phase.get('purpose', '')} ({tool_name}) ===\n")
                q.put(f"[*] $ {cmd}\n\n")

                done_event = threading.Event()
                exit_code = [None]

                def on_output(line, _buf=phase_buf):
                    _buf.append(line)
                    q.put(line)

                def on_complete(code):
                    exit_code[0] = code
                    done_event.set()

                run_tool(cmd, on_output, on_complete)
                done_event.wait()

                phase_output = "".join(phase_buf)
                collected[tool_name] = phase_output
                _session_log.record_output(tool_name, cmd, phase_output,
                                           exit_code[0] or 0, source="recon")
                q.put(f"\n[+] Phase {phase.get('phase', '?')} completed (exit {exit_code[0]})\n")

                import json as _json
                summary_lines = SessionLog.parse_phase_summary(tool_name, phase_output)
                confirm_data = _json.dumps({
                    "phase": phase.get("phase", "?"),
                    "tool": tool_name,
                    "purpose": phase.get("purpose", ""),
                    "exit_code": exit_code[0] or 0,
                    "findings": summary_lines,
                    "phase_idx": phase_idx,
                    "total": total,
                })
                confirm_msg = f"event: phase_confirm\ndata: {confirm_data}\n\n"
                q.put(("__progress__", confirm_msg))

                job["confirm_event"].clear()
                job["confirm_choice"] = True
                job["confirm_event"].wait(timeout=600)
                if not job["confirm_choice"]:
                    q.put(f"\n[!] === USER STOPPED AFTER PHASE {phase.get('phase', '?')} ===\n")
                    break

            job["collected_output"] = collected
            report = ReconReport(target)
            for tool, output in collected.items():
                report.add_phase_output(tool, output)
            job["report"] = report
            if logger:
                logger.info(f"recon_execute: job={job_id} complete, tools={list(collected.keys())}")

            done_progress = f"event: progress\ndata: {total}|{total}|done|ALL PHASES COMPLETE\n\n"
            q.put(("__progress__", done_progress))

            q.put(None)  # sentinel
            job["done"] = True

        threading.Thread(target=_run, daemon=True).start()
        return jsonify({"job_id": job_id})

    @app.route("/recon/confirm/<job_id>", methods=["POST"])
    def recon_confirm(job_id):
        """User confirms to continue or stop after a phase."""
        job = _get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        data = request.get_json(silent=True) or {}
        job["confirm_choice"] = data.get("continue", True)
        job["confirm_event"].set()
        return jsonify({"ok": True})

    @app.route("/modules")
    def modules():
        if _use_spa:
            return send_file(_spa_dist / "index.html")
        return render_template("modules.html", modules=MODULE_LIST)

    @app.route("/modules/run", methods=["POST"])
    def modules_run():
        data = request.get_json(silent=True) or {}
        module_id = data.get("module_id", "")
        target = data.get("target", "").strip()

        if not target or not _validate_target(target):
            return jsonify({"error": "Invalid target"}), 400

        if module_id == "recon":
            preset = data.get("preset", "htb")
            try:
                phases = build_recon_plan(target, config, preset=preset)
                for phase in phases:
                    cmd = resolve_tool_command(phase)
                    phase["resolved_cmd"] = phase.get("command", "(tool not found)") if not cmd else cmd
                    phase["tool_available"] = cmd is not None
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            job_id = _create_job(target=target)
            job = _get_job(job_id)
            q = job["queue"]
            _session_log.set_target(target)
            total_phases = len([p for p in phases if p.get("tool_available")])

            def _run_recon():
                collected = {}
                phase_idx = 0
                for phase in phases:
                    cmd = phase.get("resolved_cmd")
                    if not cmd or not phase.get("tool_available"):
                        q.put(f"[!] Phase {phase.get('phase', '?')}: {phase.get('tool', '?')} not found, skipping\n")
                        continue
                    tool_name = phase.get("tool", "unknown")
                    phase_buf = []
                    phase_idx += 1
                    q.put(("__progress__", f"event: progress\ndata: {phase_idx}|{total_phases}|{tool_name}|{phase.get('purpose', '')}\n\n"))
                    q.put(f"\n[*] === Phase {phase.get('phase', '?')}: {phase.get('purpose', '')} ({tool_name}) ===\n")
                    q.put(f"[*] $ {cmd}\n\n")
                    done_ev = threading.Event()
                    exit_code = [None]
                    batch = []
                    BATCH_SIZE = 25
                    def flush_batch():
                        nonlocal batch
                        if batch:
                            q.put("".join(batch))
                            batch = []
                    def on_out(line, _b=phase_buf):
                        _b.append(line)
                        batch.append(line)
                        if len(batch) >= BATCH_SIZE:
                            flush_batch()
                    def on_done(code):
                        exit_code[0] = code
                        done_ev.set()
                    run_tool(cmd, on_out, on_done)
                    done_ev.wait()
                    flush_batch()
                    phase_output = "".join(phase_buf)
                    collected[tool_name] = {
                        "output": phase_output,
                        "cmd": cmd,
                        "exit_code": exit_code[0] or 0,
                    }
                    q.put(f"\n[+] Phase {phase.get('phase', '?')} completed (exit {exit_code[0]})\n")
                job["collected_output"] = collected
                report = ReconReport(target)
                for t, detail in collected.items():
                    report.add_phase_output(t, detail["output"])
                job["report"] = report
                q.put(("__progress__", f"event: progress\ndata: {total_phases}|{total_phases}|done|ALL PHASES COMPLETE\n\n"))
                q.put(f"\n[*] All recon phases complete.\n")
                q.put(None)
                job["done"] = True

            threading.Thread(target=_run_recon, daemon=True).start()
            return jsonify({"job_id": job_id})

        module_class = MODULE_REGISTRY.get(module_id)
        if not module_class:
            return jsonify({"error": f"Module '{module_id}' not found"}), 404

        job_id = _create_job(target=target)
        job = _get_job(job_id)
        q = job["queue"]

        _session_log.set_target(target)
        if logger:
            logger.info(f"modules_run: job={job_id} module={module_id} target={target}")

        def _run():
            output_buf = []
            q.put(f"[*] Starting {module_id.upper()} module on {target}\n")
            try:
                module = module_class(config, logger)
                result = module.run(target)
                result_str = result.get("summary", str(result)) if isinstance(result, dict) else str(result) if result else ""
                output_buf.append(result_str)
                q.put(f"[+] Result: {result}\n")
                if logger:
                    logger.info(f"modules_run: job={job_id} module={module_id} completed")
            except Exception as e:
                if logger:
                    logger.exception(f"modules_run: job={job_id} module={module_id} failed: {e}")
                q.put(f"[!] Error: {e}\n")
            _session_log.record_output(module_id, f"module:{module_id}",
                                       "\n".join(output_buf), 0, source="module")
            q.put(None)
            job["done"] = True

        threading.Thread(target=_run, daemon=True).start()
        return jsonify({"job_id": job_id})

    @app.route("/terminal")
    def terminal():
        if _use_spa:
            return send_file(_spa_dist / "index.html")
        job_id = request.args.get("job", "")
        return render_template("terminal.html", job_id=job_id)

    @app.route("/stream/<job_id>")
    def stream(job_id):
        job = _get_job(job_id)
        if not job:
            if logger:
                logger.warning(f"stream: job not found job_id={job_id}")
            return Response("event: error\ndata: Job not found\n\n",
                            mimetype="text/event-stream")

        def _format_msg(msg):
            if msg is None:
                return "event: done\ndata: complete\n\n"
            if isinstance(msg, tuple) and msg[0] == "__progress__":
                return msg[1]
            escaped = (msg or "").replace("\n", "\\n")
            return f"data: {escaped}\n\n"

        def generate():
            q = job["queue"]
            # Replay buffered output (survives page refresh)
            buf = q.get_buffer_snapshot()
            for msg in buf:
                yield _format_msg(msg)
                if msg is None:
                    return
            # Drain queue duplicates (same items we just replayed)
            for _ in range(len(buf)):
                try:
                    q.get(timeout=0.1)
                except Empty:
                    break
            # Live stream
            while True:
                try:
                    msg = q.get(timeout=30)
                except Empty:
                    yield ": keepalive\n\n"
                    continue
                out = _format_msg(msg)
                yield out
                if msg is None:
                    break

        return Response(generate(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.route("/report/<job_id>")
    def report(job_id):
        fmt = request.args.get("format", "md")
        if fmt not in ("md", "html", "json"):
            return jsonify({"error": "Invalid format"}), 400
        job = _get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        rpt = job.get("report")
        if not rpt:
            if logger:
                logger.warning(f"report: no report data job_id={job_id}")
            return jsonify({"error": "No report data available (scan may still be running)"}), 404

        try:
            path = rpt.save(fmt=fmt)
            download_name = _safe_download_name(path)
            if fmt == "html":
                content = rpt.generate_html()
                return Response(content, mimetype="text/html",
                                headers={"Content-Disposition": f"attachment; filename={download_name}"})
            else:
                content = rpt.generate_markdown()
                return Response(content, mimetype="text/markdown",
                                headers={"Content-Disposition": f"attachment; filename={download_name}"})
        except Exception as e:
            if logger:
                logger.error(f"Report generation error: {e}")
            return jsonify({"error": "Report generation failed"}), 500

    @app.route("/findings/<job_id>")
    def findings(job_id):
        """Return parsed findings summary, next-step commands, and new hostnames."""
        from core.host_check import extract_hostnames_from_output, hostname_in_hosts, read_hosts_file

        job = _get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        rpt = job.get("report")
        if not rpt:
            return jsonify({"error": "Scan still running or no data collected"}), 404

        collected = job.get("collected_output", {})
        all_output = "\n".join(
            v["output"] if isinstance(v, dict) else v
            for v in collected.values()
        )
        new_hosts = extract_hostnames_from_output(all_output)
        hosts_map = read_hosts_file()
        unmapped = [h for h in new_hosts if not hostname_in_hosts(h, hosts_map)]

        return jsonify({
            "summary": rpt.get_findings_summary(),
            "next_steps": rpt.get_next_steps(),
            "target": job.get("target", ""),
            "new_hostnames": unmapped,
        })

    @app.route("/nextsteps/execute", methods=["POST"])
    def nextsteps_execute():
        """Run a single next-step command (user may have edited it). Validated against allowlist."""
        from utils.command_validation import validate_command_for_execution

        data = request.get_json(silent=True) or {}
        cmd = data.get("command", "").strip()
        if not cmd:
            return jsonify({"error": "No command provided"}), 400

        ok, err = validate_command_for_execution(cmd)
        if not ok:
            return jsonify({"error": err or "Command validation failed"}), 400

        job_id = _create_job(target=data.get("target", ""))
        job = _get_job(job_id)
        q = job["queue"]

        tool_name = cmd.split()[0] if cmd else "cmd"

        def _run():
            output_buf = []
            q.put(f"[*] === Executing next-step command ===\n")
            q.put(f"[*] $ {cmd}\n\n")
            done_event = threading.Event()
            exit_code = [None]

            def on_output(line, _buf=output_buf):
                _buf.append(line)
                q.put(line)

            def on_complete(code):
                exit_code[0] = code
                done_event.set()

            run_tool(cmd, on_output, on_complete)
            done_event.wait()
            _session_log.record_output(tool_name, cmd, "".join(output_buf),
                                       exit_code[0] or 0, source="next_step")
            q.put(f"\n[+] Command completed (exit {exit_code[0]})\n")
            q.put(None)
            job["done"] = True

        threading.Thread(target=_run, daemon=True).start()
        return jsonify({"job_id": job_id})

    @app.route("/session/findings")
    def session_findings():
        """Return cumulative findings + attack recommendations from ALL runs this session."""
        summary = _session_log.get_findings_summary()
        recs = _session_log.get_attack_recommendations()
        history = _session_log.get_run_history()
        return jsonify({
            "summary": summary,
            "findings_by_tool": _session_log.get_findings_by_tool(),
            "next_steps": recs,
            "history": history,
            "log_file": _session_log.get_log_path(),
            "target": _session_log.target,
        })

    @app.route("/session/report")
    def session_report():
        """Generate and download cumulative session report."""
        fmt = request.args.get("format", "md")
        report = _session_log.build_cumulative_report()
        try:
            path = report.save(fmt=fmt)
            if fmt == "html":
                content = report.generate_html()
                return Response(content, mimetype="text/html",
                                headers={"Content-Disposition": f"attachment; filename={path.split('/')[-1]}"})
            else:
                content = report.generate_markdown()
                return Response(content, mimetype="text/markdown",
                                headers={"Content-Disposition": f"attachment; filename={path.split('/')[-1]}"})
        except Exception as e:
            if logger:
                logger.error(f"Session report error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/about")
    def about():
        return render_template("settings.html")

    @app.route("/support")
    def support():
        if _use_spa:
            return send_file(_spa_dist / "index.html")
        return render_template("support.html")

    @app.route("/support/ticket", methods=["POST"])
    def support_ticket():
        """Save a local issue ticket to issues/ as markdown. OWASP-aligned input validation."""
        from utils.input_validation import validate_support_ticket, sanitize_for_filename, MAX_REQUEST_BODY_BYTES

        if request.content_length and request.content_length > MAX_REQUEST_BODY_BYTES:
            return jsonify({"error": f"Request body too large (max {MAX_REQUEST_BODY_BYTES} bytes)"}), 413

        payload = request.get_json(silent=True) or {}
        ok, err, validated = validate_support_ticket(payload)
        if not ok:
            return jsonify({"error": err or "Validation failed"}), 400

        title = validated["title"]
        ticket_type = validated["type"]
        component = validated["component"]
        target = validated["target"]
        steps = validated["steps"]
        expected = validated["expected"]
        actual = validated["actual"]

        issues_dir = Path("issues")
        issues_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ticket_id = f"PH-{ts}"
        safe_title = sanitize_for_filename(title, 60)
        out_path = issues_dir / f"{ticket_id}_{safe_title}.md"

        meta = {
            "ticket_id": ticket_id,
            "type": ticket_type,
            "component": component,
            "title": title,
            "target": target,
            "created_at": datetime.now().isoformat(),
            "user_agent": request.headers.get("User-Agent", ""),
        }

        body = [
            f"# {ticket_id}: {title}",
            "",
            "## Meta",
            "```json",
            json.dumps(meta, indent=2),
            "```",
            "",
            "## Steps to reproduce",
            steps or "_(not provided)_",
            "",
            "## Expected",
            expected or "_(not provided)_",
            "",
            "## Actual",
            actual or "_(not provided)_",
            "",
            "## Helpful context",
            f"- Session log: `{_session_log.get_log_path()}`",
            f"- Session target: `{_session_log.target or ''}`",
            "",
        ]

        try:
            out_path.write_text("\n".join(body), encoding="utf-8")
        except Exception as e:
            if logger:
                logger.error(f"Failed to write ticket: {e}")
            return jsonify({"error": "Failed to write ticket"}), 500

        return jsonify({"ticket_id": ticket_id, "path": str(out_path)})

    @app.route("/api/quote")
    def api_quote():
        q, movie = random.choice(MOVIE_QUOTES)
        return jsonify({"quote": q, "movie": movie})

    return app


def run_web(config, logger, host="0.0.0.0", port=8080):
    logger.info(f"Starting web UI on {host}:{port}")
    app = create_app(config, logger)
    app.run(host=host, port=port, debug=False, threaded=True)
