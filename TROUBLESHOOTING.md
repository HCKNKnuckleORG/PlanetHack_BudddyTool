# PlanetHack Troubleshooting

## When Something Goes Wrong — Check This First

**Errors are automatically saved to:**

```
logs/planethack_errors.log
```

Check this file first whenever you see:
- Internal server errors (500)
- Crashes or unhandled exceptions
- Module run failures
- Recon phase failures
- Report generation errors

The errors log includes full tracebacks and is written immediately when any `ERROR` or `CRITICAL` occurs.

---

## Log Locations

| File | Contents |
|------|----------|
| `logs/planethack_errors.log` | **ERROR and CRITICAL only** — check this first when debugging |
| `logs/planethack_{env}_{date}.log` | Full daily log (INFO, DEBUG, etc.) — e.g. `planethack_dev_20240115.log` |
| `sessions/session_*.jsonl` | Recon/module tool output — per-session scan data |

---

## Common Issues

### Report History shows 500 or blank
- Check `logs/planethack_errors.log` for the traceback.
- Usually a parsing or missing-data bug (e.g. undefined variable in report logic).

### Module or Recon not running / results not saving
- Ensure the session target is set (run recon first, or enter target on Modules page).
- Check `logs/planethack_errors.log` for exceptions during module execution.
- Verify jobs are not being evicted: max 50 jobs; oldest are cleaned after 10 minutes idle.

### "Job not found" when viewing terminal or report
- Job may have expired (10 min idle) or been evicted (job limit).
- Check `logs/planethack_errors.log` for `stream: job not found` or similar.

### Port already in use
- Use `--port 8081` (or another port) when starting the web UI.
- Or let the app try the next available port in non-interactive mode.

---

## Verbose Logging

To capture more detail (DEBUG level):

```bash
python main.py --web --log-level DEBUG
```

Or set environment variable:
```bash
LOG_LEVEL=DEBUG python main.py --web
```

---

## Log Rotation

- **Errors log**: Rotates daily; retained 90 days; compressed after rotation.
- **Daily log**: Rotates at 10 MB; retained 30 days; compressed.
