from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import sqlite3
import re
import threading


@dataclass(frozen=True)
class MinecraftName:
    id: int
    minecraft_id: str
    display_name: str
    normalized_name: str
    type: str

    @property
    def sorted_letters(self) -> str:
        return "".join(sorted(self.normalized_name))

    @property
    def word_count(self) -> int:
        return len(self.display_name.split())


class DatabaseManager:
    """
    High-performance in-memory cache and SQLite manager for Minecraft names.
    Preloads all entries once into specialized lookup tables for sub-millisecond solving.
    """

    _instance: Optional["DatabaseManager"] = None
    _lock = threading.Lock()

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = Path(__file__).parent / "minecraft_clean.db"
        else:
            self.db_path = Path(db_path)

        self._items: List[MinecraftName] = []
        self._by_normalized: Dict[str, MinecraftName] = {}
        self._by_sorted_letters: Dict[str, List[MinecraftName]] = {}
        self._by_word_count: Dict[int, List[MinecraftName]] = {}
        self._load_cache()

    @classmethod
    def get_instance(cls, db_path: Optional[Path] = None) -> "DatabaseManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(db_path)
            return cls._instance

    def _load_cache(self) -> None:
        if not self.db_path.exists():
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, minecraft_id, display_name, normalized_name, type
            FROM minecraft_names
            """
        )
        rows = cursor.fetchall()
        conn.close()

        items: List[MinecraftName] = []
        by_norm: Dict[str, MinecraftName] = {}
        by_sorted: Dict[str, List[MinecraftName]] = {}
        by_words: Dict[int, List[MinecraftName]] = {}

        for row in rows:
            item = MinecraftName(
                id=row[0],
                minecraft_id=row[1],
                display_name=row[2],
                normalized_name=row[3],
                type=row[4],
            )
            items.append(item)
            by_norm[item.normalized_name] = item

            # Group by sorted letters for O(1) unscramble
            sl = item.sorted_letters
            if sl not in by_sorted:
                by_sorted[sl] = []
            by_sorted[sl].append(item)

            # Group by word count for constrained search
            wc = item.word_count
            if wc not in by_words:
                by_words[wc] = []
            by_words[wc].append(item)

        self._items = items
        self._by_normalized = by_norm
        self._by_sorted_letters = by_sorted
        self._by_word_count = by_words

    @property
    def all_items(self) -> List[MinecraftName]:
        return self._items

    def find_by_normalized(self, normalized_name: str) -> Optional[MinecraftName]:
        """O(1) exact normalized name lookup."""
        return self._by_normalized.get(normalized_name)

    def find_by_sorted_letters(self, sorted_letters: str) -> List[MinecraftName]:
        """O(1) anagram / unscramble lookup."""
        return self._by_sorted_letters.get(sorted_letters, [])

    def get_items_by_word_count(self, count: int) -> List[MinecraftName]:
        return self._by_word_count.get(count, [])

    def learn_word(self, display_name: str, item_type: str = "learned") -> bool:
        """
        Dynamically learns a new Minecraft word/item, writes it to SQLite,
        and immediately updates in-memory caches without restarting.
        """
        clean_name = display_name.strip()
        if not clean_name:
            return False

        norm = re.sub(r"[^a-z0-9]", "", clean_name.lower())
        if not norm or self.find_by_normalized(norm) is not None:
            return False

        m_id = clean_name.lower().replace(" ", "_").replace("'", "")

        with self._lock:
            # Double check under lock
            if norm in self._by_normalized:
                return False

            new_id = len(self._items) + 1
            if self.db_path.exists():
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    try:
                        cursor.execute(
                            """
                            INSERT INTO minecraft_names (minecraft_id, display_name, normalized_name, type)
                            VALUES (?, ?, ?, ?)
                            """,
                            (m_id, clean_name, norm, item_type),
                        )
                        new_id = cursor.lastrowid
                        conn.commit()
                    except sqlite3.IntegrityError:
                        cursor.execute(
                            """
                            INSERT INTO minecraft_names (minecraft_id, display_name, normalized_name, type)
                            VALUES (?, ?, ?, ?)
                            """,
                            (f"{m_id}_{norm[:4]}", clean_name, norm, item_type),
                        )
                        new_id = cursor.lastrowid
                        conn.commit()
                    finally:
                        conn.close()
                except Exception:
                    pass

            new_item = MinecraftName(
                id=new_id,
                minecraft_id=m_id,
                display_name=clean_name,
                normalized_name=norm,
                type=item_type,
            )
            self._items.append(new_item)
            self._by_normalized[norm] = new_item

            sl = new_item.sorted_letters
            if sl not in self._by_sorted_letters:
                self._by_sorted_letters[sl] = []
            self._by_sorted_letters[sl].append(new_item)

            wc = new_item.word_count
            if wc not in self._by_word_count:
                self._by_word_count[wc] = []
            self._by_word_count[wc].append(new_item)

            return True

    def reload(self) -> None:
        with self._lock:
            self._load_cache()
