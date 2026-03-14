#!/usr/bin/env python3
"""
PlanetHack - CTF & Bug Bounty Tool
Main entry point for CLI and GUI modes
"""

import argparse
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "python"))

from core.logger import setup_logger
from core.config import Config

def main():
    parser = argparse.ArgumentParser(
        description="PlanetHack - Hack the Planet! 🌍",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --setup            # Check/install required tools (run first on Kali)
  python main.py --gui              # Launch GUI
  python main.py --cli              # Launch CLI
  python main.py --web              # Launch web UI (browser / Docker)
  python main.py --module sql       # Run SQL injection module
  python main.py --target https://example.com --module xss
        """
    )
    
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Run setup: check required tools and optionally install missing ones'
    )
    
    parser.add_argument(
        '--skip-tool-check',
        action='store_true',
        help='Skip tool availability check at startup (use if not on Kali)'
    )
    
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Launch GUI interface (default)'
    )
    
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Launch CLI interface'
    )
    
    parser.add_argument(
        '--web',
        action='store_true',
        help='Launch web UI (Flask, for Docker / browser access)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Web UI bind address (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Web UI port (default: 8080)'
    )
    
    parser.add_argument(
        '--module',
        type=str,
        help='Run specific module (recon, sql, xss, etc.)'
    )
    
    parser.add_argument(
        '--target',
        type=str,
        help='Target URL or IP address'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    
    parser.add_argument(
        '--env',
        type=str,
        choices=['dev', 'build', 'prod'],
        default='dev',
        help='Environment: dev, build, or prod'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output (for terminals that mangle ANSI codes, e.g. Tilix)'
    )
    
    parser.add_argument(
        '--ascii',
        action='store_true',
        help='Use plain ASCII characters instead of Unicode box-drawing (for limited terminals)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logger(level=args.log_level, env=args.env, no_color=args.no_color)
    logger.info("=" * 60)
    logger.info("PlanetHack - Hack the Planet!")
    logger.info("by HCKNKnuckle")
    logger.info("by HCKNKnuckle")
    logger.info("=" * 60)
    
    # Load configuration
    config = Config(args.config, env=args.env)
    
    # Setup mode: check and optionally install tools
    if args.setup:
        from core.tool_check import run_setup_check, check_tools, is_kali_or_debian
        installed, missing = check_tools(config)
        logger.info(f"Installed: {', '.join(installed) or 'none'}")
        if missing:
            logger.warning(f"Missing: {', '.join(m['binary'] for m in missing)}")
            if is_kali_or_debian():
                try:
                    from rich.prompt import Confirm
                    if Confirm.ask("Install missing tools via apt?", default=True):
                        run_setup_check(config, logger, ask_callback=lambda m: True)
                    else:
                        logger.info("Skipped. Run: sudo apt install " + " ".join({m["package"] for m in missing}))
                except ImportError:
                    ans = input("Install missing tools via apt? [Y/n]: ").strip().lower()
                    if ans != "n":
                        run_setup_check(config, logger, ask_callback=lambda m: True)
            else:
                logger.info("Not on Kali/Debian. Install manually: " + " ".join({m["package"] for m in missing}))
        else:
            logger.info("All required tools are installed.")
        return
    
    # Determine mode
    if args.web:
        # Web UI mode (Flask)
        from web.app import run_web
        from utils.helpers import is_port_in_use

        port = args.port
        if is_port_in_use(port, args.host):
            logger.warning(f"Port {port} is already in use.")
            if sys.stdin.isatty():
                # Interactive: prompt user for new port
                while True:
                    try:
                        prompt = f"Enter a different port (1-65535) [or Enter for {port + 1}]: "
                        raw = input(prompt).strip()
                        if not raw:
                            port = port + 1
                        else:
                            port = int(raw)
                        if 1 <= port <= 65535:
                            if is_port_in_use(port, args.host):
                                logger.warning(f"Port {port} is also in use. Try another.")
                            else:
                                logger.info(f"Using port {port}")
                                break
                        else:
                            print("Port must be between 1 and 65535.")
                    except ValueError:
                        print("Please enter a valid number.")
                    except (KeyboardInterrupt, EOFError):
                        logger.info("Cancelled.")
                        return
            else:
                # Non-interactive: try next available port
                for p in range(port + 1, min(port + 101, 65536)):
                    if not is_port_in_use(p, args.host):
                        port = p
                        logger.info(f"Port {port - 1} in use; using port {port}")
                        break
                else:
                    logger.error(f"All ports {port}-{port + 99} are in use. Specify --port.")
                    return
        run_web(config, logger, host=args.host, port=port)
    elif args.cli or args.module:
        # CLI mode
        from cli.main import run_cli
        run_cli(args, config, logger, ascii_mode=args.ascii)
    else:
        # GUI mode (default)
        try:
            from gui.main import run_gui
            run_gui(config, logger)
        except ImportError as e:
            logger.error(f"GUI dependencies not available: {e}")
            logger.info("Falling back to CLI mode...")
            from cli.main import run_cli
            run_cli(args, config, logger, ascii_mode=args.ascii)

if __name__ == "__main__":
    main()

