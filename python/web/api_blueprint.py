"""
PlanetHack REST API v1 - API-first endpoints for TypeScript/SPA consumption.
All routes return JSON. CORS enabled for frontend dev server.
"""

from flask import Blueprint, request, jsonify, Response
from core.recon_plan import build_recon_plan
from core.tool_runner import resolve_tool_command
from core.report import ReconReport
from core.host_check import run_preflight_check, add_to_hosts_file
from core.session import SessionLog
from core.module_readiness import evaluate_readiness
from core.module_commands import get_default_command
from modules import MODULE_REGISTRY
from utils.helpers import is_ip_address, validate_url

api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")


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


# ── Health & Meta ─────────────────────────────────────────────────────────────

@api_v1.route("/health", methods=["GET"])
def health():
    version = "1.0.0"
    try:
        from pathlib import Path
        vf = Path(__file__).resolve().parents[2] / "VERSION"
        if vf.exists():
            version = vf.read_text().strip() or version
        else:
            from flask import current_app
            cfg = current_app.config.get("PH_CONFIG")
            if cfg:
                version = (cfg.get("app", {}) or {}).get("version", version)
    except Exception:
        pass
    return jsonify({"status": "ok", "api": "v1", "version": version})


@api_v1.route("/quote", methods=["GET"])
def quote():
    import random
    quotes = [
        {"quote": "Hack the Planet!", "movie": "Hackers"},
        {"quote": "Mess with the best, die like the rest.", "movie": "Hackers"},
        {"quote": "Follow the white rabbit.", "movie": "The Matrix"},
        {"quote": "There is no spoon.", "movie": "The Matrix"},
    ]
    return jsonify(random.choice(quotes))


@api_v1.route("/modules/ready", methods=["GET"])
def modules_ready():
    """Return which modules are ready to run based on session recon findings."""
    from web.app import _session_log

    target = request.args.get("target", "").strip() or _session_log.target or ""
    findings = _session_log.get_findings_raw()
    ready, not_ready = evaluate_readiness(findings, target)
    return jsonify({
        "ready": ready,
        "not_ready": not_ready,
        "target": _session_log.target or "",
    })


@api_v1.route("/modules/<module_id>/command", methods=["GET"])
def module_default_command(module_id):
    """Return default shell command for a module + target (for payload editing)."""
    target = request.args.get("target", "").strip()
    if not target:
        return jsonify({"command": ""}), 200
    config = None
    try:
        from flask import current_app
        config = current_app.config.get("PH_CONFIG")
    except Exception:
        pass
    cmd = get_default_command(module_id, target, config)
    return jsonify({"command": cmd})


@api_v1.route("/modules", methods=["GET"])
def list_modules():
    modules = [
        {"id": m[1], "name": m[0], "color": m[2], "group": m[3] if len(m) > 3 else None}
        for m in [
            # OWASP Top 10 2025 - https://owasp.org/Top10/2025/
            ("A01 Access Control", "a01_access_control", "#ff0040", "owasp2025"),
            ("A02 Misconfiguration", "a02_misconfiguration", "#ff0040", "owasp2025"),
            ("A03 Supply Chain", "a03_supply_chain", "#ff0040", "owasp2025"),
            ("A04 Crypto Failures", "a04_crypto", "#ff0040", "owasp2025"),
            ("A05 Injection", "a05_injection", "#ff0040", "owasp2025"),
            ("A06 Insecure Design", "a06_insecure_design", "#ff0040", "owasp2025"),
            ("A07 Auth Failures", "a07_auth", "#ff0040", "owasp2025"),
            ("A08 Data Integrity", "a08_integrity", "#ff0040", "owasp2025"),
            ("A09 Logging", "a09_logging", "#ff0040", "owasp2025"),
            ("A10 Exceptional", "a10_exceptional", "#ff0040", "owasp2025"),
            # Recon & other modules
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
    ]
    return jsonify({"modules": modules})


# ── Recon ─────────────────────────────────────────────────────────────────────

@api_v1.route("/recon/preflight", methods=["POST"])
def recon_preflight():
    data = request.get_json(silent=True) or {}
    target = (data.get("target") or request.form.get("target", "")).strip()
    preset = data.get("preset") or request.form.get("preset", "full")
    if not target:
        return jsonify({"error": "No target provided"}), 400
    result = run_preflight_check(target, preset)
    return jsonify(result)


@api_v1.route("/recon/add-host", methods=["POST"])
def recon_add_host():
    data = request.get_json(silent=True) or {}
    ip = data.get("ip", "").strip()
    hostnames = data.get("hostnames", [])
    if not ip or not hostnames:
        return jsonify({"error": "IP and hostnames required"}), 400
    ok, msg = add_to_hosts_file(ip, hostnames)
    return jsonify({"success": ok, "message": msg})


@api_v1.route("/recon/plan", methods=["POST"])
def recon_plan():
    def _config():
        from flask import current_app
        return current_app.config.get("PH_CONFIG")

    data = request.get_json(silent=True) or {}
    target = (data.get("target") or request.form.get("target", "")).strip()
    preset = data.get("preset") or request.form.get("preset", "full")

    if not target or not _validate_target(target):
        return jsonify({"error": "Invalid target"}), 400

    config = _config()
    try:
        phases = build_recon_plan(target, config, preset=preset)
        for phase in phases:
            cmd = resolve_tool_command(phase)
            phase["resolved_cmd"] = phase.get("command", "(tool not found)") if not cmd else cmd
            phase["tool_available"] = cmd is not None
        return jsonify({"phases": phases, "target": target})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        try:
            from flask import current_app
            lg = current_app.config.get("PH_LOGGER")
            if lg:
                lg.exception(f"recon_plan failed: {e}")
        except Exception:
            pass
        return jsonify({"error": str(e)}), 500


@api_v1.route("/recon/execute", methods=["POST"])
def recon_execute():
    """Execute recon phases. Returns job_id for SSE stream. Plan rebuilt server-side (RCE prevention)."""
    from web.jobs import create_job, get_job
    from core.tool_runner import run_tool
    from core.session import SessionLog
    import threading
    import json as _json

    data = request.get_json(silent=True) or {}
    phases_data = data.get("phases", [])
    target = (data.get("target") or "").strip()
    preset = data.get("preset", "full")
    auto_continue = data.get("auto_continue", False)
    if not target or not _validate_target(target):
        return jsonify({"error": "Invalid target"}), 400
    if not phases_data:
        try:
            from flask import current_app
            lg = current_app.config.get("PH_LOGGER")
            if lg:
                lg.warning("recon_execute: no phases provided")
        except Exception:
            pass
        return jsonify({"error": "No phases provided"}), 400

    # Rebuild plan server-side: never trust client-sent resolved_cmd (RCE prevention)
    def _config():
        from flask import current_app
        return current_app.config.get("PH_CONFIG")
    try:
        phases_data = build_recon_plan(target, _config(), preset=preset)
        for phase in phases_data:
            cmd = resolve_tool_command(phase)
            phase["resolved_cmd"] = phase.get("command", "(tool not found)") if not cmd else cmd
            phase["tool_available"] = cmd is not None
    except (ValueError, Exception) as e:
        return jsonify({"error": str(e)}), 400

    from web.app import _session_log
    job_id = create_job(target=target)
    try:
        from flask import current_app
        lg = current_app.config.get("PH_LOGGER")
        if lg:
            lg.info(f"recon_execute: job={job_id} target={target} phases={len(phases_data)}")
    except Exception:
        pass
    job = get_job(job_id)
    q = job["queue"]
    total = len([p for p in phases_data if p.get("tool_available", False)])
    _session_log.set_target(target)

    def _run():
        collected = {}
        phase_idx = 0
        for phase in phases_data:
            cmd = phase.get("resolved_cmd")
            available = phase.get("tool_available", False)
            if not cmd or not available:
                q.put(f"[!] Phase {phase.get('phase', '?')}: {phase.get('tool', '?')} not found, skipping\n")
                continue

            tool_name = phase.get("tool", "unknown")
            phase_buf = []
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
            _session_log.record_output(tool_name, cmd, phase_output, exit_code[0] or 0, source="recon")
            q.put(f"\n[+] Phase {phase.get('phase', '?')} completed (exit {exit_code[0]})\n")

            if not auto_continue:
                confirm_data = _json.dumps({
                    "phase": phase.get("phase", "?"),
                    "tool": tool_name,
                    "purpose": phase.get("purpose", ""),
                    "exit_code": exit_code[0] or 0,
                    "findings": SessionLog.parse_phase_summary(tool_name, phase_output),
                    "phase_idx": phase_idx,
                    "total": total,
                })
                q.put(("__progress__", f"event: phase_confirm\ndata: {confirm_data}\n\n"))
                job["confirm_event"].clear()
                job["confirm_choice"] = True
                job["confirm_event"].wait(timeout=600)
                if not job["confirm_choice"]:
                    q.put(f"\n[!] === USER STOPPED AFTER PHASE {phase.get('phase', '?')} ===\n")
                    break

        job["collected_output"] = collected
        job["report"] = ReconReport(target)
        for tool, output in collected.items():
            job["report"].add_phase_output(tool, output)
        done_progress = f"event: progress\ndata: {total}|{total}|done|ALL PHASES COMPLETE\n\n"
        q.put(("__progress__", done_progress))
        q.put(None)
        job["done"] = True

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"job_id": job_id})


@api_v1.route("/recon/confirm/<job_id>", methods=["POST"])
def recon_confirm(job_id):
    from web.jobs import get_job
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    data = request.get_json(silent=True) or {}
    job["confirm_choice"] = data.get("continue", True)
    job["confirm_event"].set()
    return jsonify({"ok": True})


# ── Modules ───────────────────────────────────────────────────────────────────

@api_v1.route("/modules/run", methods=["POST"])
def modules_run():
    from web.jobs import create_job, get_job
    import threading

    data = request.get_json(silent=True) or {}
    module_id = data.get("module_id", "")
    target = data.get("target", "").strip()
    command = (data.get("command") or "").strip()

    if not target or not _validate_target(target):
        return jsonify({"error": "Invalid target"}), 400

    # When user provides a custom command, run it as shell (like nextsteps) instead of module
    if command and module_id != "recon":
        from core.tool_runner import run_tool
        from utils.command_validation import validate_command_for_execution

        ok, err = validate_command_for_execution(command)
        if not ok:
            return jsonify({"error": err or "Command validation failed"}), 400

        job_id = create_job(target=target)
        job = get_job(job_id)
        q = job["queue"]
        from web.app import _session_log
        _session_log.set_target(target)

        def _run_cmd():
            output_buf = []
            q.put(f"[*] Running custom command for {module_id}\n")
            q.put(f"[*] $ {command}\n\n")
            done_ev = threading.Event()
            exit_code = [None]

            def on_out(line, _b=output_buf):
                _b.append(line)
                q.put(line)

            def on_done(code):
                exit_code[0] = code
                done_ev.set()

            run_tool(command, on_out, on_done)
            done_ev.wait()
            tool_name = command.split()[0] if command else "cmd"
            _session_log.record_output(tool_name, command, "\n".join(output_buf), exit_code[0] or 0, source="module")
            q.put(f"\n[+] Command completed (exit {exit_code[0]})\n")
            q.put(None)
            job["done"] = True

        threading.Thread(target=_run_cmd, daemon=True).start()
        return jsonify({"job_id": job_id})

    if module_id == "recon":
        from web.jobs import create_job, get_job
        from core.tool_runner import run_tool
        import threading
        config = None
        from flask import current_app
        if current_app:
            config = current_app.config.get("PH_CONFIG")
        preset = data.get("preset", "htb")
        try:
            phases = build_recon_plan(target, config, preset=preset)
            for phase in phases:
                cmd = resolve_tool_command(phase)
                phase["resolved_cmd"] = phase.get("command", "(tool not found)") if not cmd else cmd
                phase["tool_available"] = cmd is not None
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        from web.app import _session_log
        job_id = create_job(target=target)
        job = get_job(job_id)
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
                batch: list = []
                BATCH_SIZE = 25  # reduce UI flood from heavy tools
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
                flush_batch()  # send any remaining
                phase_output = "".join(phase_buf)
                collected[tool_name] = {
                    "output": phase_output,
                    "cmd": cmd,
                    "exit_code": exit_code[0] or 0,
                }
                q.put(f"\n[+] Phase {phase.get('phase', '?')} completed (exit {exit_code[0]})\n")
            job["collected_output"] = collected
            from core.report import ReconReport
            rpt = ReconReport(target)
            for t, detail in collected.items():
                rpt.add_phase_output(t, detail["output"])
            job["report"] = rpt
            q.put(("__progress__", f"event: progress\ndata: {total_phases}|{total_phases}|done|ALL PHASES COMPLETE\n\n"))
            q.put(f"\n[*] All recon phases complete.\n")
            q.put(None)
            job["done"] = True

        threading.Thread(target=_run_recon, daemon=True).start()
        return jsonify({"job_id": job_id})

    module_class = MODULE_REGISTRY.get(module_id)
    if not module_class:
        return jsonify({"error": f"Module '{module_id}' not found"}), 404

    config = None
    logger = None
    from flask import current_app
    if current_app:
        config = current_app.config.get("PH_CONFIG")
        logger = current_app.config.get("PH_LOGGER")

    from web.app import _session_log
    job_id = create_job(target=target)
    job = get_job(job_id)
    q = job["queue"]
    _session_log.set_target(target)

    def _run():
        output_buf = []
        q.put(f"[*] Starting {module_id.upper()} module on {target}\n")
        try:
            module = module_class(config, logger)
            result = module.run(target)
            result_str = result.get("summary", str(result)) if isinstance(result, dict) else str(result) if result else ""
            output_buf.append(result_str)
            q.put(f"[+] Result: {result}\n")
        except Exception as e:
            try:
                from flask import current_app
                lg = current_app.config.get("PH_LOGGER")
                if lg:
                    lg.exception(f"module {module_id} failed: {e}")
            except Exception:
                pass
            q.put(f"[!] Error: {e}\n")
        _session_log.record_output(module_id, f"module:{module_id}", "\n".join(output_buf), 0, source="module")
        q.put(None)
        job["done"] = True

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"job_id": job_id})


# ── Terminal / Stream ─────────────────────────────────────────────────────────

@api_v1.route("/stream/<job_id>")
def stream(job_id):
    from web.jobs import get_job
    from queue import Empty

    job = get_job(job_id)
    if not job:
        try:
            from flask import current_app
            lg = current_app.config.get("PH_LOGGER")
            if lg:
                lg.warning(f"stream: job not found job_id={job_id}")
        except Exception:
            pass
        return Response("event: error\ndata: Job not found\n\n", mimetype="text/event-stream")

    def _format_msg(msg):
        if msg is None:
            return "event: done\ndata: complete\n\n"
        if isinstance(msg, tuple) and msg[0] == "__progress__":
            return msg[1]
        escaped = (msg or "").replace("\n", "\\n")
        return f"data: {escaped}\n\n"

    def generate():
        q = job["queue"]
        buf = q.get_buffer_snapshot()
        for msg in buf:
            yield _format_msg(msg)
            if msg is None:
                return
        for _ in range(len(buf)):
            try:
                q.get(timeout=0.1)
            except Empty:
                break
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

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Report & Findings ─────────────────────────────────────────────────────────

@api_v1.route("/report/<job_id>")
def report(job_id):
    from web.jobs import get_job
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    rpt = job.get("report")
    if not rpt:
        return jsonify({"error": "No report data available"}), 404
    fmt = request.args.get("format", "md")
    try:
        path = rpt.save(fmt=fmt)
        if fmt == "html":
            content = rpt.generate_html()
            return Response(content, mimetype="text/html", headers={"Content-Disposition": f"attachment; filename={path.split('/')[-1]}"})
        else:
            content = rpt.generate_markdown()
            return Response(content, mimetype="text/markdown", headers={"Content-Disposition": f"attachment; filename={path.split('/')[-1]}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.route("/findings/<job_id>")
def findings(job_id):
    from web.jobs import get_job
    from core.host_check import extract_hostnames_from_output, hostname_in_hosts, read_hosts_file

    job = get_job(job_id)
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


@api_v1.route("/jobs/<job_id>/confirm-report", methods=["POST"])
def job_confirm_report(job_id):
    """Add completed job's results to session (Report History). Called when user confirms."""
    from web.jobs import get_job
    from web.app import _session_log

    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if not job.get("done"):
        return jsonify({"error": "Job not complete"}), 400
    collected = job.get("collected_output", {})
    if not collected:
        return jsonify({"error": "No output to add"}), 400

    target = job.get("target", "")
    _session_log.set_target(target)
    for tool_name, detail in collected.items():
        if isinstance(detail, dict):
            _session_log.record_output(
                tool_name,
                detail.get("cmd", f"tool:{tool_name}"),
                detail.get("output", ""),
                detail.get("exit_code", 0),
                source="recon",
            )
        else:
            _session_log.record_output(tool_name, f"tool:{tool_name}", str(detail), 0, source="recon")

    job["report_confirmed"] = True
    return jsonify({"ok": True, "target": target})


# ── Session ───────────────────────────────────────────────────────────────────

@api_v1.route("/session/findings")
def session_findings():
    from web.app import _session_log
    return jsonify({
        "summary": _session_log.get_findings_summary(),
        "findings_by_tool": _session_log.get_findings_by_tool(),
        "next_steps": _session_log.get_attack_recommendations(),
        "history": _session_log.get_run_history(),
        "log_file": _session_log.get_log_path(),
        "target": _session_log.target,
    })


@api_v1.route("/session/report")
def session_report():
    from web.app import _session_log
    fmt = request.args.get("format", "md")
    report = _session_log.build_cumulative_report()
    try:
        path = report.save(fmt=fmt)
        if fmt == "html":
            content = report.generate_html()
            return Response(content, mimetype="text/html", headers={"Content-Disposition": f"attachment; filename={path.split('/')[-1]}"})
        else:
            content = report.generate_markdown()
            return Response(content, mimetype="text/markdown", headers={"Content-Disposition": f"attachment; filename={path.split('/')[-1]}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Next Steps ─────────────────────────────────────────────────────────────────

@api_v1.route("/nextsteps/execute", methods=["POST"])
def nextsteps_execute():
    from web.jobs import create_job, get_job
    from core.tool_runner import run_tool
    from core.session import SessionLog
    from utils.command_validation import validate_command_for_execution
    import threading

    data = request.get_json(silent=True) or {}
    cmd = data.get("command", "").strip()
    if not cmd:
        return jsonify({"error": "No command provided"}), 400

    ok, err = validate_command_for_execution(cmd)
    if not ok:
        return jsonify({"error": err or "Command validation failed"}), 400

    from web.app import _session_log
    job_id = create_job(target=data.get("target", ""))
    job = get_job(job_id)
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
        _session_log.record_output(tool_name, cmd, "".join(output_buf), exit_code[0] or 0, source="next_step")
        q.put(f"\n[+] Command completed (exit {exit_code[0]})\n")
        q.put(None)
        job["done"] = True

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"job_id": job_id})


# ── AI (Ollama) ───────────────────────────────────────────────────────────────

@api_v1.route("/ai/improve-payload", methods=["POST"])
def ai_improve_payload():
    """Use Ollama to improve a security testing payload/command."""
    from core.ollama_client import improve_payload

    data = request.get_json(silent=True) or {}
    payload = (data.get("payload") or "").strip()
    module_id = (data.get("module_id") or "").strip()
    if not payload:
        return jsonify({"error": "No payload provided"}), 400
    ok, result = improve_payload(payload, module_context=module_id)
    if not ok:
        return jsonify({"error": result, "improved": None}), 503
    return jsonify({"improved": result})


@api_v1.route("/ai/analyze-response", methods=["POST"])
def ai_analyze_response():
    """Use Ollama to analyze command output for security findings."""
    from core.ollama_client import analyze_response

    data = request.get_json(silent=True) or {}
    command = (data.get("command") or "").strip()
    output = (data.get("output") or "").strip()
    if not output:
        return jsonify({"error": "No output provided"}), 400
    ok, result = analyze_response(command, output)
    if not ok:
        return jsonify({"error": result, "analysis": None}), 503
    return jsonify({"analysis": result})


# ── Support / Tickets ────────────────────────────────────────────────────────

@api_v1.route("/support/ticket", methods=["POST"])
def support_ticket():
    """Save a local issue ticket to issues/ as markdown (API-first). OWASP-aligned validation."""
    import json
    from datetime import datetime
    from pathlib import Path
    from flask import current_app
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

    from web.app import _session_log

    issues_dir = Path("issues")
    issues_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ticket_id = f"PH-{ts}"
    safe_title = sanitize_for_filename(title, 60)
    out_path = issues_dir / f"{ticket_id}_{safe_title}.md"

    cfg = None
    try:
        cfg = current_app.config.get("PH_CONFIG")
    except Exception:
        cfg = None

    app_version = None
    try:
        app_version = getattr(cfg, "get", lambda *_: None)("app.version") if cfg else None
    except Exception:
        app_version = None

    meta = {
        "ticket_id": ticket_id,
        "type": ticket_type,
        "component": component,
        "title": title,
        "target": target,
        "created_at": datetime.now().isoformat(),
        "user_agent": request.headers.get("User-Agent", ""),
        "app_version": app_version,
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
        return jsonify({"error": f"Failed to write ticket: {e}"}), 500

    return jsonify({"ticket_id": ticket_id, "path": str(out_path)})
