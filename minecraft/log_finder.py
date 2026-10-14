"""
Minecraft Instance and Log File Detector.
Discovers Minecraft installations across standard, modpack, and custom launchers,
and allows interactive or automatic instance selection.
"""
import os
import glob
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console(safe_box=True)


@dataclass
class MinecraftInstance:
    name: str
    path: Path
    last_modified: float
    size_bytes: int

    @property
    def formatted_mtime(self) -> str:
        dt = datetime.fromtimestamp(self.last_modified)
        now = datetime.now()
        if dt.date() == now.date():
            return f"Today {dt.strftime('%H:%M:%S')}"
        elif (now - dt).days == 1:
            return f"Yesterday {dt.strftime('%H:%M:%S')}"
        else:
            return dt.strftime("%Y-%m-%d %H:%M")

    @property
    def is_recent(self) -> bool:
        """Modified in the last 24 hours."""
        return (time.time() - self.last_modified) < 86400


def detect_minecraft_logs(custom_path: Optional[str] = None) -> List[MinecraftInstance]:
    """
    Search for all valid Minecraft latest.log files on the system.
    Returns a sorted list of MinecraftInstance objects (most recently active first).
    """
    appdata = os.environ.get("APPDATA", "")
    userprofile = os.environ.get("USERPROFILE", "")

    search_patterns = [
        # Standard .minecraft
        (Path(appdata) / ".minecraft" / "logs" / "latest.log", "Default (.minecraft)"),
        # Version-specific isolated directories in .minecraft/versions/
        (Path(appdata) / ".minecraft" / "versions" / "*" / "logs" / "latest.log", ".minecraft Version: {match}"),
        # CurseForge
        (Path(userprofile) / "curseforge" / "minecraft" / "Instances" / "*" / "logs" / "latest.log", "CurseForge: {match}"),
        # Prism Launcher
        (Path(appdata) / "PrismLauncher" / "instances" / "*" / ".minecraft" / "logs" / "latest.log", "PrismLauncher: {match}"),
        (Path(appdata) / "PrismLauncher" / "instances" / "*" / "logs" / "latest.log", "PrismLauncher: {match}"),
        # Modrinth App
        (Path(appdata) / "com.modrinth.theseus" / "profiles" / "*" / "logs" / "latest.log", "Modrinth: {match}"),
        # Phoenix Launcher
        (Path(appdata) / "PhoenixLauncher" / "logs" / "latest.log", "PhoenixLauncher"),
        # Feather Client
        (Path(appdata) / ".feather" / "user-modpacks" / "*" / "logs" / "latest.log", "Feather: {match}"),
        (Path(appdata) / ".feather" / "logs" / "latest.log", "Feather Client"),
        # Badlion Client
        (Path(appdata) / ".badlion" / "logs" / "latest.log", "Badlion Client"),
        # Lunar Client
        (Path(userprofile) / ".lunarclient" / "offline" / "multiver" / "logs" / "latest.log", "Lunar Client"),
        (Path(userprofile) / ".lunarclient" / "profiles" / "*" / "logs" / "latest.log", "Lunar: {match}"),
        # MultiMC
        (Path(appdata) / "MultiMC" / "instances" / "*" / ".minecraft" / "logs" / "latest.log", "MultiMC: {match}"),
    ]

    found_map = {}

    # Check custom path if configured
    if custom_path:
        cp = Path(custom_path).expanduser().resolve()
        if cp.is_file():
            stat = cp.stat()
            found_map[str(cp).lower()] = MinecraftInstance(
                name=f"Custom: {cp.parent.parent.name if cp.parent.name == 'logs' else cp.name}",
                path=cp,
                last_modified=stat.st_mtime,
                size_bytes=stat.st_size,
            )

    for pattern_path, label_template in search_patterns:
        pattern_str = str(pattern_path)
        if "*" in pattern_str:
            for match in glob.glob(pattern_str):
                p = Path(match).resolve()
                key = str(p).lower()
                if p.is_file() and key not in found_map:
                    stat = p.stat()
                    # Extract wildcard match name from parent dir
                    match_name = p.parent.parent.name if p.parent.name == "logs" else p.parent.name
                    instance_name = label_template.replace("{match}", match_name)
                    found_map[key] = MinecraftInstance(
                        name=instance_name,
                        path=p,
                        last_modified=stat.st_mtime,
                        size_bytes=stat.st_size,
                    )
        else:
            p = pattern_path.resolve()
            key = str(p).lower()
            if p.is_file() and key not in found_map:
                stat = p.stat()
                found_map[key] = MinecraftInstance(
                    name=label_template,
                    path=p,
                    last_modified=stat.st_mtime,
                    size_bytes=stat.st_size,
                )

    instances = list(found_map.values())
    # Sort descending by last modified time (most active first)
    instances.sort(key=lambda x: x.last_modified, reverse=True)
    return instances


def prompt_select_minecraft_instance(
    instances: List[MinecraftInstance],
    current_selected_path: Optional[str] = None,
    allow_custom: bool = True,
) -> Optional[Path]:
    """
    Displays an interactive, clean selection prompt for Minecraft instances.
    """
    table = Table(box=box.ROUNDED, show_header=True, expand=False, width=78)
    table.add_column("No.", style="bold cyan", width=6)
    table.add_column("Instance / Version", style="bold white", width=36)
    table.add_column("Last Active", style="dim", width=18)
    table.add_column("Status", width=12)

    norm_current = str(Path(current_selected_path).resolve()).lower() if current_selected_path else ""

    for idx, inst in enumerate(instances, 1):
        is_current = norm_current and (str(inst.path.resolve()).lower() == norm_current)
        status_text = "[bold green]ACTIVE[/bold green]" if is_current else ("[yellow]Recent[/yellow]" if inst.is_recent else "")
        table.add_row(
            f"[{idx}]",
            inst.name[:34],
            inst.formatted_mtime,
            status_text,
        )

    if allow_custom:
        table.add_row("[C]", "Enter Custom Path...", "-", "")
    table.add_row("[0]", "<< Cancel / Keep Current", "-", "")

    console.print(Panel(table, title="[bold magenta]SELECT MINECRAFT VERSION / INSTANCE[/bold magenta]", border_style="magenta"))

    default_idx = "1"
    # If one is currently selected, find its index
    for idx, inst in enumerate(instances, 1):
        if norm_current and str(inst.path.resolve()).lower() == norm_current:
            default_idx = str(idx)
            break

    try:
        raw = console.input(f"[bold green]>> Select instance [1-{len(instances)}, C, 0] (default: [{default_idx}]): [/bold green]").strip()
    except (KeyboardInterrupt, EOFError):
        return None

    if not raw:
        raw = default_idx

    raw_lower = raw.lower()
    if raw_lower in ("0", "cancel", "q", "exit"):
        return None

    if raw_lower == "c":
        try:
            custom_input = console.input("[cyan]Enter full path to latest.log: [/cyan]").strip().strip('"\'')
            cp = Path(custom_input).expanduser().resolve()
            if cp.is_file():
                return cp
            elif cp.is_dir() and (cp / "logs" / "latest.log").is_file():
                return cp / "logs" / "latest.log"
            elif cp.is_dir() and (cp / "latest.log").is_file():
                return cp / "latest.log"
            else:
                console.print(f"[red][!] File not found at: {cp}[/red]")
                time.sleep(1.5)
                return None
        except (KeyboardInterrupt, EOFError):
            return None

    try:
        choice_idx = int(raw) - 1
        if 0 <= choice_idx < len(instances):
            return instances[choice_idx].path
    except ValueError:
        pass

    console.print("[yellow][!] Invalid selection.[/yellow]")
    time.sleep(1)
    return None
