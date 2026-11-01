# Solvers Engine & Heuristics Guide

MythoriaSolver includes 7 specialized puzzle solvers orchestrated by `solver.router.SolverRouter`. Every solver produces a ranked list of candidate answer dictionaries with the format:
```python
{
    "answer": str,       # Normalized string ready for in-game chat dispatch
    "score": float,      # Confidence score (0.0 to 100.0)
    "solver": str,       # Identifier of the solver that generated this candidate
    "metadata": dict     # Additional contextual details (e.g. formula, distance)
}
```

---

## 1. The 7 Specialized Solvers

### 1.1 Math Solver (`solver/math_solver.py`)
- **Supported Formats:**
  - Standard arithmetic: `12 + 45`, `144 / 12`, `7 * 8`, `95 - 38`
  - Complex expressions with parentheses: `(15 + 5) * 4`, `100 - (20 * 3)`
  - Exponents and modulo: `2^5`, `100 % 7`
  - Persian / Arabic numerals: `۱۲ + ۴۵` automatically normalized to `12 + 45`.
  - Words representing operations: `plus`, `minus`, `times`, `divided by`, `ضرب`, `تقسیم`.
- **Safety Mechanism:** Uses `ast.parse` with a whitelist of permitted AST nodes (`BinOp`, `UnaryOp`, `Constant`, `Add`, `Sub`, `Mult`, `Div`, `Mod`, `Pow`). Never executes arbitrary Python strings via `eval()`.
- **Output:** Returns integer format if the result is a whole number (`42`), or rounded float if fractional (`3.14`).

### 1.2 Scramble / Anagram Solver (`solver/scramble_solver.py`)
- **Problem:** Chat displays scrambled letters, e.g.: `d i a m o n d` or `ndomaid` -> `diamond`.
- **Algorithm:**
  - Tokenizes input into lowercase letters, removing spaces and delimiters.
  - Generates a **signature hash**: `tuple(sorted(characters))`.
  - Queries `DatabaseManager.find_by_signature(signature)` for instant $O(1)$ anagram lookup across 1,200+ Minecraft items, blocks, and entities.
  - Multi-word support: Handles two-word items like `iron ingot` or `golden apple`.

### 1.3 Reverse Solver (`solver/reverse_solver.py`)
- **Problem:** Chat displays backwards text, e.g.: `kcipdnomaid` or `l o o p`.
- **Algorithm:**
  - Cleans extra spaces between characters.
  - Inverts Unicode string: `s[::-1]`.
  - If the inverted word matches a verified item in the database, confidence is boosted to 100.0.

### 1.4 Trivia Solver (`solver/trivia_solver.py`)
- **Problem:** Minecraft trivia questions, e.g.: `"What tool is used to mine obsidian?"` -> `"diamond pickaxe"`.
- **Matching Pipeline:**
  1. **Exact Lookup:** Normalized question string matching in SQLite trivia table.
  2. **Levenshtein Fuzzy Match:** Uses `rapidfuzz.fuzz.token_sort_ratio` against all known trivia questions.
  3. **Thresholding:** Matches with score $\ge 85.0$ are accepted. The top candidate receives highest priority.
- **Dynamic Caching:** Pre-loads frequently asked questions into memory on startup for instant zero-disk lookups.

### 1.5 Number Guessing Solver (`solver/number_solver.py`)
- **Problem:** `"Guess a number between 1 and 50"`.
- **Configurable Strategies:**
  - `binary_search`: Selects median of remaining possible numbers $(min + max) // 2$.
  - `all`: Sequentially submits every number in the range respecting cooldowns.
  - `random`: Uniformly selects a random unpicked number in range.
  - `single`: Submits one educated guess and waits.
- **Adaptive Pool:** Monitors other players' failed guesses in chat and prunes those numbers from the pool.

### 1.6 Fill-in-the-Blank Solver (`solver/fill_solver.py`)
- **Problem:** Masked words with underscores or dashes, e.g.: `c_w` -> `cow`, `d_am_nd` -> `diamond`.
- **Algorithm:**
  - Converts blanks (`_`, `.`, `*`, `-`) into regex wildcards: `r"^c[a-z]w$"`.
  - Filters database vocabulary by exact string length first.
  - Evaluates regex pattern against length-matching candidates.

### 1.7 Equation Solver
- Linear algebraic expressions: `x + 15 = 40`, `3 * x = 27`.
- Evaluates the isolate variable $x$ by parsing left-hand and right-hand expressions.

---

## 2. Solver Router (`solver/router.py`)

The `SolverRouter` serves as the central brain dispatching queries to individual engines:
1. **Type Detection:**
   - Detects whether a question is `math`, `scramble`, `reverse`, `trivia`, `number`, or `fill` using regex signatures.
   - If the server announces the game type explicitly in the chat header, the router uses that tag directly.
2. **Fallback Cascading:**
   - If the primary detected solver yields no candidates, the router cascades through secondary solvers. For example, a single scrambled word might also be tested as a reversed word or fill-in-the-blank pattern.
3. **Multi-Candidate Scoring:**
   - Returns top-N candidates sorted by confidence score.

---

## 3. Self-Learning Engine

When enabled in settings (`auto_learn_words=True`):
- Whenever the server announces a winner and displays the correct answer:
  ```
  [Chat] Player notch won the game! The answer was: Netherite Ingot!
  ```
- The bot extracts `Netherite Ingot` and:
  1. Checks minimum length threshold (`auto_learn_min_length >= 3`).
  2. Runs the **Anti-Bot Noise Filter** (`looks_like_random_string`):
     - Prevents memorizing honeypot/anti-cheat random strings like `zK9xP2`.
     - Analyzes vowel-to-consonant ratios, entropy, and uppercase/lowercase chaos.
  3. Automatically inserts valid new words and trivia Q&As into `DatabaseManager`.
  4. Subsequent occurrences of that question will immediately resolve with 100% accuracy.
