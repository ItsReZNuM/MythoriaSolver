import random
from typing import List


# QWERTY keyboard neighbor map for typo simulation
KEYBOARD_NEIGHBORS = {
    'a': 'sqwz', 'b': 'vghn', 'c': 'xdfv', 'd': 'sfecx', 'e': 'wrsdf',
    'f': 'dgrtcv', 'g': 'fhtyb', 'h': 'gjyun', 'i': 'ujko', 'j': 'hkunm',
    'k': 'jloi', 'l': 'kop', 'm': 'njk', 'n': 'bhjm', 'o': 'iklp',
    'p': 'ol', 'q': 'wa', 'r': 'edft', 's': 'adwxz', 't': 'rfgy',
    'u': 'yhji', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tghu',
    'z': 'asx',
}


def _nearby_key(char: str) -> str:
    """Replace a character with a nearby keyboard key."""
    lower = char.lower()
    if lower in KEYBOARD_NEIGHBORS:
        neighbors = KEYBOARD_NEIGHBORS[lower]
        replacement = random.choice(neighbors)
        return replacement if char.islower() else replacement.upper()
    return char


def generate_typo_answer(correct_answer: str) -> str:
    """Generate a plausible typo version of the correct answer."""
    if len(correct_answer) <= 1:
        return correct_answer.lower()

    strategies = ["nearby_keys", "swap_case", "partial", "reversed_word", "missing_chars"]
    strategy = random.choice(strategies)

    if strategy == "nearby_keys":
        chars = list(correct_answer)
        n_corrupt = random.randint(1, min(2, len(chars) - 1))
        alpha_positions = [i for i, c in enumerate(chars) if c.isalpha()]
        if not alpha_positions:
            return correct_answer.lower()
        positions = random.sample(alpha_positions, min(n_corrupt, len(alpha_positions)))
        for pos in positions:
            chars[pos] = _nearby_key(chars[pos])
        return "".join(chars)

    elif strategy == "swap_case":
        if correct_answer[0].isupper():
            return correct_answer[0].lower() + correct_answer[1:]
        else:
            return correct_answer

    elif strategy == "partial":
        cut = max(2, int(len(correct_answer) * random.uniform(0.4, 0.7)))
        return correct_answer[:cut]

    elif strategy == "reversed_word":
        words = correct_answer.split()
        if len(words) > 1:
            idx = random.randint(0, len(words) - 1)
            words[idx] = words[idx][::-1]
            return " ".join(words)
        else:
            return correct_answer[::-1]

    elif strategy == "missing_chars":
        chars = list(correct_answer)
        alpha_positions = [i for i, c in enumerate(chars) if c.isalpha()]
        if len(alpha_positions) <= 1:
            return correct_answer.lower()
        n_drop = random.randint(1, max(1, len(alpha_positions) // 4))
        to_drop = sorted(
            random.sample(alpha_positions, min(n_drop, len(alpha_positions) - 1)),
            reverse=True,
        )
        for pos in to_drop:
            chars.pop(pos)
        return "".join(chars)

    return correct_answer


def plan_fake_attempts(correct_answer: str, stealth_cfg) -> List[str]:
    """
    Plan the sequence of fake wrong messages to send before the correct answer.
    Returns a list of wrong answer strings (may be empty if 0 attempts chosen).
    """
    n_fakes = random.randint(stealth_cfg.fake_attempts_min, stealth_cfg.fake_attempts_max)

    if n_fakes <= 0:
        return []

    fakes = []
    seen = {correct_answer.lower()}
    for _ in range(n_fakes):
        for _attempt in range(10):  # retry to avoid duplicates
            fake = generate_typo_answer(correct_answer)
            if fake.lower() not in seen and fake.lower() != correct_answer.lower():
                seen.add(fake.lower())
                fakes.append(fake)
                break
        else:
            # Fallback: just lowercase it
            fallback = correct_answer.lower()
            if fallback not in seen:
                fakes.append(fallback)

    return fakes


def looks_like_random_string(text: str) -> bool:
    """
    Heuristic: detect random-looking strings that shouldn't be learned.
    Examples of random: 'OnpjAm', '84H2heqtC', 'SWGihXI'
    Examples of real: 'Dead Bush', 'Nether Brick Slab', 'Cow'
    """
    clean = text.strip()
    if not clean:
        return True

    # If it contains spaces, it's likely a real Minecraft name
    if " " in clean:
        words = clean.split()
        for w in words:
            if not _is_title_case_word(w) and not w.islower() and not w.isupper():
                if "'" not in w:
                    return True
        return False

    # Single word: check patterns
    # Pure digits = not a name
    if clean.isdigit():
        return True

    # Standard Title Case single word like "Cow", "Witch", "Bee" = valid
    if clean[0].isupper() and (len(clean) == 1 or clean[1:].islower()):
        return False

    # Short all-caps = likely random
    if clean.isupper() and len(clean) <= 5:
        return True

    # Mixed case single word without standard title-case = random
    if any(c.isupper() for c in clean[1:]) and any(c.islower() for c in clean):
        if not clean.istitle():
            return True

    # Contains digits mixed with letters = random
    has_digit = any(c.isdigit() for c in clean)
    has_alpha = any(c.isalpha() for c in clean)
    if has_digit and has_alpha:
        return True

    return False


def _is_title_case_word(word: str) -> bool:
    """Check if word follows Title Case or is a minor word."""
    minor_words = {"of", "with", "the", "and", "in", "on", "at", "to", "for", "from", "by"}
    if word.lower() in minor_words:
        return True
    if len(word) == 0:
        return True
    return word[0].isupper() and (len(word) == 1 or word[1:].islower() or "'" in word)
