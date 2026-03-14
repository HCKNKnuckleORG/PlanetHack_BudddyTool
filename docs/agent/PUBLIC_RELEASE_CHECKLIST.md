# Pre-Public Release Checklist

Before publishing this repository to GitHub as a **public** repo, verify:

## Sensitive Data

- [ ] **No API keys, tokens, or credentials** in source code or config
- [ ] **config/config.yaml** is gitignored (contains local paths; copy from config.example.yaml)
- [ ] **.env** is gitignored; use .env.example as template
- [ ] **logs/**, **sessions/**, **reports/**, **issues/** are gitignored (contain target IPs, scan output)
- [ ] No real target IPs or domains in committed files (only examples like `example.com`, `10.10.10.5`)

## Files Never to Commit

| Path | Reason |
|------|--------|
| `.env` | Environment secrets |
| `config/config.yaml` | Local overrides, paths |
| `logs/` | Scan logs, errors |
| `sessions/` | Target IPs, tool output |
| `reports/` | Target IPs, scan reports |
| `issues/` | Support tickets |
| `venv/` | Local paths, Python env |
| `*.key`, `*.pem`, `*.cert` | Certificates, private keys |

## Verification Commands

```bash
# Run pre-publish check (recommended)
./scripts/pre-publish-check.sh

# Ensure no secrets in staged files
git diff --cached | grep -iE 'api[_-]?key|password|secret|token|credential'

# Check .gitignore coverage
git status --ignored
```

## Security Notes

- **CORS**: App allows `*` for dev; consider restricting in production
- **Flask secret_key**: Generated per-run (`uuid.uuid4().hex`) — no static secret in repo
- **PostgreSQL**: Docker compose uses `POSTGRES_PASSWORD` from `.env` — never commit `.env`
- **WPScan**: Report suggests `YOUR_TOKEN` placeholder — users add their own API token

