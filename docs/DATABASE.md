# Database & Persistent Storage Guide

MythoriaSolver utilizes an embedded **SQLite** database (`database/minecraft_clean.db`) alongside a dedicated user configuration file in Windows `%APPDATA%`.

---

## 1. Storage Locations

| Data Type | File Path | Purpose |
| :--- | :--- | :--- |
| **User Settings** | `%APPDATA%\MythoriaSolver\settings.json` | Persistent user configurations, delays, player username, custom ad messages |
| **Clean Database** | `database/minecraft_clean.db` | Pre-indexed Minecraft blocks, items, mobs, and trivia Q&As |
| **Historical Logs** | `collector/chat_games.json` | Recorded games, duration statistics, and accuracy metrics |

---

## 2. SQLite Schema Design

Managed through `database/models.py`:

### Items / Vocabulary Table (`items`)
```sql
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT,          -- block, item, entity, biome, effect
    length INTEGER NOT NULL,
    signature TEXT NOT NULL -- sorted characters tuple for anagrams
);

CREATE INDEX IF NOT EXISTS idx_items_signature ON items(signature);
CREATE INDEX IF NOT EXISTS idx_items_length ON items(length);
CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);
```

- **Signature Indexing:** The `signature` column stores alphabetically sorted characters (e.g. `apple` -> `aelpp`). This allows the anagram solver to look up scrambled words with a single $O(1)$ indexed query:
  ```sql
  SELECT name FROM items WHERE signature = ?;
  ```

### Trivia Questions Table (`trivia`)
```sql
CREATE TABLE IF NOT EXISTS trivia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL UNIQUE,
    answer TEXT NOT NULL,
    category TEXT,
    confidence REAL DEFAULT 100.0,
    times_seen INTEGER DEFAULT 1,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trivia_question ON trivia(question);
```

---

## 3. Database Manager Operations (`database/models.py`)

- `DatabaseManager.get_instance()`: Thread-safe singleton providing cached access to SQLite connections.
- `DatabaseManager.all_items`: In-memory list of verified Minecraft item names loaded at boot for zero-latency in-memory pattern matching.
- `DatabaseManager.add_item(name, category)`: Inserts a newly learned word into SQLite and recalculates its signature hash.
- `DatabaseManager.add_trivia(question, answer)`: Inserts or updates trivia questions learned dynamically from server announcements.
