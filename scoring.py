"""
Turning two numbers into one, and one number into something a person can read.
"""

import config


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def combine_signals(model_score: float, style_score: float) -> float:
    """
    Combine two 0-1 signals (higher = more likely AI) into one 0-1 score.

    Rule:
      1. Weighted average (weights in config.py, 0.5 / 0.5).
      2. If the signals differ by DISAGREEMENT_GAP (0.45) or more, pull the
         result toward 0.5 by keeping only 40% of its distance from 0.5.
         Disagreement means uncertainty, so it lands in "unsure".
      3. The AI threshold (0.69) is set further from the middle than the
         human one (0.35), so a wrong accusation needs more evidence than a
         "human" call.
    """
    m = _clamp(model_score)
    s = _clamp(style_score)
    combined = config.WEIGHT_MODEL_SIGNAL * m + config.WEIGHT_STYLE_SIGNAL * s
    if abs(m - s) >= config.DISAGREEMENT_GAP:
        combined = 0.5 + (combined - 0.5) * config.DISAGREEMENT_SHRINK
    return round(_clamp(combined), 4)


LABEL_AI = (
    "Our checks suggest this may have been written with the help of AI. "
    "These tools can be wrong, so if you wrote it yourself, please tell us "
    "and a person will take another look."
)
LABEL_HUMAN = "We think this was probably written by a person."
LABEL_UNSURE = (
    "We can't tell for sure whether this was written by a person or by AI. "
    "That isn't a finding that anything is wrong. If you wrote it yourself, "
    "you don't need to do anything, and you can ask for a review at any time."
)


def score_to_label(score: float) -> tuple[str, str]:
    """Turn a score into (guess, label_text). Thresholds are in config.py."""
    if score >= config.AI_THRESHOLD:
        return "ai", LABEL_AI
    if score <= config.HUMAN_THRESHOLD:
        return "human", LABEL_HUMAN
    return "unsure", LABEL_UNSURE


def label_ranges() -> list[tuple[str, str]]:
    """The score range each label covers."""
    return [
        ("high-confidence human", f"0.00 – {config.HUMAN_THRESHOLD:.2f}"),
        ("unsure", f"{config.HUMAN_THRESHOLD:.2f} – {config.AI_THRESHOLD:.2f}"),
        ("high-confidence AI", f"{config.AI_THRESHOLD:.2f} – 1.00"),
    ]
