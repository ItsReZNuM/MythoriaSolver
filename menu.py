"""
Game-style interactive TUI menu for Minecraft Chat Game Bot.
Start / Settings / Exit with full configuration sub-menus.
"""
import sys
import os
from typing import Optional, Callable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from rich.columns import Columns

from settings import Settings, GAME_TYPES, GAME_TYPE_LABELS, GameTypeDelay, StealthSettings

console = Console(safe_box=True)


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


def show_main_menu(settings: Settings) -> str:
    """Show the main menu. Returns 'start', 'settings', or 'exit'."""
    clear_screen()
    console.print(f"[bold magenta]{LOGO}[/bold magenta]")
    console.print(
        Panel(
            "[bold white]Minecraft SMP Chat Game Auto-Solver[/bold white]\n"
            f"[dim]Player: [bold cyan]{settings.player_username}[/bold cyan] | "
            f"Mode: [bold {'yellow' if settings.dry_run else 'green'}]"
            f"{'DRY-RUN' if settings.dry_run else 'LIVE'}[/bold {'yellow' if settings.dry_run else 'green'}][/dim]",
            border_style="magenta",
            padding=(0, 2),
        )
    )

    menu_items = Table(box=None, show_header=False, padding=(0, 4))
    menu_items.add_column("Key", style="bold green", width=6)
    menu_items.add_column("Label", style="bold white")

    menu_items.add_row("[1]", ">> START BOT")
    menu_items.add_row("[2]", ">> SETTINGS")
    menu_items.add_row("[3]", ">> EXIT")

    console.print(Panel(menu_items, title="[bold cyan]MAIN MENU[/bold cyan]", border_style="cyan", padding=(1, 2)))
    choice = _input_safe("[bold green]>> Select option [1-3]: [/bold green]", "1")

    if choice == "1":
        return "start"
    elif choice == "2":
        return "settings"
    elif choice == "3":
        return "exit"
    return "start"


def show_settings_menu(settings: Settings):
    """Settings sub-menu with all configuration categories."""
    while True:
        clear_screen()
        console.print("[bold magenta]== SETTINGS ==[/bold magenta]\n")

        cat_table = Table(box=box.ROUNDED, show_header=True, expand=True)
        cat_table.add_column("#", style="bold cyan", width=4)
        cat_table.add_column("Category", style="bold white")
        cat_table.add_column("Summary", style="dim")

        cat_table.add_row("1", "General", f"Mode: {'DRY-RUN' if settings.dry_run else 'LIVE'} | Focus: {'ON' if settings.require_focus else 'OFF'} | Method: {settings.send_method}")
        cat_table.add_row("2", "Delays (Global)", f"Min: {settings.global_min_delay:.1f}s | Max: {settings.global_max_delay:.1f}s")
        cat_table.add_row("3", "Delays (Per Game Type)", f"{sum(1 for gt in GAME_TYPES if settings.game_delays.get(gt, GameTypeDelay()).enabled)}/{len(GAME_TYPES)} game types enabled")
        cat_table.add_row("4", "Answer Ratio", f"1 of every {settings.answer_ratio} games ({100/settings.answer_ratio:.0f}%)")
        cat_table.add_row("5", "Anti-Cheat (Fake Attempts)", f"Min: {settings.stealth.fake_attempts_min} | Max: {settings.stealth.fake_attempts_max} wrong attempts")
        cat_table.add_row("6", "Auto-Learning", f"{'ON' if settings.auto_learn_words else 'OFF'} | Filter Random: {'ON' if settings.auto_learn_filter_random else 'OFF'}")
        cat_table.add_row("7", "View All Settings", "Show full config summary")
        cat_table.add_row("0", "<< BACK", "Return to main menu")

        console.print(cat_table)
        choice = _input_safe("\n[bold green]>> Select category [0-7]: [/bold green]", "0")

        if choice == "0":
            settings.save()
            console.print("[green][+] Settings saved![/green]")
            return
        elif choice == "1":
            _settings_general(settings)
        elif choice == "2":
            _settings_global_delays(settings)
        elif choice == "3":
            _settings_per_game_delays(settings)
        elif choice == "4":
            _settings_ratio(settings)
        elif choice == "5":
            _settings_stealth(settings)
        elif choice == "6":
            _settings_learning(settings)
        elif choice == "7":
            _show_full_config(settings)


def _settings_general(settings: Settings):
    """General settings: dry_run, focus, send_method, chat_key, cooldown."""
    console.print("\n[bold cyan]-- General Settings --[/bold cyan]\n")

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

    settings.player_username = _input_safe(
        f"[cyan]Player Username[/cyan] [{settings.player_username}]: ",
        settings.player_username,
    )

    console.print("[green][+] General settings updated.[/green]\n")


def _settings_global_delays(settings: Settings):
    """Global delay configuration."""
    console.print("\n[bold cyan]-- Global Delay Settings --[/bold cyan]")
    console.print("[dim]These are used as fallback when per-game-type delay is not set.[/dim]\n")

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

    console.print(f"[green][+] Global delays: {settings.global_min_delay:.1f}s - {settings.global_max_delay:.1f}s[/green]\n")


def _settings_per_game_delays(settings: Settings):
    """Per-game-type delay and enable/disable settings."""
    while True:
        console.print("\n[bold cyan]-- Per Game Type Delays --[/bold cyan]\n")

        gt_table = Table(box=box.ROUNDED, show_header=True, expand=True)
        gt_table.add_column("#", style="bold cyan", width=4)
        gt_table.add_column("Game Type", style="bold white", width=22)
        gt_table.add_column("Enabled", style="bold", width=10)
        gt_table.add_column("Min Delay", justify="right", width=10)
        gt_table.add_column("Max Delay", justify="right", width=10)

        for idx, gt in enumerate(GAME_TYPES, 1):
            gd = settings.game_delays.get(gt, GameTypeDelay())
            en_style = "green" if gd.enabled else "red"
            gt_table.add_row(
                str(idx),
                GAME_TYPE_LABELS.get(gt, gt),
                f"[{en_style}]{'ON' if gd.enabled else 'OFF'}[/{en_style}]",
                f"{gd.min_delay:.1f}s",
                f"{gd.max_delay:.1f}s",
            )

        gt_table.add_row("0", "<< BACK", "", "", "")
        console.print(gt_table)

        choice = _input_safe("[bold green]>> Select game type to edit [0-7]: [/bold green]", "0")
        if choice == "0":
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(GAME_TYPES):
                gt = GAME_TYPES[idx]
                _edit_game_type_delay(settings, gt)
        except ValueError:
            pass


def _edit_game_type_delay(settings: Settings, gt: str):
    """Edit a single game type's delay/enabled settings."""
    gd = settings.game_delays.get(gt, GameTypeDelay())
    label = GAME_TYPE_LABELS.get(gt, gt)

    console.print(f"\n[bold cyan]Editing: {label}[/bold cyan]\n")

    gd.enabled = _input_bool(f"[cyan]Enable this game type[/cyan]", gd.enabled)

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

    settings.game_delays[gt] = gd
    console.print(f"[green][+] {label} updated.[/green]")


def _settings_ratio(settings: Settings):
    """Answer ratio configuration."""
    console.print("\n[bold cyan]-- Answer Ratio --[/bold cyan]")
    console.print("[dim]1 = answer all games, 3 = answer 1 of every 3 games[/dim]\n")

    settings.answer_ratio = _input_int(
        f"[cyan]Answer 1 of every N games[/cyan] [{settings.answer_ratio}]: ",
        settings.answer_ratio, 1, 100,
    )
    pct = 100.0 / settings.answer_ratio
    console.print(f"[green][+] Will answer {pct:.0f}% of games (1 of {settings.answer_ratio}).[/green]\n")


def _settings_stealth(settings: Settings):
    """Anti-cheat fake wrong attempt configuration."""
    st = settings.stealth
    console.print("\n[bold cyan]-- Anti-Cheat: Fake Wrong Attempts --[/bold cyan]")
    console.print("[dim]Send deliberate wrong answers before the correct one to look human.[/dim]\n")

    st.fake_attempts_min = _input_int(
        f"[cyan]Minimum fake wrong attempts[/cyan] [{st.fake_attempts_min}]: ",
        st.fake_attempts_min, 0, 5,
    )
    st.fake_attempts_max = _input_int(
        f"[cyan]Maximum fake wrong attempts[/cyan] [{st.fake_attempts_max}]: ",
        st.fake_attempts_max, 0, 5,
    )
    if st.fake_attempts_min > st.fake_attempts_max:
        st.fake_attempts_min, st.fake_attempts_max = st.fake_attempts_max, st.fake_attempts_min

    st.fake_attempt_cooldown = _input_float(
        f"[cyan]Cooldown between attempts (seconds)[/cyan] [{st.fake_attempt_cooldown:.1f}]: ",
        st.fake_attempt_cooldown, 1.0, 30.0,
    )

    console.print("\n[bold]Fake Answer Strategies:[/bold]")
    st.typo_nearby_keys = _input_bool("[cyan]  Nearby keyboard key typos[/cyan]", st.typo_nearby_keys)
    st.typo_swap_case = _input_bool("[cyan]  Swap first letter case[/cyan]", st.typo_swap_case)
    st.typo_partial_word = _input_bool("[cyan]  Send partial word[/cyan]", st.typo_partial_word)
    st.typo_reversed_word = _input_bool("[cyan]  Reverse a word[/cyan]", st.typo_reversed_word)
    st.typo_missing_chars = _input_bool("[cyan]  Drop random characters[/cyan]", st.typo_missing_chars)

    settings.stealth = st

    if st.fake_attempts_max > 0:
        console.print(
            f"\n[green][+] Will send {st.fake_attempts_min}-{st.fake_attempts_max} "
            f"wrong attempts before correct answer, "
            f"with {st.fake_attempt_cooldown:.1f}s cooldown each.[/green]\n"
        )
    else:
        console.print("[yellow][+] Fake wrong attempts disabled (max = 0).[/yellow]\n")


def _settings_learning(settings: Settings):
    """Auto-learn configuration."""
    console.print("\n[bold cyan]-- Auto-Learning Settings --[/bold cyan]\n")

    settings.auto_learn_words = _input_bool(
        "[cyan]Auto-learn new words from server[/cyan]", settings.auto_learn_words
    )
    if settings.auto_learn_words:
        settings.auto_learn_min_length = _input_int(
            f"[cyan]Minimum word length to learn[/cyan] [{settings.auto_learn_min_length}]: ",
            settings.auto_learn_min_length, 1, 50,
        )
        settings.auto_learn_filter_random = _input_bool(
            "[cyan]Filter out random strings (e.g. 'OnpjAm')[/cyan]",
            settings.auto_learn_filter_random,
        )
    console.print("[green][+] Learning settings updated.[/green]\n")


def _show_full_config(settings: Settings):
    """Display all current settings in a readable format."""
    console.print("\n[bold magenta]== FULL CONFIGURATION ==[/bold magenta]\n")

    # General
    gen_table = Table(box=box.SIMPLE, show_header=False, expand=True)
    gen_table.add_column("Setting", style="bold cyan", width=30)
    gen_table.add_column("Value", style="white")

    gen_table.add_row("Player Username", settings.player_username)
    gen_table.add_row("Dry-Run Mode", "[yellow]ON[/yellow]" if settings.dry_run else "[green]OFF[/green]")
    gen_table.add_row("Require Focus", "[green]ON[/green]" if settings.require_focus else "[red]OFF[/red]")
    gen_table.add_row("Send Method", settings.send_method.upper())
    gen_table.add_row("Chat Key", settings.chat_key)
    gen_table.add_row("Server Cooldown", f"{settings.send_cooldown:.1f}s")
    gen_table.add_row("Max Retries", str(settings.max_candidate_retries))
    gen_table.add_row("Answer Ratio", f"1 of {settings.answer_ratio} ({100/settings.answer_ratio:.0f}%)")
    gen_table.add_row("Global Min Delay", f"{settings.global_min_delay:.1f}s")
    gen_table.add_row("Global Max Delay", f"{settings.global_max_delay:.1f}s")
    gen_table.add_row("Guess Number Mode", settings.guess_number_mode)

    console.print(Panel(gen_table, title="[bold]General[/bold]", border_style="cyan"))

    # Per-game delays
    gt_table = Table(box=box.SIMPLE, show_header=True, expand=True)
    gt_table.add_column("Game Type", style="bold white", width=22)
    gt_table.add_column("Enabled", width=8)
    gt_table.add_column("Min Delay", justify="right", width=10)
    gt_table.add_column("Max Delay", justify="right", width=10)

    for gt in GAME_TYPES:
        gd = settings.game_delays.get(gt, GameTypeDelay())
        en_style = "green" if gd.enabled else "red"
        gt_table.add_row(
            GAME_TYPE_LABELS.get(gt, gt),
            f"[{en_style}]{'ON' if gd.enabled else 'OFF'}[/{en_style}]",
            f"{gd.min_delay:.1f}s",
            f"{gd.max_delay:.1f}s",
        )

    console.print(Panel(gt_table, title="[bold]Per Game-Type Delays[/bold]", border_style="yellow"))

    # Stealth
    st = settings.stealth
    st_table = Table(box=box.SIMPLE, show_header=False, expand=True)
    st_table.add_column("Setting", style="bold cyan", width=30)
    st_table.add_column("Value", style="white")

    st_table.add_row("Fake Attempts", f"{st.fake_attempts_min} - {st.fake_attempts_max}")
    st_table.add_row("Attempt Cooldown", f"{st.fake_attempt_cooldown:.1f}s")
    st_table.add_row("Typo: Nearby Keys", "[green]ON[/green]" if st.typo_nearby_keys else "[red]OFF[/red]")
    st_table.add_row("Typo: Swap Case", "[green]ON[/green]" if st.typo_swap_case else "[red]OFF[/red]")
    st_table.add_row("Typo: Partial Word", "[green]ON[/green]" if st.typo_partial_word else "[red]OFF[/red]")
    st_table.add_row("Typo: Reversed Word", "[green]ON[/green]" if st.typo_reversed_word else "[red]OFF[/red]")
    st_table.add_row("Typo: Missing Chars", "[green]ON[/green]" if st.typo_missing_chars else "[red]OFF[/red]")

    console.print(Panel(st_table, title="[bold]Anti-Cheat Stealth[/bold]", border_style="red"))

    # Learning
    lr_table = Table(box=box.SIMPLE, show_header=False, expand=True)
    lr_table.add_column("Setting", style="bold cyan", width=30)
    lr_table.add_column("Value", style="white")

    lr_table.add_row("Auto-Learn Words", "[green]ON[/green]" if settings.auto_learn_words else "[red]OFF[/red]")
    lr_table.add_row("Min Length", str(settings.auto_learn_min_length))
    lr_table.add_row("Filter Random Strings", "[green]ON[/green]" if settings.auto_learn_filter_random else "[red]OFF[/red]")

    console.print(Panel(lr_table, title="[bold]Auto-Learning[/bold]", border_style="green"))

    _input_safe("\n[dim]Press Enter to go back...[/dim]")


def run_menu(settings: Settings) -> Optional[str]:
    """
    Run the full interactive menu loop.
    Returns 'start' when user wants to start the bot, or 'exit' to quit.
    """
    while True:
        action = show_main_menu(settings)

        if action == "start":
            settings.save()
            return "start"
        elif action == "settings":
            show_settings_menu(settings)
        elif action == "exit":
            console.print("[yellow]Goodbye![/yellow]")
            return "exit"
