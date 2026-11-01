# Tabchi / Auto-Advertiser Engine Guide

MythoriaSolver includes a built-in automated advertiser ("Tabchi / تبچی") designed to promote in-game auction listings, shop items, or custom announcements on Minecraft SMP servers.

---

## 1. Scheduling & Interval Timing

The Tabchi worker operates in the background:
- **Interval Bounds:** `min_interval_minutes` to `max_interval_minutes` (e.g. 5 to 10 minutes).
- **Interval Modes:**
  - **Randomized (`randomize_interval=True`):** Picks a random duration between min and max for each cycle, preventing predictable periodicity detectable by server spam filters.
  - **Fixed:** Uses the exact interval specified.

---

## 2. Anti-Duplicate Dot / Spam Bypass Algorithm

Most Minecraft servers enforce a strict duplicate chat filter:
> *"You cannot send the same message twice in a row!"*

To circumvent this restriction without changing the meaning of your advertisement:
1. **Dot Prefix Bypass (`anti_duplicate_dot=True`):**
   - Before dispatching the advertisement, the bot sends a lone dot `.` or space.
   - Waits `dot_delay_seconds` (default: 3.5s to clear server chat cooldown).
   - Then sends the actual advertisement text.
   - Because the preceding message was `.`, the server's duplicate filter is cleared.
2. **Invisible Zero-Width Character Injection:**
   - Alternatively, injects zero-width non-joiners (ZWNJ: `\u200c`) or spaces into the text. The visual message is identical to players, but the server sees a distinct string hash.

---

## 3. Message Pool Management

- **Dispatch Orders:**
  - `cycle`: Rotates through the configured pool sequentially (1 -> 2 -> 3 -> 1).
  - `random`: Uniformly selects a random advertisement from the pool.
- **Dynamic Pool Editing:**
  - Messages can be added, deleted, or reset to defaults directly from the GUI **Tabchi Auto-Ads** tab without restarting the bot.
  - Messages persist automatically in `%APPDATA%\MythoriaSolver\settings.json`.
