"""
Tool Check - Verify required tools are installed, offer to install via apt on Kali/Debian
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


def is_kali_or_debian() -> bool:
    """Check if running on Kali Linux or Debian-based system with apt."""
    try:
        os_release = Path("/etc/os-release")
        if not os_release.exists():
            return False
        content = os_release.read_text().lower()
        return "kali" in content or "debian" in content or "ubuntu" in content
    except Exception:
        return False


def check_tool_available(tool_name: str, tool_path: Optional[str] = None) -> bool:
    """Check if a tool binary is available on PATH."""
    if tool_path:
        return Path(tool_path).exists() or shutil.which(tool_path) is not None
    return shutil.which(tool_name) is not None


def get_tools_from_config(config: Any) -> Dict[str, Dict[str, Any]]:
    """
    Load tool requirements from config.setup.tools_required.
    Returns dict of binary_name -> {package, category, description, ...}
    """
    raw = getattr(config, "config", config) if config else {}
    setup = raw.get("setup", {})
    tools = setup.get("tools_required", {})
    if isinstance(tools, dict):
        return tools
    return {}


def check_tools(config: Any) -> Tuple[List[str], List[Dict]]:
    """
    Check which required tools are installed and which are missing.
    
    Returns:
        (installed_binaries, missing_entries)
        missing_entries: list of {binary, package, description, ...}
    """
    tools_cfg = get_tools_from_config(config)
    if not tools_cfg:
        return [], []

    installed = []
    missing = []

    for binary, info in tools_cfg.items():
        pkg = info.get("package", binary) if isinstance(info, dict) else binary
        desc = info.get("description", "") if isinstance(info, dict) else ""
        if check_tool_available(binary):
            installed.append(binary)
        else:
            missing.append({
                "binary": binary,
                "package": pkg,
                "description": desc,
                **({"fallback_for": info["fallback_for"]} if isinstance(info, dict) and info.get("fallback_for") else {}),
            })

    return installed, missing


def install_tools_via_apt(
    packages: List[str],
    logger=None,
) -> bool:
    """
    Install packages via apt. Requires sudo. Only on Kali/Debian.
    
    Returns:
        True if install succeeded, False otherwise
    """
    if not packages:
        return True

    if not is_kali_or_debian():
        if logger:
            logger.warning("Not on Kali/Debian - cannot auto-install. Install manually: " + ", ".join(packages))
        return False

    import re
    _PKG_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9.+\-]+$')
    for pkg in packages:
        if not _PKG_RE.match(pkg):
            if logger:
                logger.error(f"Invalid package name rejected: {pkg!r}")
            return False

    cmd = f"sudo apt-get update -qq && sudo apt-get install -y {' '.join(packages)}"
    if logger:
        logger.info(f"Installing: {', '.join(packages)}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            if logger:
                logger.error(f"Install failed: {result.stderr or result.stdout}")
            return False
        return True
    except subprocess.TimeoutExpired:
        if logger:
            logger.error("Install timed out")
        return False
    except Exception as e:
        if logger:
            logger.error(f"Install error: {e}")
        return False


def run_setup_check(
    config: Any,
    logger,
    ask_callback=None,
    install_callback=None,
) -> bool:
    """
    Run tool check. If missing tools, optionally prompt and install.
    
    Args:
        config: Config object
        logger: Logger
        ask_callback: func(missing: List[dict]) -> bool. Return True to install.
        install_callback: func(msg: str) -> None. Progress callback.
    
    Returns:
        True to continue (all OK or user skipped), False on critical failure
    """
    installed, missing = check_tools(config)

    if not missing:
        logger.info("All required tools are installed.")
        return True

    missing_binaries = [m["binary"] for m in missing]
    packages = list({m["package"] for m in missing})

    logger.warning(f"Missing tools: {', '.join(missing_binaries)}")

    if ask_callback and not ask_callback(missing):
        logger.info("User chose not to install. Some features may be limited.")
        return True

    if install_callback:
        install_callback(f"Installing: {', '.join(packages)}")

    success = install_tools_via_apt(packages, logger)
    if success:
        logger.info("Tool installation completed.")
    else:
        logger.warning("Some tools may not have installed. Run: sudo apt install " + " ".join(packages))

    return True
