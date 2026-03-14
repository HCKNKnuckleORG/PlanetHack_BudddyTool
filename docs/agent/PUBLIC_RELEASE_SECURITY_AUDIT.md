# Public Release Security Audit

**Date:** March 14, 2025  
**Scope:** Full bottom-to-top security review for GitHub public release  
**Perspective:** Defensive — assume malicious actors will analyze the repo

---

## Executive Summary

| Category | Status | Notes |
|----------|--------|-------|
| Secrets & credentials | ✅ Pass | No hardcoded keys, tokens, or passwords |
| Identity/anonymity | ✅ Pass | Creator: HCKNKnuckle (GitHub); no local paths, emails, or personal data in tracked files |
| RCE prevention | ✅ Pass | Command allowlist, server-side recon rebuild |
| Input validation | ✅ Pass | Hosts injection, target validation, command validation |
| .gitignore coverage | ✅ Pass | Sensitive paths excluded |
| .dockerignore coverage | ✅ Pass | Hardened with config, sessions, reports |
| Documentation | ✅ Pass | SECURITY.md, .env.example present |

---

## 1. Secrets & Credentials

### ✅ Verified Clear

- **API keys, tokens, passwords:** None in source
- **Flask `secret_key`:** `uuid.uuid4().hex` per run — no static secret
- **PostgreSQL:** Uses `POSTGRES_PASSWORD` from `.env` (docker-compose requires it when using `with-db` profile)
- **Ollama:** URL only; no credentials
- **WPScan:** `YOUR_TOKEN` placeholder in report recommendations — user adds their own
- **CI/CD:** Uses `secrets.DOCKER_USERNAME` and `secrets.DOCKER_PASSWORD` — not hardcoded

### Files to Never Commit

| Path | Reason |
|------|--------|
| `.env` | POSTGRES_PASSWORD, other secrets |
| `config/config.yaml` | Local overrides, paths |
| `logs/`, `sessions/`, `reports/`, `issues/` | Target IPs, scan output |

---

## 2. Identity & Anonymity

### ✅ Verified Clear

- **Creator:** HCKNKnuckle (GitHub handle) — used consistently in README, LICENSE, About, report footer, settings, and templates
- **No personal data:** No real names, emails, or physical addresses in source
- **Local paths:** `venv/` gitignored; `pyvenv.cfg` and activate scripts contain `C:\Users\...` / `Z:\...` but are not committed
- **pre-publish-check.sh:** BAD_PATTERNS catches `C:\Users\...` and `/home/...` in tracked files
- **docs/agent/:** Internal audit docs; move to `notes/` and gitignore if not publishing

### Reminder

If cloning to a new path, delete and recreate `venv/` so no old paths leak into new environment files.

---

## 3. Remote Code Execution (RCE)

### ✅ Mitigations in Place

| Endpoint | Protection |
|----------|------------|
| `/recon/execute` | Plan rebuilt server-side from `target` + `preset`; ignores client `resolved_cmd` |
| `/nextsteps/execute` | `validate_command_for_execution()` before `run_tool()` |
| `/modules/run` | Same validation; only allowlisted tools (nmap, nikto, etc.) |
| Recon phases | Commands from `build_recon_plan()` + `resolve_tool_command()` — never from client |

### Command Allowlist

- **`command_validation.py`:** Only tools in `ALLOWED_TOOL_NAMES`; rejects shell metacharacters `;&|`$(){}!<>\\`
- **Max length:** 4096 chars
- **tool_check.py (apt install):** Uses `shell=True` but packages validated with `_PKG_RE`; user-initiated setup only

---

## 4. Input Validation

### ✅ Verified

- **`add_to_hosts_file()`:** IP via `is_ip_address()`, hostnames via `_HOSTNAME_RE`, rejects `\n\r;|` etc.
- **Target validation:** `_validate_target()` for recon/modules (URL, IP, domain)
- **Support tickets:** OWASP-aligned validation in `utils/input_validation.py`

---

## 5. .gitignore Coverage

| Path | Status |
|------|--------|
| `venv/`, `.env`, `config/config.yaml` | ✅ |
| `logs/`, `sessions/`, `reports/`, `issues/` | ✅ |
| `secrets/`, `*.key`, `*.pem`, `*.cert` | ✅ |
| `docs/agent/` | ✅ |
| `*.bat` | ⚠️ All .bat files ignored (note: Windows not primary platform) |

---

## 6. .dockerignore Coverage

| Path | Status |
|------|--------|
| `.git`, `venv/`, `.env` | ✅ |
| `config/config.yaml`, `sessions/`, `reports/`, `issues/` | ✅ Added |
| `*.md` except README | ✅ |
| `.github/` | ✅ |

Prevents sensitive local data from being copied into Docker build context.

---

## 7. Network & Binding

| Item | Current | Risk |
|------|---------|------|
| Web bind | `0.0.0.0:8080` | Anyone on network can access |
| CORS | `Access-Control-Allow-Origin: *` | Any origin can call API |
| Auth | None | By design for local pentest tool |

**Recommendation:** Document that users should:
- Run behind firewall/VPN when exposing remotely
- Consider `--host 127.0.0.1` for local-only binding if appropriate

---

## 8. Docker & CI

- **Dockerfile:** Copies `config/` (gets `config.example.yaml`); `config.yaml` excluded via .dockerignore
- **docker-compose:** `POSTGRES_PASSWORD` required from `.env` when using `with-db` profile
- **CI:** Lint, test, build-docker; deploy steps are placeholders
- **Build-docker:** Fails if `DOCKER_USERNAME`/`DOCKER_PASSWORD` secrets not set — acceptable

---

## 9. Pre-Release Checklist

Before pushing to GitHub:

1. Run `./scripts/pre-publish-check.sh` (or `scripts\pre-publish-check.bat` on Windows)
2. Verify `git status --ignored` — no sensitive files staged
3. Ensure `venv/` is not committed
4. Confirm no `config/config.yaml` in staging

---

## 10. References

- [SECURITY.md](../../SECURITY.md) — Vulnerability reporting
- [.env.example](../../.env.example) — Environment template

---

**Remember: Only hack systems you own or have explicit permission to test!**
