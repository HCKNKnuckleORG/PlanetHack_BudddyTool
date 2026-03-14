# PlanetHack – Setup & Run Options

Choose how to run PlanetHack: **Web** or **GUI**, with **local Python venv** or **Docker**.

## Quick reference

| Mode  | Local (venv)       | Containerized (Docker)  |
|-------|--------------------|--------------------------|
| **Web** | `./launch.sh` → 1 / `make run-web` | `./launch.sh` → 4 / `docker-compose up -d` |
| **GUI** | `./launch.sh` → 2 / `make run-gui` | Not supported (needs display) |
| **CLI** | `./launch.sh` → 3 / `make run-cli` | `./launch.sh` → 5 / `docker-compose exec ... --cli` |

---

## Option 1: Unified launcher (recommended)

```bash
chmod +x launch.sh
./launch.sh
```

Shows a menu:
- 1 = Web UI (local venv)
- 2 = GUI (local venv)
- 3 = CLI (local venv)
- 4 = Web UI (Docker)
- 5 = CLI (Docker)
- 6 = Web + Ollama (Python)
- 7 = Web + Ollama (Docker)
- 8 = Setup (tool check)
- 9 = Exit

---

## Option 2: Direct launchers

### Local Python venv

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Then:
python main.py --web   # Web UI
python main.py --gui   # GUI
python main.py --cli   # CLI
```

Or use `make`:
```bash
make install
make run-web   # or run-gui, run-cli
```

### Docker

| Command                                   | Mode   | Access                   |
|-------------------------------------------|--------|--------------------------|
| `docker-compose up -d`                    | Web UI | http://localhost:8080    |
| `docker-compose exec planet-hack python main.py --cli` | CLI | Inside container |

---

## Option 3: Setup first

Run setup to check and optionally install required tools (e.g. on Kali):

```bash
./setup.sh

# Or
python main.py --setup
```

Use `--skip-tool-check` if you run off-Kali and don't need recon tools:
```bash
python main.py --web --skip-tool-check
```

---

## Summary

| Run method              | Web   | GUI | CLI |
|-------------------------|-------|-----|-----|
| `./launch.sh`           | ✅ 1, 4 | ✅ 2 | ✅ 3, 5 |
| `docker-compose up -d`  | ✅    |     |     |
| `docker-compose exec ... --cli` | |     | ✅  |
| `make run-web`          | ✅    |     |     |
| `make run-gui`          |       | ✅  |     |
| `make run-cli`          |       |     | ✅  |

**Note:** GUI in Docker would need X11/VNC and is not supported by default. Use Web UI or CLI in containers.
