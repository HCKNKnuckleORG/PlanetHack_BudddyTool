# Contributing to PlanetHack

Thank you for your interest in contributing to PlanetHack! 🌍

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch (`git checkout -b feature/amazing-feature`)
4. Make your changes
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Code Style

### Python
- Follow PEP 8
- Use type hints where possible
- Write docstrings for all functions and classes
- Run `black` and `flake8` before committing

## Adding New Modules

1. Create a new file in `python/modules/`
2. Inherit from `BaseModule`
3. Implement required methods
4. Add module to `config/config.yaml`
5. Update `python/gui/main.py` (welcome screen + modules tab)
6. Update documentation

**Recon-style guided workflows** use `core/recon_plan.py` and `core/tool_runner.py`.

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for good test coverage

## Documentation

- Update README.md if adding major features
- Add docstrings to new code
- Update module documentation
- Keep QUICKSTART.md in sync with GUI flow (validate end-to-end)

## Kali Tools

Recon invokes Kali tools (nmap, nikto, gobuster, whatweb, nuclei). Fallbacks: feroxbuster, dirb. Configure paths and wordlists in `config/config.yaml` → `tools.kali`.

## GitHub Repository Setup

To enable CI/CD Docker push, add these repository secrets (Settings → Secrets and variables → Actions):
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password or access token

## Questions?

Open an issue or reach out to maintainers!

---

**Remember: Only hack systems you own or have explicit permission to test!**

