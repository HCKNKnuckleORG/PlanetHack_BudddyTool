# PlanetHack Update System

For staging/deployment on Ubuntu Server (e.g. bare metal i7 970).

## Version Scheme (SemVer)

| Part   | When to bump | Example     |
|--------|--------------|-------------|
| MAJOR  | Breaking changes | 1.0.0 → 2.0.0 |
| MINOR  | New features, backwards compatible | 1.0.0 → 1.1.0 |
| PATCH  | Bug fixes        | 1.0.0 → 1.0.1 |

**Source of truth:** `VERSION` file at project root. Config and package.json are synced when you bump.

## Version Commands

```bash
# Show current version
./scripts/version.sh

# Bump patch (1.0.0 → 1.0.1)
./scripts/version.sh bump patch

# Bump minor (1.0.0 → 1.1.0)
./scripts/version.sh bump minor

# Bump major (1.0.0 → 2.0.0)
./scripts/version.sh bump major

# Set exact version
./scripts/version.sh set 2.1.3

# Reset to dev/staging (clear version)
./scripts/version.sh reset
# → 0.0.0-dev
```

Use `reset` when you want a clean slate for dev/staging builds.

## Self-Update (Staging)

From the project root on your Ubuntu box:

```bash
# Pull latest, install deps, build frontend
./scripts/update.sh

# Same + restart systemd service
./scripts/update.sh --restart
```

The update script:
1. `git pull`
2. `pip install -r requirements.txt` (in venv if present)
3. `cd frontend && npm ci && npm run build`
4. (optional) `sudo systemctl restart planethack`

## Initial Staging Install

After a fresh Ubuntu Server install:

```bash
# From your dev machine, copy repo to the box, then:
cd /path/to/PlanetHack_BudddyTool
chmod +x scripts/*.sh
./scripts/install-staging.sh /opt/planethack

# Or clone from your repo (set PLANETHACK_REPO first):
PLANETHACK_REPO=https://github.com/HCKNKnuckle/PlanetHack_BudddyTool.git ./scripts/install-staging.sh /opt/planethack
```

Edit `config/config.yaml` and start the service:

```bash
sudo systemctl start planethack
```

## Hardware Notes (i7 970, 8GB, 1080TI)

- 8GB RAM: Keep Ollama disabled or use a small model (e.g. `llama3:7b`) if you enable AI
- 1080TI: Useful for Ollama GPU acceleration if you install NVIDIA drivers
- If you wiped Ubuntu and are reinstalling: skip NVIDIA drivers initially; get the app running first, then add drivers if needed for minikube/Ollama
