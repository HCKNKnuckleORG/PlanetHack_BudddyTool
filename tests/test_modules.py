"""
PlanetHack module tests
"""

import sys
from pathlib import Path

# Add project root so python/ is importable
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "python"))


def test_import_modules():
    """Test that all modules can be imported"""
    from modules import MODULE_REGISTRY, BaseModule

    assert len(MODULE_REGISTRY) >= 15
    assert BaseModule is not None


def test_base_module_interface():
    """Test BaseModule has required interface"""
    from modules.base import BaseModule

    assert hasattr(BaseModule, "run")
    assert hasattr(BaseModule, "get_info")
    assert hasattr(BaseModule, "validate_target")


def test_recon_plan_builder():
    """Test recon plan builds for valid target"""
    from core.recon_plan import build_recon_plan, normalize_target

    normalized = normalize_target("10.10.10.5")
    assert normalized["host"] == "10.10.10.5"
    assert "http://" in normalized["base_url"]

    phases = build_recon_plan("example.com", preset="full")
    assert len(phases) >= 1
    assert phases[0]["tool"] == "nmap"


def test_helpers():
    """Test utility helpers"""
    from utils.helpers import is_ip_address, validate_url, extract_domain

    assert is_ip_address("192.168.1.1") is True
    assert is_ip_address("not-an-ip") is False
    assert validate_url("https://example.com") is True
    assert extract_domain("https://sub.example.com/path") == "sub.example.com"


def test_tool_check():
    """Test tool check loads config and checks tools"""
    from core.tool_check import (
        check_tool_available,
        get_tools_from_config,
        check_tools,
    )

    # Mock config with tools_required
    class MockConfig:
        config = {
            "setup": {
                "tools_required": {
                    "nmap": {"package": "nmap", "description": "Port scan"},
                    "nonexistent_tool_xyz": {"package": "nonexistent", "description": "Test"},
                }
            }
        }

    tools = get_tools_from_config(MockConfig())
    assert "nmap" in tools
    assert tools["nmap"]["package"] == "nmap"

    installed, missing = check_tools(MockConfig())
    # nmap might or might not be installed; nonexistent_tool_xyz should be missing
    assert "nonexistent_tool_xyz" in [m["binary"] for m in missing]
