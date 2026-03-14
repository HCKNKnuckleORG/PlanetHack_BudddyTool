# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please do **NOT** open a public issue.

**Report via GitHub Security Advisory:**
1. Go to the repository **Security** tab
2. Click **Report a vulnerability**
3. Fill out the form with details

Alternatively, open a private security advisory from the Security tab.

## Responsible Disclosure

We follow responsible disclosure practices. Please:

1. Do not disclose the vulnerability publicly until it has been addressed
2. Give us reasonable time to fix the issue
3. Provide detailed information about the vulnerability

## What We Don't Store or Expose

- **No API keys** in the repository — tool runs locally; optional WPScan token is user-provided
- **No credentials** — `config/config.yaml` and `.env` are gitignored
- **No scan data in repo** — `logs/`, `sessions/`, `reports/`, `issues/` are gitignored
- **Flask secret_key** — Generated per run; no static secret committed

## Security Best Practices

**IMPORTANT**: This tool is for authorized security testing only. Users are responsible for:

- Only testing systems they own or have explicit written permission to test
- Complying with all applicable laws and regulations
- Not using this tool for malicious purposes
- Keeping `.env`, `config/config.yaml`, and generated outputs out of version control

The maintainers are not responsible for misuse of this tool.

---

**Remember: Only hack systems you own or have explicit permission to test!**

