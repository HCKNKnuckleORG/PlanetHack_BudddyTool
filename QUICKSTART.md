# Quick Start Guide

## Choose Your Setup

| Mode | Local (venv) | Docker |
|------|--------------|--------|
| **Web** | `make run-web` / `./launch.sh` → 1 | `docker-compose up -d` → http://localhost:8080 |
| **GUI** | `make run-gui` / `./launch.sh` → 2 | Not supported |
| **CLI** | `make run-cli` / `./launch.sh` → 3 | `docker-compose exec planet-hack python main.py --cli` |

**Unified launcher:** Run `./launch.sh` for an interactive menu.

📖 Full options: [SETUP_OPTIONS.md](SETUP_OPTIONS.md)

---

## Step 0: Run Setup (Kali/Debian)

```bash
python main.py --setup
# Or: ./setup.sh
```

This checks for required tools (nmap, nikto, gobuster, whatweb, nuclei, sqlmap) and offers to install missing ones via apt. Use `--skip-tool-check` if running off-Kali.

---

## Option 1: Docker

```bash
# Build and run (Web UI on :8080)
docker-compose up -d

# Open http://localhost:8080 in browser

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Option 2: Local Installation

```bash
./launch.sh         # Unified menu
make run-web        # Web UI
make run-gui        # GUI
make run-cli        # CLI
```

## First Steps

1. **Launch the application**
   - GUI: `python main.py --gui`
   - CLI: `python main.py --cli`

2. **GUI flow (from end to start)**
   - You see: "What do you want to do?" on the **Home** tab
   - Click **Reconnaissance** → opens **Recon** tab
   - Enter target: IP (e.g. `10.10.10.5`) or domain/URL (e.g. `http://example.com`)
   - Pick preset: Full recon, CTF box, or Web app focus (for lab platforms like HTB, TryHackMe, PwnLab, VulnHub)
   - Click **Build Recon Plan** → shows phased tool plan
   - **Execute** (run in Terminal) or **Copy** each command; or **Run All Phases**
   - Or click **Browse all modules** for direct module access

3. **Target examples**
   - Lab boxes (HTB, TryHackMe, PwnLab, VulnHub): `10.10.10.50` or `machinename.htb`
   - Web app: `http://testphp.vulnweb.com` (authorized test site)

## Example Usage

### CLI Mode
```bash
# Interactive mode
python main.py --cli

# Direct module execution
python main.py --module recon --target https://example.com

# With custom log level
python main.py --module sql --target https://example.com --log-level DEBUG
```

### GUI Mode
1. Launch GUI: `python main.py --gui`
2. On **Home**: click **Reconnaissance** (or **Browse all modules**)
3. **Recon flow**: Enter target (IP or URL) → Build Recon Plan → Execute or Copy phases
4. **Modules tab**: Enter target in "Target" field → click a module button
5. View output in the **Terminal** tab

## Configuration

Edit `config/config.yaml` to customize:
- **tools.kali**: wordlist_dir, gobuster_wordlist (Kali default: `/usr/share/wordlists/...`)
- Module settings, tool paths (nmap, sqlmap, etc.)
- GUI theme colors, logging levels

## Environment Variables

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Set environment
export ENV=prod
```

## Troubleshooting

### Python not found
- Install Python 3.9+ from python.org
- Ensure Python is in your PATH

### Module import errors
- Run `pip install -r requirements.txt`
- Activate virtual environment if using one

### GUI not working
- Install tkinter: `sudo apt-get install python3-tk` (Linux)

### Recon tools not found (Kali)
- Run on Kali Linux for full support. Tools expected on PATH: nmap, nikto, gobuster, whatweb, nuclei
- Fallbacks: feroxbuster, dirb (for directory discovery)
- Wordlists: `config/config.yaml` → `tools.kali.gobuster_wordlist`

## Next Steps

- Read the full [README.md](README.md)
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to add modules
- Review module structure in `python/modules/`

---

**Remember: Only hack systems you own or have explicit permission to test!**

