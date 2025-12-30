"""
Interactive selectors for Glance CLI.
Handles Java and Minecraft version selection with Rich UI.
"""

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from utils.platform_utils import (
    find_java_installations,
    get_java_version,
    get_keytool_executable,
)
from utils.minecraft import get_minecraft_versions
from utils.certificates import find_cacerts, check_cert_installed

console = Console()


def show_spinner(description: str):
    """Context manager for showing a spinner with a description."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def select_java():
    """Interactive Java installation selector with Rich UI."""
    with show_spinner("Searching for Java installations...") as progress:
        progress.add_task("Searching for Java installations...", total=None)
        java_installations = find_java_installations()

    if not java_installations:
        console.print("[bold red]✗[/] Java not found!")
        console.print("  [dim]Install Java (JDK 8+) and try again[/]")
        return None

    table = _build_java_table(java_installations)
    console.print()
    console.print(table)
    console.print()

    return _prompt_java_selection(java_installations)


def _build_java_table(java_installations: list) -> Table:
    """Build the Java installations table."""
    table = Table(
        title=f"[bold cyan]Found {len(java_installations)} Java Installation(s)[/]",
        box=box.ROUNDED,
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("#", style="cyan", justify="center", width=4)
    table.add_column("Status", justify="center", width=10)
    table.add_column("Path", style="white")
    table.add_column("Version", style="green", width=15)

    for i, java_home in enumerate(java_installations, 1):
        version = get_java_version(java_home)
        cacerts = find_cacerts(java_home)
        keytool = get_keytool_executable(java_home)

        if cacerts:
            installed = check_cert_installed(keytool, cacerts)
            status = "[bold green]✓ CERT[/]" if installed else "[yellow]○ NO CERT[/]"
        else:
            status = "[dim]?[/]"

        table.add_row(str(i), status, java_home, version)

    return table


def _prompt_java_selection(java_installations: list):
    while True:
        try:
            choice = Prompt.ask("[cyan]Select Java[/]", default="1")
            choice = int(choice)
            if 1 <= choice <= len(java_installations):
                selected = java_installations[choice - 1]
                console.print(f"[bold green]✓[/] Selected: [cyan]{selected}[/]")
                return selected
            else:
                console.print("[red]Invalid number, try again[/]")
        except ValueError:
            console.print("[red]Enter a number[/]")
        except KeyboardInterrupt:
            return None


def select_minecraft_version(minecraft_dir: str):
    """Interactive Minecraft version selector with Rich UI."""
    with show_spinner("Searching for Minecraft versions...") as progress:
        progress.add_task("Searching for Minecraft versions...", total=None)
        versions = get_minecraft_versions(minecraft_dir)

    if not versions:
        console.print("[bold red]✗[/] No Minecraft versions found!")
        console.print(f"  [dim]Check folder: {minecraft_dir}/versions[/]")
        return None

    page_size = 15
    current_page = 0
    total_pages = (len(versions) + page_size - 1) // page_size

    while True:
        _display_version_page(versions, current_page, page_size, total_pages)
        result = _handle_version_input(versions, current_page, total_pages)

        if result == "next":
            current_page += 1
        elif result == "prev":
            current_page -= 1
        elif result is not None:
            return result


def _display_version_page(
    versions: list, current_page: int, page_size: int, total_pages: int
):
    """Display a page of Minecraft versions."""
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, len(versions))

    table = Table(
        title=f"[bold cyan]Minecraft Versions[/] [dim](Page {current_page + 1}/{total_pages})[/]",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("#", style="cyan", justify="center", width=5)
    table.add_column("Version", style="white")

    for i in range(start_idx, end_idx):
        table.add_row(str(i + 1), versions[i])

    console.print()
    console.print(table)

    if total_pages > 1:
        console.print(
            "[dim]  [n] Next page  •  [p] Previous page  •  Or enter version number[/]"
        )
    console.print()


def _handle_version_input(versions: list, current_page: int, total_pages: int):
    """Handle user input for version selection. Returns selected version or navigation command."""
    try:
        choice = Prompt.ask("[cyan]Select version[/]")

        if choice.lower() == "n" and current_page < total_pages - 1:
            return "next"
        elif choice.lower() == "p" and current_page > 0:
            return "prev"

        choice = int(choice)
        if 1 <= choice <= len(versions):
            selected = versions[choice - 1]
            console.print(f"[bold green]✓[/] Selected: [cyan]{selected}[/]")
            return selected
        else:
            console.print("[red]Invalid number[/]")
            return None
    except ValueError:
        console.print("[red]Enter a number[/]")
        return None
    except KeyboardInterrupt:
        return None


def select_mode():
    """Let user choose between Auto mode (launch Minecraft) or Manual mode (proxy only)."""
    console.print()
    console.rule("[bold cyan]Select Mode[/]", style="cyan")
    console.print()

    table = Table(
        title="[bold cyan]Available Modes[/]",
        box=box.ROUNDED,
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("#", style="cyan", justify="center", width=4)
    table.add_column("Mode", style="white", width=15)
    table.add_column("Description", style="dim")

    table.add_row(
        "1",
        "[bold green]Auto[/]",
        "Launch Minecraft automatically with proxy configured",
    )
    table.add_row(
        "2",
        "[bold yellow]Manual[/]",
        "Start proxy only on port 8080 - launch Minecraft yourself",
    )

    console.print(table)
    console.print()

    while True:
        try:
            choice = Prompt.ask("[cyan]Select mode[/]", default="1")
            choice = int(choice)
            if choice == 1:
                console.print(
                    "[bold green]✓[/] Mode: [cyan]Auto[/] (with Minecraft launch)"
                )
                return "auto"
            elif choice == 2:
                console.print("[bold green]✓[/] Mode: [cyan]Manual[/] (proxy only)")
                return "manual"
            else:
                console.print("[red]Invalid choice. Enter 1 or 2[/]")
        except ValueError:
            console.print("[red]Enter a number[/]")
        except KeyboardInterrupt:
            return None
