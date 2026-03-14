# Security Audit Report — Pre-GitHub Release

**Date:** March 14, 2025  
**Application:** PlanetHack CTF & Bug Bounty Tool  
**Scope:** Full codebase scan for secrets, vulnerabilities, and Kali deployment readiness

---

## Executive Summary

This audit was performed to validate the application before uploading to GitHub. **Critical RCE vulnerabilities were identified and fixed.** The application now has improved security controls for command execution, input validation, and configuration.

---

## 1. Secrets & Credentials Scan

### ✅ No Hardcoded Secrets

- **API keys, passwords, tokens:** None found in source code
- **Flask `secret_key`:** Generated per-run via `uuid.uuid4().hex` (no static secret)
- **Ollama URL:** Configurable, default `http://localhost:11434` (no credentials)
- **Docker:** Uses `POSTGRES_PASSWORD` from `.env` (never commit `.env`)

### ✅ .gitignore Coverage

Sensitive paths are correctly excluded:

| Path | Reason |
|------|--------|
| `.env`, `.env.local`, `.env.*.local` | Environment secrets |
| `config/config.yaml`, `config/local.yaml` | Local overrides |
| `logs/`, `sessions/`, `reports/`, `issues/` | Scan data, target IPs |
| `secrets/`, `*.key`, `*.pem`, `*.cert`, `*.p12` | Certificates, keys |

### ⚠️ Pre-Release Verification

Run before pushing:

```bash
git diff --cached | grep -iE 'api[_-]?key|password|secret|token|credential'
# Should return nothing
```

---

## 2. Vulnerabilities Identified & Fixed

### 🔴 CRITICAL: Arbitrary Command Execution (RCE)

**Before:** Multiple endpoints accepted user-supplied commands and executed them via `subprocess` with `shell=True`:

- `/nextsteps/execute` — arbitrary `command` from client
- `/api/v1/nextsteps/execute` — same
- `/api/v1/modules/run` with `command` param — custom command execution
- `/recon/execute` — client could send modified `resolved_cmd` in phases

**Impact:** Unauthenticated RCE when web UI is exposed (default `0.0.0.0:8080`).

**Fix applied:**

1. **Command allowlist** (`python/utils/command_validation.py`): Only commands starting with known security tools (nmap, nikto, gobuster, etc.) are allowed. Shell metacharacters rejected.
2. **Recon plan rebuilt server-side:** `/recon/execute` now rebuilds the plan from `target` + `preset` and ignores client-sent `resolved_cmd`.
3. **Validation on nextsteps/modules:** `validate_command_for_execution()` applied before any `run_tool()` call from web/API.

### 🟠 HIGH: /etc/hosts Injection

**Before:** `add_to_hosts_file(ip, hostnames)` concatenated user input into a line passed to `tee -a /etc/hosts`. Hostnames with newlines could inject arbitrary lines.

**Fix:** Input validation in `host_check.py`:
- IP validated via `is_ip_address()`
- Hostnames validated: no `\n`, `\r`, `;`, `|`, etc.
- Hostname format: `_HOSTNAME_RE` allows valid DNS-style names

### 🟡 MEDIUM: CORS Allow-All

**Current:** `Access-Control-Allow-Origin: *` in `web/app.py`.

**Recommendation:** For production deployments, restrict to specific origins. The tool is designed for local/Docker use; if exposed, consider adding auth or binding to `127.0.0.1` only.

### 🟡 MEDIUM: No Authentication

The web UI has no login. Anyone with network access can use it. **By design** for a local pentesting tool. Document that users should:

- Run behind firewall/VPN when remote
- Use `--host 127.0.0.1` for local-only binding when appropriate

---

## 3. Additional Security Controls

### Input Validation

- **Support tickets:** OWASP-aligned validation in `utils/input_validation.py` (XSS, path traversal, length limits)
- **Target validation:** `_validate_target()` for recon/module targets (URL, IP, domain)

### Safe Subprocess Usage

- **tool_runner.py:** Uses `shell=True` for tool invocation; commands are now validated before reaching it
- **host_check.py:** `add_to_hosts_file` uses `subprocess.run(["sudo", "tee", "-a", "/etc/hosts"], input=line)` — no shell metacharacter expansion

---

## 4. Kali Linux Readiness

### ✅ Requirements Documented

- **KALI_REQUIREMENTS.md** created with:
  - System tools (nmap, nikto, gobuster, whatweb, nuclei, sqlmap, hydra)
  - Python deps (`requirements.txt`)
  - Wordlist paths
  - Quick setup instructions

### ✅ config.example.yaml Updated

- `tools_required` uncommented so `python main.py --setup` works after copying config
- Includes all Kali tools: nmap, nikto, gobuster, whatweb, nuclei, feroxbuster, dirb, sqlmap, hydra

### Setup Script

- `setup.sh` invokes `python main.py --setup`
- `tool_check.py` validates package names before apt install (regex `^[a-zA-Z0-9][a-zA-Z0-9.+\-]+$`)

---

## 5. Files Never to Commit

| Path | Reason |
|------|--------|
| `.env` | Env secrets |
| `config/config.yaml` | Local paths, overrides |
| `logs/`, `sessions/`, `reports/`, `issues/` | Target IPs, scan output |
| `*.key`, `*.pem`, `*.cert` | Certificates |

---

## 6. Checklist Before GitHub Push

- [x] No API keys, tokens, or credentials in source
- [x] `.gitignore` covers sensitive paths
- [x] RCE vectors mitigated (command allowlist, server-side recon rebuild)
- [x] Host injection in add_to_hosts_file fixed
- [x] config.example.yaml includes tools_required
- [x] KALI_REQUIREMENTS.md created
- [ ] Run `python main.py --setup` on Kali to verify tool install
- [ ] Run `git status --ignored` to confirm no sensitive files staged

---

## 7. References

- [SECURITY.md](SECURITY.md) — Vulnerability reporting
- [PUBLIC_RELEASE_CHECKLIST.md](PUBLIC_RELEASE_CHECKLIST.md) — Pre-release checklist
- [KALI_REQUIREMENTS.md](KALI_REQUIREMENTS.md) — Kali setup

---

**Remember: Only hack systems you own or have explicit permission to test!**
