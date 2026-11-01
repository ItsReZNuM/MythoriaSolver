# Stealth & Anti-Cheat Evasion Guide

To avoid detection by server anti-cheat plugins and heuristic monitoring (e.g. GrimAC, Vulcan, or custom chat analytics looking for instant, robotic answers), MythoriaSolver implements several layers of human behavior simulation.

---

## 1. Human Reaction Delays & Jittering

Server admins monitor chat timing anomalies. A bot answering in 50ms consistently will be banned.

- **Per-Game-Type Delays:** Each puzzle type has customized minimum and maximum wait times (e.g. Math might take 4-7 seconds for a human, while Unscramble might take 2-4 seconds).
- **Gaussian / Uniform Sampling:**
  ```python
  delay = random.uniform(gd.min_delay, gd.max_delay)
  ```
- **Interruption Check:** During the wait sleep, the bot checks every 50ms if another player in chat has already answered the question. If someone else wins, the bot immediately cancels its pending send, avoiding embarrassing late answers.

---

## 2. Plausible Human Mistake Simulation (`plan_fake_attempts`)

Real players frequently make typos when rushing to win chat games. MythoriaSolver can deliberately submit 0-2 plausible mistakes before the true answer.

### Flow:
1. `fake_attempts_min` to `fake_attempts_max` (configurable, e.g. 0 to 2).
2. If `fake_count > 0`:
   - Generates slightly corrupted versions of the true answer.
   - Submits `fake_attempt_1` to chat.
   - Waits for server cooldown (default: 3.0s).
   - Repeats if `fake_count == 2`.
   - Finally submits the true, correct answer.

---

## 3. Physical QWERTY Neighbor Key Matrix

Typos are not completely random; they follow physical keyboard adjacency. `stealth.py` defines a physical QWERTY matrix:

```python
ADJACENT_KEYS = {
    'a': ['q', 'w', 's', 'z'],
    'b': ['v', 'g', 'h', 'n'],
    'c': ['x', 'd', 'f', 'v'],
    'd': ['s', 'e', 'r', 'f', 'c', 'x'],
    'e': ['w', 's', 'd', 'r'],
    ...
}
```

### The 5 Typo Patterns:
1. **Adjacent Key Slip (`typo_nearby_keys`):**
   - Swaps a letter for its neighbor on a standard QWERTY keyboard (e.g. `diamond` -> `siamond` or `dismond`).
2. **Initial Case Swap (`typo_swap_case`):**
   - Accidentally types with CapsLock or Shift (e.g. `Diamond` -> `dIAMOND`).
3. **Partial Word Submission (`typo_partial_word`):**
   - Inadvertently hits Enter before finishing typing (e.g. `diamond` -> `diam`).
4. **Character Pair Inversion (`typo_reversed_word`):**
   - Swaps two adjacent letters due to fast finger timing (e.g. `diamond` -> `daimond`).
5. **Dropped Letter (`typo_missing_chars`):**
   - Misses a character while typing at high speed (e.g. `diamond` -> `dimond`).

---

## 4. Anti-Bot Noise & Honeypot Detection (`looks_like_random_string`)

Some Minecraft servers generate anti-bot honeypots: questions where the expected answer is a randomly generated string of noise (e.g. `x7KpQ9z`).

If the bot learns this into its database, it pollutes the dictionary. The `looks_like_random_string` function evaluates:
1. **Length Anomalies:** Abnormally long character sequences without word boundaries.
2. **Vowel-to-Consonant Ratio:** Genuine English and Minecraft names have balanced vowel distributions (typically 25% - 50%). Strings with 0 vowels or 80% consonants are flagged.
3. **Digit/Special Symbol Entropy:** Mixed alphanumeric strings like `a9B8c7` are identified as high-entropy honeypots and rejected from auto-learning.
