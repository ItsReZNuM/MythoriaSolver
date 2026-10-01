import sqlite3
import re
import os
import glob
import gzip
from pathlib import Path
from typing import Set, Dict, Tuple

BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "database"
BLOCKS_FILE = BASE_DIR / "minecraft_names" / "blocks.txt"
ITEMS_FILE = BASE_DIR / "minecraft_names" / "items.txt"
OUTPUT_DB = DB_DIR / "minecraft_clean.db"

# Words that should remain lowercase in Minecraft titles unless at index 0
LOWERCASE_WORDS = {"of", "with", "the", "and", "in", "on", "at", "to", "for", "from", "by"}

# State/texture suffixes to ignore when generating real item/block names
IGNORE_SUFFIXES = [
    "_inventory",
    "_pressed",
    "_top",
    "_bottom",
    "_left",
    "_right",
    "_open",
    "_closed",
    "_side",
    "_particle",
    "_stage",
    "_horizontal",
    "_inner",
    "_outer",
    "_unconnected",
    "_unpowered",
    "_powered",
    "_on",
    "_post",
    "_tall",
    "_raised_ne",
    "_raised_sw",
    "_front",
    "_back",
    "_down",
    "_up",
]

# Standard Minecraft entities & mobs
MINECRAFT_MOBS = [
    "allay", "armadillo", "axolotl", "bat", "bee", "blaze", "bogged", "breeze",
    "camel", "cat", "cave_spider", "chicken", "cod", "cow", "creaking", "creeper",
    "dolphin", "donkey", "drowned", "elder_guardian", "ender_dragon", "enderman",
    "endermite", "evoker", "fox", "frog", "ghast", "giant", "glow_squid", "goat",
    "guardian", "hoglin", "horse", "husk", "illusioner", "iron_golem", "llama",
    "magma_cube", "mooshroom", "mule", "ocelot", "panda", "parrot", "phantom",
    "pig", "piglin", "piglin_brute", "pillager", "polar_bear", "pufferfish", "rabbit",
    "ravager", "salmon", "sheep", "shulker", "silverfish", "skeleton", "skeleton_horse",
    "slime", "sniffer", "snow_golem", "spider", "squid", "stray", "strider",
    "tadpole", "trader_llama", "tropical_fish", "turtle", "vex", "villager",
    "vindicator", "wandering_trader", "warden", "witch", "wither", "wither_skeleton",
    "wolf", "zoglin", "zombie", "zombie_horse", "zombie_villager", "zombified_piglin"
]


def normalize_name(text: str) -> str:
    """Normalize text for indexed search: lowercase, alphanumeric only."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def convert_identifier_to_display_name(identifier: str) -> str:
    """
    Convert a Minecraft identifier (e.g. nether_brick_slab) to standard display name.
    Preserves proper title casing and lowercase minor words.
    """
    raw = identifier.replace("_o_lantern", "_o'lantern").replace("_o_enchanting", "_o'enchanting")
    words = raw.split("_")
    formatted = []
    for i, w in enumerate(words):
        if not w:
            continue
        if "'" in w:
            parts = w.split("'", 1)
            w = parts[0].capitalize() + " o'" + parts[1].capitalize() if parts[0].lower() == "jack" else parts[0].capitalize() + "'" + parts[1].capitalize()
        elif i > 0 and w.lower() in LOWERCASE_WORDS:
            w = w.lower()
        else:
            w = w.capitalize()
        formatted.append(w)
    return " ".join(formatted)


def should_ignore_identifier(ident: str) -> bool:
    """Check if identifier represents an internal rendering state rather than a real name."""
    ident_lower = ident.lower()
    if ident_lower.endswith(".mcmeta") or "." in ident_lower:
        return True
    for sfx in IGNORE_SUFFIXES:
        if ident_lower.endswith(sfx):
            return True
    # Digits like age0, stage0, etc.
    if re.search(r"(_age\d+|_stage\d+|\d+)$", ident_lower) and not ident_lower in {"c418", "13", "5", "11"}:
        return True
    return False


def collect_server_log_words() -> Set[str]:
    """Scan available Minecraft log files (including gzip archives) to extract verified words."""
    words = set()
    log_dir = Path(os.path.expandvars(r"%APPDATA%\.minecraft\logs"))
    if not log_dir.exists():
        return words

    files = list(log_dir.glob("*.log.gz"))
    latest_log = log_dir / "latest.log"
    if latest_log.exists():
        files.append(latest_log)

    for fpath in files:
        try:
            if fpath.suffix == ".gz":
                with gzip.open(fpath, "rt", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            else:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

            for w in re.findall(r"The word was:\s*(.*?)\s*◀", content):
                cleaned = w.strip()
                # Exclude obvious random strings (like 84H2heqtC)
                if cleaned and " " in cleaned or cleaned in {"Cow", "Bee", "Witch", "Snowball"}:
                    words.add(cleaned)
        except Exception:
            continue

    return words


def build_clean_database(db_path: Path = OUTPUT_DB) -> int:
    """Builds clean, indexed SQLite database with blocks, items, mobs, and verified words."""
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS minecraft_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            minecraft_id TEXT UNIQUE,
            display_name TEXT,
            normalized_name TEXT,
            type TEXT
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_normalized ON minecraft_names(normalized_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_display ON minecraft_names(display_name)")

    # Dictionary: normalized_name -> (minecraft_id, display_name, item_type)
    collected: Dict[str, Tuple[str, str, str]] = {}

    def add_entry(m_id: str, display: str, itype: str):
        norm = normalize_name(display)
        if not norm:
            return
        if norm not in collected:
            collected[norm] = (m_id, display, itype)

    # 1. Import Blocks
    if BLOCKS_FILE.exists():
        with open(BLOCKS_FILE, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                raw = line.strip()
                if not raw or should_ignore_identifier(raw):
                    continue
                display = convert_identifier_to_display_name(raw)
                add_entry(raw, display, "block")

    # 2. Import Items
    if ITEMS_FILE.exists():
        with open(ITEMS_FILE, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                raw = line.strip()
                if not raw or should_ignore_identifier(raw):
                    continue
                display = convert_identifier_to_display_name(raw)
                add_entry(raw, display, "item")

    # 3. Import Mobs and Entities
    for mob in MINECRAFT_MOBS:
        display = convert_identifier_to_display_name(mob)
        add_entry(mob, display, "entity")

    # 4. Import Verified Words from Server Logs
    log_words = collect_server_log_words()
    for w in log_words:
        m_id = w.lower().replace(" ", "_").replace("'", "")
        add_entry(m_id, w, "server_verified")

    # Insert all entries
    inserted = 0
    for norm, (m_id, display, itype) in collected.items():
        try:
            cursor.execute(
                """
                INSERT INTO minecraft_names (minecraft_id, display_name, normalized_name, type)
                VALUES (?, ?, ?, ?)
                """,
                (m_id, display, norm, itype),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            # Fallback if m_id collides
            try:
                cursor.execute(
                    """
                    INSERT INTO minecraft_names (minecraft_id, display_name, normalized_name, type)
                    VALUES (?, ?, ?, ?)
                    """,
                    (f"{m_id}_{norm[:4]}", display, norm, itype),
                )
                inserted += 1
            except Exception:
                pass

    conn.commit()
    conn.close()
    return inserted


if __name__ == "__main__":
    count = build_clean_database()
    print(f"Successfully built minecraft_clean.db with {count} unique entries.")