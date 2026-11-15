"""
Signal two: the style signal.

Measures the text as text: sentence-length spread, vocabulary variety, and
punctuation. It cannot read, so anything that reshapes the text without
changing its meaning (typos, chopped sentences, pasted quotes) moves it.

Direction: every measure is converted so HIGHER = MORE LIKELY AI.

    python stylometry.py "some text to look at"
"""

import re
import statistics

# Marks other than commas and full stops. These vary more between writers.
RARE_MARKS = set(";:—–()!?\"“”…-")


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped."""
    return re.findall(r"[a-z0-9']+", text.lower())


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def sentence_length_spread(text: str) -> float:
    """
    Coefficient of variation of sentence length (stdev / mean).
    0 = every sentence the same length; ~0.7+ = very lumpy.
    HIGH = more human. Fewer than 2 sentences returns 0.0.
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    return statistics.stdev(lengths) / mean if mean else 0.0


def type_token_ratio(text: str) -> float:
    """
    Unique words / total words over the FIRST 100 words only, so long and
    short texts are comparable. Scale 0-1. HIGH = more human.
    """
    w = words(text)[:100]
    return len(set(w)) / len(w) if w else 0.0


def punctuation_density(text: str) -> float:
    """Marks other than commas and full stops, per word. HIGH = more human."""
    n = len(words(text))
    if n == 0:
        return 0.0
    marks = sum(1 for ch in text if ch in RARE_MARKS)
    return marks / n


def style_signal(text: str) -> float:
    """
    0-1 score, HIGHER = MORE LIKELY AI.

    Each measure is flipped so high means AI-like and scaled to 0-1, then
    combined: spread 0.45, vocabulary 0.30, punctuation 0.25.
    Too little text to judge (under 3 sentences or 30 words) returns 0.5,
    "no opinion", rather than guessing and risking a false accusation.
    """
    if len(sentences(text)) < 3 or len(words(text)) < 30:
        return 0.5

    spread_ai = 1 - _clamp(sentence_length_spread(text) / 0.7)
    vocab_ai = _clamp((0.85 - type_token_ratio(text)) / 0.35)
    punct_ai = 1 - _clamp(punctuation_density(text) / 0.08)

    score = 0.45 * spread_ai + 0.30 * vocab_ai + 0.25 * punct_ai
    return round(score, 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text):.3f}")
    print(f"type_token_ratio         {type_token_ratio(text):.3f}")
    print(f"punctuation_density      {punctuation_density(text):.3f}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
