"""
Main entry point for Glance CLI.
Orchestrates the user interaction flow.
"""

import sys

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from cli.display import print_banner
from cli.selectors import select_java, select_minecraft_version, select_mode
from cli.session import (
    setup_certificates,
    get_username,
    launch_session,
    launch_manual_mode,
)
from utils.minecraft import find_minecraft_directory

console = Console()


def show_spinner(description: str):
    """Context manager for showing a spinner with a description."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def main():
    """Main entry point for the Glance CLI."""
    console.clear()
    print_banner()
    console.print()

    java_home = select_java()
    if not java_home:
        console.print("\n[bold red]✗[/] Java not selected. Exiting.")
        sys.exit(1)

    success, cert_path = setup_certificates(java_home)
    if not success:
        sys.exit(1)

    mode = select_mode()
    if not mode:
        console.print("\n[bold red]✗[/] Mode not selected. Exiting.")
        sys.exit(1)

    if mode == "manual":
        launch_manual_mode()
        return

    minecraft_dir = _find_minecraft()
    if not minecraft_dir:
        console.print("[bold red]✗[/] .minecraft folder not found!")
        console.print("  [dim]Run Minecraft at least once first[/]")
        sys.exit(1)

    console.print(f"[bold green]✓[/] Found Minecraft: [dim]{minecraft_dir}[/]")
    console.print()
    console.rule("[bold cyan]Select Minecraft Version[/]", style="cyan")

    version = select_minecraft_version(minecraft_dir)
    if not version:
        console.print("\n[bold red]✗[/] Version not selected. Exiting.")
        sys.exit(1)

    username = get_username()
    launch_session(java_home, minecraft_dir, version, username)


def _find_minecraft() -> str | None:
    """Find Minecraft installation with spinner."""
    with show_spinner("Finding Minecraft installation...") as progress:
        progress.add_task("Finding Minecraft installation...", total=None)
        return find_minecraft_directory()


if __name__ == "__main__":
    main()
