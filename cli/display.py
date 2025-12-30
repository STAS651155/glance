"""
Display utilities for Glance CLI.
Handles banner, panels, and visual output components.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

from utils.platform_utils import get_platform

console = Console()


def print_banner():
    """Display the Glance banner."""
    banner = Text()
    banner.append(
        "╔═══════════════════════════════════════════════════════════╗\n", style="cyan"
    )
    banner.append("║", style="cyan")
    banner.append(
        "              🛡️  GLANCE  🛡️                              ", style="bold white"
    )
    banner.append("║\n", style="cyan")
    banner.append("║", style="cyan")
    banner.append(
        "        Minecraft Security Interceptor                     ", style="dim white"
    )
    banner.append("║\n", style="cyan")
    banner.append(
        "╠═══════════════════════════════════════════════════════════╣\n", style="cyan"
    )
    banner.append("║", style="cyan")
    banner.append(f"  Platform: {get_platform().upper():<48}", style="green")
    banner.append("║\n", style="cyan")
    banner.append(
        "╚═══════════════════════════════════════════════════════════╝", style="cyan"
    )
    console.print(banner)
    console.print()
    console.print(
        Panel(
            "[bold]Protects against malicious mods stealing your tokens[/bold]\n"
            "[dim]Intercepts Discord/Telegram webhooks and API calls[/dim]",
            border_style="dim",
            box=box.ROUNDED,
        )
    )


def show_active_session_panel():
    """Display the active session panel."""
    console.print()
    console.print(
        Panel(
            "[bold green]Minecraft is running![/]\n\n"
            "[cyan]All HTTPS traffic is being intercepted[/]\n"
            "[dim]Suspicious requests will be blocked and logged[/]\n\n"
            "[yellow]Press Ctrl+C to stop[/]",
            title="[bold]🎮 Active Session[/]",
            border_style="green",
            box=box.DOUBLE,
        )
    )


def show_manual_launch_panel():
    """Display the manual launch instructions panel."""
    console.print()
    console.print(
        Panel(
            "[yellow]Minecraft not launched automatically[/]\n\n"
            "Launch Minecraft manually with proxy:\n"
            "[cyan]  Host: 127.0.0.1[/]\n"
            "[cyan]  Port: 8080[/]\n\n"
            "[dim]Press Ctrl+C to stop MITM proxy[/]",
            title="[bold]Manual Launch Required[/]",
            border_style="yellow",
        )
    )


def show_manual_mode_panel():
    """Display the manual mode panel with proxy instructions."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]MITM Proxy is running on port 8080[/]\n\n"
            "[white]Configure Minecraft to use the proxy:[/]\n"
            "[cyan]  • Host: 127.0.0.1[/]\n"
            "[cyan]  • Port: 8080[/]\n\n"
            "[dim]Launch Minecraft with JVM arguments:[/]\n"
            "[dim]  -Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=8080[/]\n\n"
            "[yellow]Press Ctrl+C to stop the proxy[/]",
            title="[bold]🔧 Manual Mode Active[/]",
            border_style="cyan",
            box=box.DOUBLE,
        )
    )
