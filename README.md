# 🌍 PlanetHack - CTF & Bug Bounty Tool

> **Hack the Planet!** 🚀

Created by **HCKNKnuckle**

A comprehensive CTF and bug bounty hunting tool inspired by the classic "Hackers" movie aesthetic. Built for CTFs, practice boxes, and lab environments—such as those on **Hack The Box**, **TryHackMe**, **PwnLab**, and **VulnHub**—as well as authorized bug bounty testing.

**Platform:** Linux (Ubuntu, Kali, Debian). Docker runs on any Linux host.

## 🎯 Features

- **Guided Recon Workflow** - Start with "What do you want to do?"; enter target (IP or domain); build phased tool plan; execute or copy commands
- **80s Retro GUI** - Cyberpunk aesthetic with neon colors and terminal vibes
- **Kali Linux Ready** - Designed for Kali with nmap, nikto, gobuster, whatweb, nuclei (fallbacks: feroxbuster, dirb)
- **Modular Architecture** - Each Bug Bounty Bootcamp chapter has its own module
- **Multi-Language** - Python (API/engine), TypeScript (SPA frontend)
- **Docker Ready** - Run everything in containers
- **CI/CD Pipeline** - Automated builds and deployments
- **Comprehensive Logging** - Track all activities with structured logging

## 📚 Modules (Bug Bounty Bootcamp)

Each chapter maps to a module. Guide: *Bug Bounty Bootcamp* by Vickie Li.

| Ch | Module | Description |
|----|--------|-------------|
| 5 | **Reconnaissance** | nmap, whatweb, nikto, gobuster, nuclei. Presets: Full, CTF, Web |
| 6 | **XSS** | Reflected, stored, DOM-based XSS |
| 7 | **Open Redirect** | Open redirect vulnerability testing |
| 8 | **Clickjacking** | UI redressing, clickjacking |
| 9 | **CSRF** | Cross-Site Request Forgery |
| 10,17 | **Access Control** | IDOR, privilege escalation, logic errors |
| 11 | **SQL Injection** | Detection, exploitation, payloads |
| 12 | **Business Logic** | Race conditions, workflow manipulation |
| 13 | **SSRF** | Server-Side Request Forgery |
| 14 | **Deserialization** | Insecure deserialization |
| 15 | **XXE** | XML External Entity |
| 16 | **Template Injection** | SSTI testing |
| 18 | **RCE** | Remote Code Execution |
| 20 | **Authentication** | Session, JWT, OAuth, SSO |
| 21 | **Information Disclosure** | Sensitive data exposure |
| 24 | **API Security** | REST/GraphQL, rate limiting |
| 25 | **Fuzzing** | Automatic vuln discovery |
| — | **Brute Force** | Password/credential attacks (Hydra) — SSH, HTTP forms, FTP, MySQL, RDP, SMB |

Also: File Upload, Session Management, Request Smuggling, Web Cache

## Update System (Staging)

For self-updating on Ubuntu Server staging:

- **Version:** `VERSION` file (SemVer). Bump with `./scripts/version.sh bump patch|minor|major`
- **Reset:** `./scripts/version.sh reset` → 0.0.0-dev
- **Update:** `./scripts/update.sh` (git pull + deps + build) or `./scripts/update.sh --restart`

## First-Time Setup

1. **Clone or download** this repository
2. **Run setup** (recommended on Kali): `python main.py --setup` or `./setup.sh`
   - Checks for required tools (nmap, nikto, gobuster, whatweb, nuclei, etc.)
   - Prompts to install missing tools via apt (Kali/Debian only)
3. **Config**: Copy `config/config.example.yaml` to `config/config.yaml` to customize (optional)
4. **No API keys** required; the tool runs locally

## 🚀 Quick Start

### Unified launcher (easiest)

```bash
chmod +x launch.sh && ./launch.sh
```

Choose from the menu: Web, GUI, or CLI — local venv or Docker.

📖 **See [SETUP_OPTIONS.md](SETUP_OPTIONS.md) for the full options matrix**

### Run options at a glance

| Mode | Local (venv) | Docker |
|------|--------------|--------|
| **Web** | `./launch.sh` → 1 / `make run-web` | `docker-compose up -d` → http://localhost:8080 |
| **GUI** | `./launch.sh` → 2 / `make run-gui` | *(not supported)* |
| **CLI** | `./launch.sh` → 3 / `make run-cli` | `docker-compose exec planet-hack python main.py --cli` |

### Docker (Web UI)

```bash
docker-compose up -d
# Browse to http://localhost:8080
```

📖 **See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for detailed Docker instructions**

### TypeScript/React UI (default)

The Web UI uses the **React SPA** when built. Build once, then start:

```bash
# 1. Build the React frontend and legacy scripts (one time, or after pulling changes)
cd frontend && npm install && npm run build
cd ..

# 2. Start the server
python main.py --web
# Browse to http://localhost:8080 — React UI
```

If `frontend/dist` does not exist, Flask falls back to the legacy Jinja2 UI. The build step also compiles legacy scripts (`app.js`, `terminal.js`, `matrix-rain.js`) from TypeScript to `python/web/static/js/`.

### Development mode (Vite dev server)

For hot-reload during frontend development:

```bash
# Terminal 1: Flask API
python main.py --web

# Terminal 2: Vite dev server
cd frontend && npm run dev
# Browse to http://localhost:5173 — React dev UI with live reload
```

**Kali**: The recon workflow invokes nmap, nikto, gobuster, whatweb, nuclei. Wordlists: `config/config.yaml` → `tools.kali`.

## 🏗️ Project Structure

```
PlanetHack_BudddyTool/
├── python/              # Python (API engine, modules)
│   ├── gui/            # Tkinter GUI (legacy)
│   ├── web/            # Flask API + legacy Jinja2 UI
│   │   ├── api_blueprint.py   # REST API v1 (/api/v1/*)
│   │   ├── jobs.py            # Job store for async runs
│   │   ├── static/            # CSS, JS (cyber theme)
│   │   └── templates/         # Jinja2 HTML (legacy)
│   ├── core/           # config, recon_plan, tool_runner
│   ├── modules/        # Bug bounty modules
│   └── utils/          # helpers
├── frontend/           # TypeScript SPA (Vite + React)
│   └── src/            # Pages, API client, styles
├── config/             # config.yaml
└── logs/               # Application logs (planethack_errors.log = errors only, check first)
```

## 🎨 Theme

Inspired by **Hackers (1995)**, **Swordfish (2001)**, and **The Matrix (1999)**:
- Matrix digital rain animation (Canvas / Tkinter)
- Neon green, cyan, magenta on black
- CRT scanline overlay
- Rotating movie quotes from all three films
- ASCII art banner
- Custom neon-glow buttons

## 🔧 Troubleshooting

When something goes wrong, **check `logs/planethack_errors.log` first** — errors are automatically saved there with full tracebacks.

📖 See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for log locations, common issues, and verbose logging.

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 👤 Author

**HCKNKnuckle**

## Security & Legal

**This tool is for authorized security testing only.**

- **No secrets in repo** — No API keys, credentials, or personal data are committed. See [SECURITY.md](SECURITY.md).
- **Authorized use only** — Only test systems you own or have explicit written permission to test
- **No warranty** — Use at your own risk; maintainers are not responsible for misuse
- **Data handling** — Scan results, logs, and reports stay local. Never commit `config/config.yaml`, `.env`, `logs/`, `sessions/`, or `reports/` to version control

**Remember: Only hack systems you own or have explicit permission to test!**

