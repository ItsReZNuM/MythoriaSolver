"""
Game-style interactive TUI menu for Minecraft Chat Game Bot.
Start / Select Version / Settings / Exit with full configuration sub-menus.
Ultra-readable layout with compact aligned columns and bulk message management.
"""
import sys
import os
import time
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

from settings import (
    Settings,
    GAME_TYPES,
    GAME_TYPE_LABELS,
    GameTypeDelay,
    StealthSettings,
    TabchiSettings,
)
from minecraft.log_finder import (
    detect_minecraft_logs,
    prompt_select_minecraft_instance,
    MinecraftInstance,
)

console = Console(safe_box=True)

MENU_WIDTH = 78

# ── ASCII Art Banner ─────────────────────────────────────────────────
LOGO = r"""
 __  __  ____    ____   _           _     ____          _
|  \/  |/ ___|  / ___| | |__   __ _| |_  | __ )  ___  | |_
| |\/| | |     | |     | '_ \ / _` | __| |  _ \ / _ \ | __|
| |  | | |___  | |___  | | | | (_| | |_  | |_) | (_) || |_
|_|  |_|\____|  \____| |_| |_|\__,_|\__| |____/ \___/  \__|
"""


def clear_screen():
    os.system("cls" if sys.platform == "win32" else "clear")


def _input_safe(prompt: str, default: str = "") -> str:
    """Safe input with keyboard interrupt handling."""
    try:
        val = console.input(prompt).strip()
        return val if val else default
    except (KeyboardInterrupt, EOFError):
        return default


def _input_float(prompt: str, default: float, min_val: float = 0.0, max_val: float = 999.0) -> float:
    val_str = _input_safe(prompt, str(default))
    try:
        v = float(val_str)
        return max(min_val, min(max_val, v))
    except ValueError:
        return default


def _input_int(prompt: str, default: int, min_val: int = 0, max_val: int = 999) -> int:
    val_str = _input_safe(prompt, str(default))
    try:
        v = int(val_str)
        return max(min_val, min(max_val, v))
    except ValueError:
        return default


def _input_bool(prompt: str, default: bool) -> bool:
    hint = "y" if default else "n"
    val = _input_safe(f"{prompt} [bold dim](y/n)[/bold dim] [{hint}]: ", hint).lower()
    if val in ("y", "yes", "1", "true"):
        return True
    if val in ("n", "no", "0", "false"):
        return False
    return default


def get_active_instance_label(settings: Settings) -> str:
    """Returns a short friendly label for the currently active Minecraft log."""
    active_path = settings.get_active_log_path()
    norm_active = str(active_path.resolve()).lower()
    instances = detect_minecraft_logs(custom_path=settings.minecraft_log_path)
    for inst in instances:
        if str(inst.path.resolve()).lower() == norm_active:
            return inst.name
    return active_path.parent.parent.name if active_path.parent.name == "logs" else active_path.name


def show_main_menu(settings: Settings) -> str:
    """
    Show the main menu. Returns 'start', 'select_version', 'settings', or 'exit'.
    """
    clear_screen()
    console.print(f"[bold magenta]{LOGO}[/bold magenta]")

    instance_label = get_active_instance_label(settings)
    mode_text = "[bold yellow]DRY-RUN[/bold yellow]" if settings.dry_run else "[bold green]LIVE[/bold green]"
    tabchi_text = f"[bold green]ENABLED ({len(settings.tabchi.messages)} msgs)[/bold green]" if settings.tabchi.enabled else "[dim red]DISABLED[/dim red]"

    info_text = (
        f"[dim]Player:[/dim] [bold cyan]{settings.player_username}[/bold cyan]  |  "
        f"[dim]Version:[/dim] [bold white]{instance_label[:24]}[/bold white]\n"
        f"[dim]Mode:[/dim] {mode_text}  |  "
        f"[dim]Tabchi:[/dim] {tabchi_text}"
    )
    console.print(Panel(info_text, border_style="magenta", padding=(0, 2), width=MENU_WIDTH))

    menu_table = Table(box=box.ROUNDED, show_header=True, expand=False, width=MENU_WIDTH)
    menu_table.add_column("No.", style="bold cyan", width=6)
    menu_table.add_column("Action", style="bold white", width=28)
    menu_table.add_column("Description", style="dim", width=38)

    menu_table.add_row("[1]", "START BOT", "Launch chat solver & monitoring")
    menu_table.add_row("[2]", "SELECT MC VERSION", f"Active: {instance_label[:30]}")
    menu_table.add_row("[3]", "SETTINGS", "Username, Delays, Stealth, Tabchi...")
    menu_table.add_row("[4]", "EXIT", "Close application")

    console.print(Panel(menu_table, title="[bold cyan]MAIN MENU[/bold cyan]", border_style="cyan", padding=(0, 1), width=MENU_WIDTH))
    choice = _input_safe("[bold green]>> Select option [1-4]: [/bold green]", "1")

    if choice == "1":
        return "start"
    elif choice == "2":
        return "select_version"
    elif choice == "3":
        return "settings"
    elif choice == "4":
        return "exit"
    return "start"


def show_settings_menu(settings: Settings):
    """Settings sub-menu with clear, adjacent number-action layout."""
    while True:
        clear_screen()
        console.print("[bold magenta]== CONFIGURATION & SETTINGS ==[/bold magenta]\n")

        cat_table = Table(box=box.ROUNDED, show_header=True, expand=False, width=MENU_WIDTH)
        cat_table.add_column("No.", style="bold cyan", width=6)
        cat_table.add_column("Category", style="bold white", width=24)
        cat_table.add_column("Current Value / Summary", style="dim", width=42)

        instance_label = get_active_instance_label(settings)
        cat_table.add_row("[1]", "Player Username", f"[bold cyan]{settings.player_username}[/bold cyan]")
        cat_table.add_row("[2]", "Minecraft Version / Log", f"[white]{instance_label[:38]}[/white]")
        cat_table.add_row("[3]", "General Settings", f"Mode: {'DRY' if settings.dry_run else 'LIVE'} | Focus: {'ON' if settings.require_focus else 'OFF'} | {settings.send_method.upper()}")
        cat_table.add_row("[4]", "Global Delays", f"{settings.global_min_delay:.1f}s - {settings.global_max_delay:.1f}s")
        active_gt = sum(1 for gt in GAME_TYPES if settings.game_delays.get(gt, GameTypeDelay()).enabled)
        cat_table.add_row("[5]", "Per-Game Delays", f"{active_gt}/{len(GAME_TYPES)} game types enabled")
        cat_table.add_row("[6]", "Answer Ratio", f"1 of every {settings.answer_ratio} games ({100/settings.answer_ratio:.0f}%)")
        cat_table.add_row("[7]", "Anti-Cheat Stealth", f"{settings.stealth.fake_attempts_min}-{settings.stealth.fake_attempts_max} fake typos")
        cat_table.add_row("[8]", "Auto-Learning", f"{'ON' if settings.auto_learn_words else 'OFF'} | Filter Random: {'ON' if settings.auto_learn_filter_random else 'OFF'}")
        tabchi_status = "ENABLED" if settings.tabchi.enabled else "DISABLED"
        cat_table.add_row("[9]", "Tabchi / Auto-Ads", f"{tabchi_status} | {len(settings.tabchi.messages)} msgs | {settings.tabchi.min_interval_minutes:.1f}-{settings.tabchi.max_interval_minutes:.1f}m")
        cat_table.add_row("[10]", "View All Configuration", "Display complete summary card")
        cat_table.add_row("[0]", "<< BACK TO MAIN MENU", "Save changes and return")

        console.print(cat_table)
        choice = _input_safe("\n[bold green]>> Select category [0-10]: [/bold green]", "0")

        if choice == "0":
            settings.save()
            console.print("[green][+] Settings saved successfully![/green]")
            time.sleep(0.8)
            return
        elif choice == "1":
            _settings_username(settings)
        elif choice == "2":
            _settings_minecraft_version(settings)
        elif choice == "3":
            _settings_general(settings)
        elif choice == "4":
            _settings_global_delays(settings)
        elif choice == "5":
            _settings_per_game_delays(settings)
        elif choice == "6":
            _settings_ratio(settings)
        elif choice == "7":
            _settings_stealth(settings)
        elif choice == "8":
            _settings_learning(settings)
        elif choice == "9":
            _settings_tabchi(settings)
        elif choice == "10":
            _show_full_config(settings)


def _settings_username(settings: Settings):
    """Direct, single-step prompt to update player username."""
    clear_screen()
    console.print("[bold magenta]== PLAYER USERNAME CONFIGURATION ==[/bold magenta]\n")
    console.print(f"Current Username: [bold green]{settings.player_username}[/bold green]\n")
    console.print("[dim]Used for winner verification, stat tracking, and chat targeting.[/dim]\n")

    new_name = _input_safe(
        f"[bold cyan]Enter your Minecraft in-game username [{settings.player_username}]: [/bold cyan]",
        settings.player_username,
    ).strip()

    if new_name:
        settings.player_username = new_name
        console.print(f"[bold green][+] Username updated to: '{settings.player_username}'[/bold green]")
    time.sleep(1.0)


def _settings_minecraft_version(settings: Settings):
    """Scan and select which Minecraft instance / version to monitor."""
    clear_screen()
    console.print("[bold magenta]== MINECRAFT VERSION & LOG SELECTION ==[/bold magenta]\n")
    console.print("[dim]Scanning PC for installed Minecraft launchers and versions...[/dim]\n")

    instances = detect_minecraft_logs(custom_path=settings.minecraft_log_path)
    if not instances:
        console.print("[yellow][!] No standard Minecraft log files detected on this PC.[/yellow]")
        custom = _input_safe("[cyan]Enter full path to latest.log manually: [/cyan]", "").strip().strip('"\'')
        if custom and Path(custom).is_file():
            settings.minecraft_log_path = str(Path(custom).resolve())
            console.print(f"[green][+] Selected custom log: {settings.minecraft_log_path}[/green]")
        time.sleep(1.2)
        return

    chosen_path = prompt_select_minecraft_instance(
        instances=instances,
        current_selected_path=str(settings.get_active_log_path()),
    )
    if chosen_path:
        settings.minecraft_log_path = str(chosen_path.resolve())
        console.print(f"\n[bold green][+] Selected Minecraft instance:[/bold green] {chosen_path}")
        time.sleep(1.2)


def _settings_general(settings: Settings):
    """General settings: dry_run, focus, send_method, chat_key, cooldown."""
    clear_screen()
    console.print("[bold cyan]== GENERAL SETTINGS ==[/bold cyan]\n")

    settings.player_username = _input_safe(
        f"[cyan]Player Username[/cyan] [{settings.player_username}]: ",
        settings.player_username,
    )
    settings.dry_run = _input_bool(
        f"[cyan]Dry-Run Mode (no keystrokes)[/cyan]", settings.dry_run
    )
    settings.require_focus = _input_bool(
        f"[cyan]Require Minecraft Focus[/cyan]", settings.require_focus
    )

    method = _input_safe(
        f"[cyan]Send Method[/cyan] [bold dim](paste/write)[/bold dim] [{settings.send_method}]: ",
        settings.send_method,
    ).lower()
    if method in ("paste", "write"):
        settings.send_method = method

    settings.chat_key = _input_safe(
        f"[cyan]Chat Open Key[/cyan] [{settings.chat_key}]: ", settings.chat_key
    )

    settings.send_cooldown = _input_float(
        f"[cyan]Server Cooldown (seconds)[/cyan] [{settings.send_cooldown}]: ",
        settings.send_cooldown, 1.0, 30.0,
    )

    settings.max_candidate_retries = _input_int(
        f"[cyan]Max Candidate Retries[/cyan] [{settings.max_candidate_retries}]: ",
        settings.max_candidate_retries, 0, 10,
    )

    console.print("[green][+] General settings updated.[/green]\n")
    time.sleep(1.0)


def _settings_global_delays(settings: Settings):
    """Global delay configuration."""
    clear_screen()
    console.print("[bold cyan]== GLOBAL DELAY SETTINGS ==[/bold cyan]")
    console.print("[dim]Fallback delays used when per-game-type delay is not set.[/dim]\n")

    settings.global_min_delay = _input_float(
        f"[cyan]Minimum Delay (seconds)[/cyan] [{settings.global_min_delay:.1f}]: ",
        settings.global_min_delay, 0.0, 60.0,
    )
    settings.global_max_delay = _input_float(
        f"[cyan]Maximum Delay (seconds)[/cyan] [{settings.global_max_delay:.1f}]: ",
        settings.global_max_delay, 0.0, 60.0,
    )

    if settings.global_min_delay > settings.global_max_delay:
        settings.global_min_delay, settings.global_max_delay = settings.global_max_delay, settings.global_min_delay

    console.print(f"[green][+] Global delays set: {settings.global_min_delay:.1f}s - {settings.global_max_delay:.1f}s[/green]\n")
    time.sleep(1.0)


def _settings_per_game_delays(settings: Settings):
    """Per-game-type delay and enable/disable settings."""
    while True:
        clear_screen()
        console.print("[bold cyan]== PER GAME TYPE DELAYS ==[/bold cyan]\n")

        gt_table = Table(box=box.ROUNDED, show_header=True, expand=False, width=MENU_WIDTH)
        gt_table.add_column("No.", style="bold cyan", width=6)
        gt_table.add_column("Game Type", style="bold white", width=26)
        gt_table.add_column("Status", width=12)
        gt_table.add_column("Min Delay", justify="right", width=14)
        gt_table.add_column("Max Delay", justify="right", width=14)

        for idx, gt in enumerate(GAME_TYPES, 1):
            gd = settings.game_delays.get(gt, GameTypeDelay())
            en_style = "green" if gd.enabled else "red"
            gt_table.add_row(
                f"[{idx}]",
                GAME_TYPE_LABELS.get(gt, gt),
                f"[{en_style}]{'ENABLED' if gd.enabled else 'DISABLED'}[/{en_style}]",
                f"{gd.min_delay:.1f}s",
                f"{gd.max_delay:.1f}s",
            )

        gt_table.add_row("[0]", "<< BACK", "-", "-", "-")
        console.print(gt_table)

        choice = _input_safe(f"[bold green]>> Select game type to edit [0-{len(GAME_TYPES)}]: [/bold green]", "0")
        if choice == "0":
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(GAME_TYPES):
                gt = GAME_TYPES[idx]
                _edit_game_type_delay(settings, gt)
        except ValueError:
            pass


def _edit_game_type_delay(settings: Settings, game_type: str):
    """Edit delay for a single game type."""
    label = GAME_TYPE_LABELS.get(game_type, game_type)
    gd = settings.game_delays.get(game_type, GameTypeDelay())

    clear_screen()
    console.print(f"[bold cyan]== EDIT DELAY: {label.upper()} ==[/bold cyan]\n")

    gd.enabled = _input_bool(f"Enable answers for '{label}'", gd.enabled)
    if gd.enabled:
        gd.min_delay = _input_float(
            f"[cyan]Min Delay (seconds)[/cyan] [{gd.min_delay:.1f}]: ",
            gd.min_delay, 0.0, 60.0,
        )
        gd.max_delay = _input_float(
            f"[cyan]Max Delay (seconds)[/cyan] [{gd.max_delay:.1f}]: ",
            gd.max_delay, 0.0, 60.0,
        )
        if gd.min_delay > gd.max_delay:
            gd.min_delay, gd.max_delay = gd.max_delay, gd.min_delay

    settings.game_delays[game_type] = gd
    console.print(f"[green][+] Updated {label} settings.[/green]")
    time.sleep(0.8)


def _settings_ratio(settings: Settings):
    """Answer frequency ratio setting."""
    clear_screen()
    console.print("[bold cyan]== ANSWER FREQUENCY RATIO ==[/bold cyan]")
    console.print("[dim]Control how often the bot answers games to blend in with players.[/dim]\n")
    console.print("  • 1 = Answer 100% of games (every single game)")
    console.print("  • 2 = Answer ~50% of games (1 out of every 2)")
    console.print("  • 3 = Answer ~33% of games (1 out of every 3)\n")

    settings.answer_ratio = _input_int(
        f"[cyan]Answer 1 out of every N games[/cyan] [{settings.answer_ratio}]: ",
        settings.answer_ratio, 1, 20,
    )
    console.print(f"[green][+] Ratio set: 1 of every {settings.answer_ratio} games ({100/settings.answer_ratio:.0f}%)[/green]\n")
    time.sleep(1.0)


def _settings_stealth(settings: Settings):
    """Stealth and fake wrong answer configuration."""
    clear_screen()
    st = settings.stealth
    console.print("[bold cyan]== ANTI-CHEAT & STEALTH CONFIGURATION ==[/bold cyan]")
    console.print("[dim]Simulates realistic human mistakes before submitting the correct answer.[/dim]\n")

    st.fake_attempts_min = _input_int(
        f"[cyan]Min Fake Wrong Attempts[/cyan] [{st.fake_attempts_min}]: ",
        st.fake_attempts_min, 0, 5,
    )
    st.fake_attempts_max = _input_int(
        f"[cyan]Max Fake Wrong Attempts[/cyan] [{st.fake_attempts_max}]: ",
        st.fake_attempts_max, 0, 5,
    )
    if st.fake_attempts_min > st.fake_attempts_max:
        st.fake_attempts_min, st.fake_attempts_max = st.fake_attempts_max, st.fake_attempts_min

    st.fake_attempt_cooldown = _input_float(
        f"[cyan]Cooldown Between Fakes (seconds)[/cyan] [{st.fake_attempt_cooldown:.1f}]: ",
        st.fake_attempt_cooldown, 1.0, 10.0,
    )

    console.print("\n[bold]Typo Simulation Strategies:[/bold]")
    st.typo_nearby_keys = _input_bool("  Keyboard Neighbor Typos (e.g. 'a' -> 's')", st.typo_nearby_keys)
    st.typo_swap_case = _input_bool("  Accidental Lowercase Initial", st.typo_swap_case)
    st.typo_partial_word = _input_bool("  Send Half-Word First", st.typo_partial_word)
    st.typo_reversed_word = _input_bool("  Reversed Word Mistake", st.typo_reversed_word)
    st.typo_missing_chars = _input_bool("  Drop Letters (Fast Typing)", st.typo_missing_chars)

    console.print("[green][+] Stealth settings updated.[/green]\n")
    time.sleep(1.0)


def _settings_learning(settings: Settings):
    """Auto-learning configuration."""
    clear_screen()
    console.print("[bold cyan]== AUTO-LEARNING SETTINGS ==[/bold cyan]")
    console.print("[dim]Allows the bot to automatically learn unknown answers announced by the server.[/dim]\n")

    settings.auto_learn_words = _input_bool(
        "Auto-Learn new words from server", settings.auto_learn_words
    )
    if settings.auto_learn_words:
        settings.auto_learn_min_length = _input_int(
            f"[cyan]Minimum Word Length to Learn[/cyan] [{settings.auto_learn_min_length}]: ",
            settings.auto_learn_min_length, 2, 20,
        )
        settings.auto_learn_filter_random = _input_bool(
            "Filter out random strings (e.g. 'OnpjAm', '84H2he')",
            settings.auto_learn_filter_random,
        )

    console.print("[green][+] Auto-learning settings updated.[/green]\n")
    time.sleep(1.0)


# ── Tabchi / Auto-Advertiser Sub-Menu ──────────────────────────────────
def _settings_tabchi(settings: Settings):
    """Sub-menu for Tabchi / Auto-Advertiser configuration."""
    tab = settings.tabchi
    while True:
        clear_screen()
        console.print("[bold magenta]== TABCHI / AUTO-ADVERTISER SETTINGS ==[/bold magenta]\n")

        status_color = "green" if tab.enabled else "red"
        status_text = "ENABLED" if tab.enabled else "DISABLED"

        info_table = Table(box=box.SIMPLE, show_header=False, expand=False, width=MENU_WIDTH)
        info_table.add_column("Setting", style="bold cyan", width=24)
        info_table.add_column("Value", style="white", width=50)

        info_table.add_row("Status", f"[{status_color}]{status_text}[/{status_color}]")
        interval_desc = (
            f"{tab.min_interval_minutes:.1f} - {tab.max_interval_minutes:.1f} minutes (Randomized)"
            if tab.randomize_interval
            else f"{tab.min_interval_minutes:.1f} minutes (Fixed)"
        )
        info_table.add_row("Interval", interval_desc)
        info_table.add_row("Message Order", tab.order.capitalize())
        info_table.add_row("Anti-Duplicate Dot", "[green]ON[/green]" if tab.anti_duplicate_dot else "[red]OFF[/red]")
        info_table.add_row("Total Messages", f"{len(tab.messages)} message(s) configured")

        console.print(Panel(info_table, title="[bold]Current Tabchi Config[/bold]", border_style="magenta", width=MENU_WIDTH))

        menu_table = Table(box=box.ROUNDED, show_header=True, expand=False, width=MENU_WIDTH)
        menu_table.add_column("No.", style="bold cyan", width=6)
        menu_table.add_column("Action", style="bold white", width=28)
        menu_table.add_column("Details", style="dim", width=38)

        menu_table.add_row("[1]", "Toggle Enabled/Disabled", f"Currently {status_text}")
        menu_table.add_row("[2]", "Set Interval (Minutes)", f"{tab.min_interval_minutes:.1f} - {tab.max_interval_minutes:.1f} min")
        menu_table.add_row("[3]", "Toggle Random Interval", f"{'ON' if tab.randomize_interval else 'OFF'}")
        menu_table.add_row("[4]", "List All Messages", f"View all {len(tab.messages)} messages")
        menu_table.add_row("[5]", "Add Messages (Bulk)", "Add multiple or pipe-separated")
        menu_table.add_row("[6]", "Remove Messages (Bulk)", "Delete single, list, ranges, or all")
        menu_table.add_row("[7]", "Toggle Message Order", f"Currently: {tab.order} (cycle/random)")
        menu_table.add_row("[8]", "Toggle Anti-Duplicate Dot", f"Prepend '.' to repeat ads: {'ON' if tab.anti_duplicate_dot else 'OFF'}")
        menu_table.add_row("[0]", "<< BACK", "Return to Settings menu")

        console.print(menu_table)
        choice = _input_safe("\n[bold green]>> Select option [0-8]: [/bold green]", "0")

        if choice == "0":
            return
        elif choice == "1":
            tab.enabled = not tab.enabled
            console.print(f"[green][+] Tabchi {'enabled' if tab.enabled else 'disabled'}![/green]")
            time.sleep(0.8)
        elif choice == "2":
            tab.min_interval_minutes = _input_float(
                f"[cyan]Min Interval (minutes)[/cyan] [{tab.min_interval_minutes:.1f}]: ",
                tab.min_interval_minutes, 0.1, 1440.0,
            )
            tab.max_interval_minutes = _input_float(
                f"[cyan]Max Interval (minutes)[/cyan] [{tab.max_interval_minutes:.1f}]: ",
                tab.max_interval_minutes, 0.1, 1440.0,
            )
            if tab.min_interval_minutes > tab.max_interval_minutes:
                tab.min_interval_minutes, tab.max_interval_minutes = tab.max_interval_minutes, tab.min_interval_minutes
            console.print(f"[green][+] Interval set: {tab.min_interval_minutes:.1f} - {tab.max_interval_minutes:.1f} minutes[/green]")
            time.sleep(0.8)
        elif choice == "3":
            tab.randomize_interval = not tab.randomize_interval
            console.print(f"[green][+] Randomize interval: {'ON' if tab.randomize_interval else 'OFF'}[/green]")
            time.sleep(0.8)
        elif choice == "4":
            _list_tabchi_messages(tab)
        elif choice == "5":
            _add_tabchi_messages(tab)
        elif choice == "6":
            _remove_tabchi_messages(tab)
        elif choice == "7":
            tab.order = "random" if tab.order == "cycle" else "cycle"
            console.print(f"[green][+] Order set to: {tab.order}[/green]")
            time.sleep(0.8)
        elif choice == "8":
            tab.anti_duplicate_dot = not tab.anti_duplicate_dot
            console.print(f"[green][+] Anti-duplicate dot: {'ON' if tab.anti_duplicate_dot else 'OFF'}[/green]")
            time.sleep(0.8)


def _print_tabchi_messages_table(tab: TabchiSettings):
    """Render a clean numbered table of current messages."""
    if not tab.messages:
        console.print("[yellow]No advertisement messages configured yet.[/yellow]\n")
        return

    msg_table = Table(box=box.ROUNDED, show_header=True, expand=False, width=MENU_WIDTH)
    msg_table.add_column("No.", style="bold cyan", width=6)
    msg_table.add_column("Advertisement Message", style="bold white", width=66)

    for idx, msg in enumerate(tab.messages, 1):
        msg_table.add_row(f"[{idx}]", msg)

    console.print(msg_table)


def _list_tabchi_messages(tab: TabchiSettings):
    """Display list of all current Tabchi advertisement messages."""
    clear_screen()
    console.print("\n[bold cyan]== CURRENT TABCHI ADVERTISEMENT MESSAGES ==[/bold cyan]\n")
    _print_tabchi_messages_table(tab)
    _input_safe("\n[dim]Press Enter to continue...[/dim]")


def _add_tabchi_messages(tab: TabchiSettings):
    """
    Bulk & Multi-line message addition.
    Supports single input, pipe-separated '|', file loading, or continuous entry.
    """
    clear_screen()
    console.print("[bold magenta]== ADD TABCHI MESSAGES (BULK SUPPORTED) ==[/bold magenta]\n")
    console.print(
        Panel(
            "[bold white]Options for adding messages:[/bold white]\n"
            "  • [cyan]Continuous / Multi-line:[/cyan] Type/paste messages line by line, then press [bold green]Enter on empty line[/bold green] (or 'done').\n"
            "  • [cyan]Pipe-separated:[/cyan] Paste messages separated by '|' in one line (e.g. [dim]ad 1 | ad 2 | ad 3[/dim])\n"
            "  • [cyan]From file:[/cyan] Type 'file:path/to/ads.txt' to import all lines from a file.\n"
            "  • [cyan]Cancel:[/cyan] Enter 0 to cancel.\n",
            border_style="magenta",
            width=MENU_WIDTH,
        )
    )

    first_input = _input_safe("[bold green]>> Enter message(s) or file: [/bold green]", "").strip()
    if not first_input or first_input == "0":
        console.print("[yellow]Cancelled.[/yellow]")
        time.sleep(0.8)
        return

    # 1. File Import
    if first_input.lower().startswith("file:"):
        filepath = Path(first_input[5:].strip().strip('"\''))
        if filepath.is_file():
            try:
                lines = filepath.read_text(encoding="utf-8").splitlines()
                new_msgs = [line.strip() for line in lines if line.strip()]
                tab.messages.extend(new_msgs)
                console.print(f"[bold green][+] Successfully imported {len(new_msgs)} messages from file![/bold green]")
            except Exception as e:
                console.print(f"[red][!] Error reading file: {e}[/red]")
        else:
            console.print(f"[red][!] File not found: {filepath}[/red]")
        time.sleep(1.2)
        return

    # 2. Pipe-separated bulk input
    if "|" in first_input:
        parts = [p.strip() for p in first_input.split("|") if p.strip()]
        tab.messages.extend(parts)
        console.print(f"[bold green][+] Added {len(parts)} messages from pipe-separated line![/bold green]")
        time.sleep(1.2)
        return

    # 3. Continuous line-by-line input
    added_count = 0
    tab.messages.append(first_input)
    added_count += 1
    console.print(f"[green][+] Added message #1: '{first_input}'[/green]")
    console.print("[dim]Keep entering messages (press Enter on empty line or type 'done' to finish):[/dim]")

    while True:
        line = _input_safe(f"[cyan]Message #{len(tab.messages) + 1} (Enter to finish): [/cyan]", "").strip()
        if not line or line.lower() in ("done", "exit", "finish", "q"):
            break
        if "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            tab.messages.extend(parts)
            added_count += len(parts)
            console.print(f"[green][+] Added {len(parts)} messages![/green]")
        else:
            tab.messages.append(line)
            added_count += 1
            console.print(f"[green][+] Added: '{line}'[/green]")

    console.print(f"\n[bold green][+] Done! Added {added_count} new message(s). (Pool now has {len(tab.messages)} messages)[/bold green]")
    time.sleep(1.2)


def _remove_tabchi_messages(tab: TabchiSettings):
    """
    Remove messages from Tabchi messages list with bulk and range support.
    Supports single numbers (e.g. 3), lists (1, 3, 5), ranges (2-6), or 'all'.
    """
    if not tab.messages:
        console.print("[yellow]No messages to delete.[/yellow]")
        time.sleep(1.0)
        return

    clear_screen()
    console.print("\n[bold yellow]== REMOVE TABCHI MESSAGES ==[/bold yellow]\n")
    _print_tabchi_messages_table(tab)

    console.print(
        Panel(
            "[bold white]Deletion options:[/bold white]\n"
            "  • Single message: [cyan]3[/cyan]\n"
            "  • Multiple messages: [cyan]1, 3, 5[/cyan]\n"
            "  • Range of messages: [cyan]2-6[/cyan]\n"
            "  • Mixed: [cyan]1, 3-5, 8[/cyan]\n"
            "  • Delete ALL messages: [red]all[/red]\n"
            "  • Cancel: [cyan]0[/cyan] (or press Enter)\n",
            border_style="yellow",
            width=MENU_WIDTH,
        )
    )

    raw = _input_safe("[bold yellow]>> Enter message number(s) to delete: [/bold yellow]", "0").strip()
    if not raw or raw == "0":
        console.print("[yellow]Cancelled.[/yellow]")
        time.sleep(0.8)
        return

    if raw.lower() == "all":
        confirm = _input_bool("[bold red]Are you sure you want to DELETE ALL messages?[/bold red]", default=False)
        if confirm:
            count = len(tab.messages)
            tab.messages.clear()
            console.print(f"[bold red][+] Deleted all {count} messages![/bold red]")
        else:
            console.print("[yellow]Cancelled.[/yellow]")
        time.sleep(1.2)
        return

    # Parse numbers, commas, and ranges
    indices_to_delete = set()
    tokens = [t.strip() for t in raw.split(",") if t.strip()]
    for token in tokens:
        if "-" in token:
            parts = token.split("-", 1)
            try:
                start, end = int(parts[0]), int(parts[1])
                if start > end:
                    start, end = end, start
                for num in range(start, end + 1):
                    if 1 <= num <= len(tab.messages):
                        indices_to_delete.add(num - 1)
            except ValueError:
                pass
        else:
            try:
                num = int(token)
                if 1 <= num <= len(tab.messages):
                    indices_to_delete.add(num - 1)
            except ValueError:
                pass

    if not indices_to_delete:
        console.print("[red][!] No valid message numbers found to delete.[/red]")
        time.sleep(1.2)
        return

    # Perform deletion in reverse index order
    deleted_texts = []
    for idx in sorted(indices_to_delete, reverse=True):
        deleted_texts.append(tab.messages.pop(idx))

    console.print(f"[bold green][+] Successfully removed {len(indices_to_delete)} message(s)![/bold green]")
    for d in reversed(deleted_texts[:4]):
        console.print(f"  [dim]- Removed: '{d}'[/dim]")
    if len(deleted_texts) > 4:
        console.print(f"  [dim]... and {len(deleted_texts) - 4} more[/dim]")
    time.sleep(1.4)


def _show_full_config(settings: Settings):
    """Display all current settings in a compact, readable card layout."""
    clear_screen()
    console.print("\n[bold magenta]== FULL CONFIGURATION SUMMARY ==[/bold magenta]\n")

    # General
    gen_table = Table(box=box.SIMPLE, show_header=False, expand=False, width=MENU_WIDTH)
    gen_table.add_column("Setting", style="bold cyan", width=28)
    gen_table.add_column("Value", style="white", width=46)

    instance_label = get_active_instance_label(settings)
    gen_table.add_row("Player Username", f"[bold green]{settings.player_username}[/bold green]")
    gen_table.add_row("Minecraft Version / Log", instance_label)
    gen_table.add_row("Full Log Path", str(settings.get_active_log_path()))
    gen_table.add_row("Dry-Run Mode", "[yellow]ON[/yellow]" if settings.dry_run else "[green]OFF[/green]")
    gen_table.add_row("Require Focus", "[green]ON[/green]" if settings.require_focus else "[red]OFF[/red]")
    gen_table.add_row("Send Method", settings.send_method.upper())
    gen_table.add_row("Chat Key", settings.chat_key)
    gen_table.add_row("Server Cooldown", f"{settings.send_cooldown:.1f}s")
    gen_table.add_row("Max Retries", str(settings.max_candidate_retries))
    gen_table.add_row("Answer Ratio", f"1 of {settings.answer_ratio} ({100/settings.answer_ratio:.0f}%)")
    gen_table.add_row("Global Delays", f"{settings.global_min_delay:.1f}s - {settings.global_max_delay:.1f}s")
    gen_table.add_row("Guess Number Mode", settings.guess_number_mode)

    console.print(Panel(gen_table, title="[bold]General & Identity[/bold]", border_style="cyan", width=MENU_WIDTH))

    # Per-game delays
    gt_table = Table(box=box.SIMPLE, show_header=True, expand=False, width=MENU_WIDTH)
    gt_table.add_column("Game Type", style="bold white", width=26)
    gt_table.add_column("Status", width=14)
    gt_table.add_column("Min Delay", justify="right", width=16)
    gt_table.add_column("Max Delay", justify="right", width=16)

    for gt in GAME_TYPES:
        gd = settings.game_delays.get(gt, GameTypeDelay())
        en_style = "green" if gd.enabled else "red"
        gt_table.add_row(
            GAME_TYPE_LABELS.get(gt, gt),
            f"[{en_style}]{'ENABLED' if gd.enabled else 'DISABLED'}[/{en_style}]",
            f"{gd.min_delay:.1f}s",
            f"{gd.max_delay:.1f}s",
        )

    console.print(Panel(gt_table, title="[bold]Per Game-Type Delays[/bold]", border_style="yellow", width=MENU_WIDTH))

    # Stealth
    st = settings.stealth
    st_table = Table(box=box.SIMPLE, show_header=False, expand=False, width=MENU_WIDTH)
    st_table.add_column("Setting", style="bold cyan", width=28)
    st_table.add_column("Value", style="white", width=46)

    st_table.add_row("Fake Attempts", f"{st.fake_attempts_min} - {st.fake_attempts_max} attempts")
    st_table.add_row("Attempt Cooldown", f"{st.fake_attempt_cooldown:.1f}s")
    st_table.add_row("Typo: Nearby Keys", "[green]ON[/green]" if st.typo_nearby_keys else "[red]OFF[/red]")
    st_table.add_row("Typo: Swap Case", "[green]ON[/green]" if st.typo_swap_case else "[red]OFF[/red]")
    st_table.add_row("Typo: Partial Word", "[green]ON[/green]" if st.typo_partial_word else "[red]OFF[/red]")
    st_table.add_row("Typo: Reversed Word", "[green]ON[/green]" if st.typo_reversed_word else "[red]OFF[/red]")
    st_table.add_row("Typo: Missing Chars", "[green]ON[/green]" if st.typo_missing_chars else "[red]OFF[/red]")

    console.print(Panel(st_table, title="[bold]Anti-Cheat Stealth[/bold]", border_style="red", width=MENU_WIDTH))

    # Tabchi / Auto-Advertiser
    tab = settings.tabchi
    tab_table = Table(box=box.SIMPLE, show_header=False, expand=False, width=MENU_WIDTH)
    tab_table.add_column("Setting", style="bold cyan", width=28)
    tab_table.add_column("Value", style="white", width=46)

    tab_table.add_row("Status", "[green]ENABLED[/green]" if tab.enabled else "[red]DISABLED[/red]")
    interval_info = (
        f"{tab.min_interval_minutes:.1f} - {tab.max_interval_minutes:.1f} minutes (Randomized)"
        if tab.randomize_interval
        else f"{tab.min_interval_minutes:.1f} minutes (Fixed)"
    )
    tab_table.add_row("Interval", interval_info)
    tab_table.add_row("Order", tab.order.capitalize())
    tab_table.add_row("Anti-Duplicate Dot", "[green]ON[/green]" if tab.anti_duplicate_dot else "[red]OFF[/red]")
    tab_table.add_row("Total Messages", f"{len(tab.messages)} message(s)")
    if tab.messages:
        for idx, msg in enumerate(tab.messages[:3], 1):
            tab_table.add_row(f"  Msg #{idx}", f"[dim]{msg}[/dim]")
        if len(tab.messages) > 3:
            tab_table.add_row("  ...", f"[dim]+{len(tab.messages) - 3} more message(s)[/dim]")

    console.print(Panel(tab_table, title="[bold]Tabchi / Auto-Advertiser[/bold]", border_style="magenta", width=MENU_WIDTH))

    _input_safe("\n[dim]Press Enter to go back...[/dim]")


def run_menu(settings: Settings) -> Optional[str]:
    """
    Run the full interactive menu loop.
    Returns 'start' when user wants to start the bot, or 'exit' to quit.
    """
    while True:
        action = show_main_menu(settings)

        if action == "start":
            active_log = settings.get_active_log_path()
            # If active log does not exist or multiple instances are detected on first run, verify with user
            if not active_log.is_file():
                console.print(f"\n[bold yellow][!] Configured log file not found at: {active_log}[/bold yellow]")
                _settings_minecraft_version(settings)
            settings.save()
            return "start"
        elif action == "select_version":
            _settings_minecraft_version(settings)
            settings.save()
        elif action == "settings":
            show_settings_menu(settings)
        elif action == "exit":
            console.print("[yellow]Goodbye![/yellow]")
            return "exit"
