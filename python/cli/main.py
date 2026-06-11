"""
PlanetHack CLI Interface
Command-line interface for running modules
"""

import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from modules import MODULE_REGISTRY

console = Console()

UNICODE_BANNER = """
    +=========================================================+
    |                                                           |
    |     PLANET HACK - HACK THE PLANET!                       |
    |                                                           |
    |     "Mess with the best, die like the rest!"             |
    |                                                           |
    +=========================================================+
    """

FANCY_BANNER = """
    \u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557
    \u2551                                                           \u2551
    \u2551     PLANET HACK - HACK THE PLANET!                       \u2551
    \u2551                                                           \u2551
    \u2551     "Mess with the best, die like the rest!"             \u2551
    \u2551                                                           \u2551
    \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d
    """

_ascii_mode = False


def print_banner():
    """Print PlanetHack banner (uses plain ASCII if --ascii flag is set)."""
    banner = UNICODE_BANNER if _ascii_mode else FANCY_BANNER
    console.print(Panel(banner, style="bold green"))


def show_modules():
    """Display available modules from Bug Bounty Bootcamp"""
    table = Table(title="Available Modules (Bug Bounty Bootcamp)")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description", style="yellow")

    for module_id, module_class in MODULE_REGISTRY.items():
        mod = module_class(None, None)
        info = mod.get_info()
        table.add_row(module_id, info["name"], info["description"])

    console.print(table)


def run_module(module_id: str, target: str, config, logger):
    """Run a specific module"""
    logger.info(f"Running module: {module_id} on target: {target}")

    try:
        console.print(f"[green][+][/green] Module {module_id} execution started")
        console.print(f"[cyan][*][/cyan] Target: {target}")

        module_class = MODULE_REGISTRY.get(module_id)
        if module_class:
            module = module_class(config, logger)
            result = module.run(target)
            console.print(f"[green][+][/green] Result: {result}")
        else:
            console.print(f"[red][!][/red] Module {module_id} not found")

    except Exception as e:
        logger.error(f"Error running module: {e}")
        console.print(f"[red][!][/red] Error: {str(e)}")


def interactive_mode(config, logger):
    """Interactive CLI mode"""
    print_banner()

    while True:
        console.print("\n[bold cyan]PlanetHack CLI[/bold cyan]")
        console.print("1. List modules")
        console.print("2. Run module")
        console.print("3. Exit")

        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3"])

        if choice == "1":
            show_modules()
        elif choice == "2":
            module_id = Prompt.ask("Enter module ID")
            target = Prompt.ask("Enter target URL or IP")
            run_module(module_id, target, config, logger)
        elif choice == "3":
            console.print("[green]Hack the Planet![/green]")
            sys.exit(0)


def run_cli(args, config, logger, ascii_mode=False):
    """Run CLI interface"""
    global _ascii_mode
    _ascii_mode = ascii_mode

    if args.module and args.target:
        print_banner()
        run_module(args.module, args.target, config, logger)
    else:
        interactive_mode(config, logger)
