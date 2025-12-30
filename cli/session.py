"""
Session management for Glance CLI.
Handles certificate setup and Minecraft launch session.
"""

import os
import subprocess
import time

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.config import EXPORT_FOLDER
from utils.minecraft import launch_minecraft
from utils.certificates import (
    get_mitmproxy_cert_path,
    install_cert_to_java,
    generate_mitmproxy_cert,
)
from cli.display import (
    show_active_session_panel,
    show_manual_launch_panel,
    show_manual_mode_panel,
)

console = Console()


def show_spinner(description: str):
    """Context manager for showing a spinner with a description."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def setup_certificates(java_home: str) -> tuple[bool, str | None]:
    """Handle certificate generation and installation with Rich UI."""
    console.print()
    console.rule("[bold cyan]Certificate Setup[/]", style="cyan")
    console.print()

    with show_spinner("Checking mitmproxy certificate...") as progress:
        progress.add_task("Checking mitmproxy certificate...", total=None)
        success = generate_mitmproxy_cert()

    if not success:
        console.print("[bold red]✗[/] Failed to create certificate. Exiting.")
        return False, None

    cert_path = get_mitmproxy_cert_path()
    console.print(f"[bold green]✓[/] Certificate: [dim]{cert_path}[/]")

    with show_spinner("Installing certificate to Java keystore...") as progress:
        progress.add_task("Installing certificate to Java keystore...", total=None)
        installed = install_cert_to_java(java_home, cert_path)

    if not installed:
        console.print("[bold yellow]![/] Failed to install certificate automatically")
        console.print("  [dim]Minecraft may not trust the proxy[/]")
        if not Confirm.ask("Continue anyway?", default=False):
            return False, None

    return True, cert_path


def get_username() -> str:
    """Prompt user for Minecraft username."""
    console.print()
    return Prompt.ask("[cyan]Enter username[/]", default="Player")


def launch_session(java_home: str, minecraft_dir: str, version: str, username: str):
    """Launch the MITM proxy and Minecraft with Rich UI."""
    console.print()
    console.rule("[bold cyan]Launching[/]", style="cyan")
    console.print()

    console.print("[bold green]▶[/] Starting MITM proxy on port [cyan]8080[/]...")
    console.print(f"[dim]  Exports folder: {EXPORT_FOLDER.absolute()}[/]")
    console.print()

    mitm_process = _start_mitm_proxy()
    if not mitm_process:
        return

    time.sleep(2)

    mc_process = launch_minecraft(java_home, minecraft_dir, version, username)
    _handle_session(mitm_process, mc_process)


def _start_mitm_proxy() -> subprocess.Popen | None:
    """Start the mitmproxy process."""
    try:
        addon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "core", "addon.py"
        )
        mitm_process = subprocess.Popen(
            [
                "mitmdump",
                "-s",
                addon_path,
                "--listen-port",
                "8080",
                "--set",
                "block_global=false",
                "--set",
                "ssl_insecure=true",
                "--ssl-insecure",
            ],
        )
        console.print(
            f"[bold green]✓[/] MITM proxy started [dim](PID: {mitm_process.pid})[/]"
        )
        return mitm_process
    except FileNotFoundError:
        console.print("[bold red]✗[/] mitmdump not found!")
        console.print("  [dim]Install: pip install mitmproxy[/]")
        return None


def _handle_session(mitm_process: subprocess.Popen, mc_process):
    """Handle the active session, waiting for processes to complete."""
    if mc_process:
        show_active_session_panel()
        try:
            mc_process.wait()
        except KeyboardInterrupt:
            pass
        finally:
            mitm_process.terminate()
            console.print("\n[bold green]✓[/] Session ended")
    else:
        show_manual_launch_panel()
        try:
            mitm_process.wait()
        except KeyboardInterrupt:
            mitm_process.terminate()
            console.print("\n[bold green]✓[/] Proxy stopped")


def launch_manual_mode():
    """Launch only the MITM proxy for manual Minecraft launch."""
    console.print()
    console.rule("[bold cyan]Manual Mode[/]", style="cyan")
    console.print()

    console.print("[bold green]▶[/] Starting MITM proxy on port [cyan]8080[/]...")
    console.print(f"[dim]  Exports folder: {EXPORT_FOLDER.absolute()}[/]")
    console.print()

    mitm_process = _start_mitm_proxy()
    if not mitm_process:
        return

    time.sleep(1)
    show_manual_mode_panel()

    try:
        mitm_process.wait()
    except KeyboardInterrupt:
        mitm_process.terminate()
        console.print("\n[bold green]✓[/] Proxy stopped")
