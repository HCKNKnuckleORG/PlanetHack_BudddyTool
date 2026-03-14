# Project Structure

```
PlanetHack_BudddyTool/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline (GitHub Actions)
│
├── config/
│   └── config.yaml             # Main configuration file
│
├── python/
│   ├── __init__.py
│   ├── cli/                    # CLI interface
│   │   ├── __init__.py
│   │   └── main.py
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── logger.py          # Logging setup
│   │   ├── recon_plan.py      # Recon plan builder (phases, Kali tools)
│   │   └── tool_runner.py     # Execute tools via subprocess, stream output
│   ├── gui/                    # GUI (Home, Recon, Modules, Terminal, Settings)
│   │   ├── __init__.py
│   │   └── main.py
│   ├── modules/                # Security testing modules
│   │   ├── __init__.py
│   │   ├── base.py            # Base module class
│   │   ├── recon.py           # Reconnaissance (legacy; GUI uses recon_plan)
│   │   ├── sql.py             # SQL Injection
│   │   └── [other modules]    # XSS, Auth, etc.
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── helpers.py         # validate_url, is_ip_address, extract_domain
│
├── logs/                       # Application logs (created at runtime)
│
├── .dockerignore               # Docker ignore patterns
├── .gitignore                  # Git ignore patterns
├── CONTRIBUTING.md             # Contribution guidelines
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker build file
├── LICENSE                     # MIT License
├── Makefile                    # Make commands
├── main.py                     # Main entry point
├── QUICKSTART.md               # Quick start guide
├── README.md                   # Main documentation
├── requirements.txt            # Python dependencies
├── SECURITY.md                 # Security policy
├── launch.sh                  # Unified launcher (Web, GUI, CLI, Docker)
└── launch_web_with_ollama.sh  # Web + Ollama launcher
```

## Module Structure

Each module in `python/modules/` follows this pattern:

```python
from .base import BaseModule

class MyModule(BaseModule):
    def get_info(self):
        return {
            "name": "Module Name",
            "description": "Description",
            "version": "1.0.0"
        }
    
    def run(self, target: str, **kwargs):
        # Module implementation
        pass
```

## Recon Workflow (End → Start)

Flow traced backwards from execution:

1. **Execute/Copy** → `tool_runner.py` runs subprocess or copies to clipboard
2. **Plan display** → `recon_plan.py` `build_recon_plan()` generates phases (nmap, whatweb, nikto, gobuster, nuclei)
3. **Build Recon Plan** → GUI validates target, calls `build_recon_plan()`, reads `config.yaml` tools.kali
4. **Recon tab** → User enters target (IP or URL), selects preset (full/htb/web), clicks Build
5. **Welcome** → Home tab asks "What do you want to do?"; Reconnaissance opens Recon tab

## Adding New Modules

1. Create `python/modules/your_module.py`
2. Inherit from `BaseModule`
3. Implement `get_info()` and `run()` methods
4. Add module to `config/config.yaml`
5. Update GUI to include new module button (in `create_welcome_screen` and/or `create_modules_tab`)

For a guided workflow like Recon: add a plan builder in `core/` and wire it in `gui/main.py`.

## Environment Setup

- **Python**: 3.9+
- **Docker**: Optional, for containerized deployment

## Build/Dev/Prod Environments

- **dev**: Development environment (default)
- **build**: Build/CI environment
- **prod**: Production environment

Set via `--env` flag or `ENV` environment variable.

