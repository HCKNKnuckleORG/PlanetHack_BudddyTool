# Pre-Publish Audit — Backward Validation

**Validated:** Full backward trace from data sinks to source.  
**Purpose:** Ensure no usage or testing data is published to GitHub.

---

## Data Flow (Backward)

### 1. Sinks (where usage data lands)

| Sink | Location | Status |
|------|----------|--------|
| Session logs | `sessions/*.jsonl` | ✅ **CLEARED** — all 15 files removed |
| Recon reports | `reports/*.md` | ✅ **CLEARED** — all 4 files removed |
| App logs | `logs/*.log` | ✅ **CLEARED** — all 8 files removed |
| Support tickets | `issues/` | ✅ Empty |
| Config overrides | `config/config.yaml` | ✅ No targets — gitignored |
| Jobs (in-memory) | `python/web/jobs.py` | ✅ Not persisted |
| Browser storage | `sessionStorage` (frontend) | ✅ Client-side only, not in repo |

### 2. .gitignore Coverage

| Path | Excluded | Notes |
|------|----------|-------|
| `logs/` | ✅ | Scan logs, errors |
| `sessions/` | ✅ | Target IPs, tool output |
| `reports/` | ✅ | Recon reports |
| `issues/` | ✅ | Support tickets |
| `config/config.yaml` | ✅ | Local overrides |
| `venv/` | ✅ | Contains local paths (Z:\, C:\Users\) |
| `.env` | ✅ | Secrets |
| `node_modules/` | ✅ | Dependencies |
| `frontend/dist/` | ✅ | Build output |

### 3. Source Code Scan

| Check | Result |
|-------|--------|
| Real IPs | ✅ Not in source — only generic examples in docs |
| Usage domains | ✅ Not found |
| Local paths | ✅ Only in venv/ (gitignored) |
| Session IDs, timestamps | ✅ None in committed files |

### 4. Documentation Examples

- `10.10.10.5`, `10.10.10.50` — generic lab example IPs ✅
- `example.com`, `target.example.com` — generic placeholders ✅
- `planethack_dev_20260223.log` — changed to `20240115` (generic) ✅

---

## Pre-Publish Script

Run before pushing:

```bash
./scripts/pre-publish-check.sh
```

Checks:
1. `logs/`, `sessions/`, `reports/`, `issues/` have no files (or are gitignored)
2. `config/config.yaml` is not staged
3. No known usage IPs/domains in tracked files
4. `venv/` is not staged

---

## Clean Before First Commit

If you haven’t initialized git yet:

1. **Ensure sensitive dirs are empty** (already done):
   - `logs/`, `sessions/`, `reports/` cleared

2. **Initialize and add:**
   ```bash
   git init
   git add .
   git status
   ```

3. **Verify** — you should NOT see:
   - config/config.yaml
   - logs/, sessions/, reports/, issues/
   - venv/, node_modules/, frontend/dist/

4. **Run:** `./scripts/pre-publish-check.sh`

---

## Summary

The application is sanitized and ready for GitHub. All usage data has been removed, .gitignore is correct, and the pre-publish script will catch any regressions.
