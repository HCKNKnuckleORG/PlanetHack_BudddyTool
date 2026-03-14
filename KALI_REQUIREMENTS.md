# Kali Linux Requirements

PlanetHack is designed to run on **Kali Linux** (or Debian/Ubuntu). This document lists all required tools and Python dependencies.

## System Tools (apt packages)

Install via: `sudo apt install <package>`

Or run: `python main.py --setup` — the setup script will check and prompt to install missing tools.

| Tool | Package | Purpose |
|------|---------|---------|
| nmap | nmap | Port scanning |
| nikto | nikto | Web vulnerability scanner |
| gobuster | gobuster | Directory/file brute force |
| whatweb | whatweb | Web technology fingerprinting |
| nuclei | nuclei | Vulnerability template scanning |
| sqlmap | sqlmap | SQL injection testing |
| hydra | hydra | Password brute force |

### Fallbacks (optional)

| Tool | Package | Replaces |
|------|---------|----------|
| feroxbuster | feroxbuster | gobuster |
| dirb | dirb | gobuster |

## Python Dependencies

Install via: `pip install -r requirements.txt`

Core requirements are in `requirements.txt`. Key packages:
- Flask (web UI)
- requests, httpx, aiohttp (HTTP)
- beautifulsoup4, lxml (HTML parsing)
- selenium, playwright (browser automation)
- python-nmap, scapy (network)
- cryptography, pyjwt (security testing)
- pyyaml, python-dotenv (config)

## Wordlists (Kali default paths)

PlanetHack expects these paths on Kali:

- `/usr/share/wordlists/dirb/common.txt` — directory brute force
- `/usr/share/wordlists/rockyou.txt` — passwords (may need `gunzip`)
- `/usr/share/wordlists/metasploit/unix_users.txt` — usernames

Override in `config/config.yaml` under `tools.kali` if using different locations.

## Quick Setup on Kali

```bash
# 1. Clone the repo
git clone <repo-url>
cd PlanetHack_BudddyTool

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python deps
pip install -r requirements.txt

# 4. Check/install system tools
python main.py --setup

# 5. Copy config (optional)
cp config/config.example.yaml config/config.yaml

# 6. Run
./launch.sh   # or: python main.py --web
```
