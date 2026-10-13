"""Script-aware tokenisation.

Python's \\w does not match Devanagari vowel signs (matras), so a naive \\w+ would shred Marathi words
into fragments. Tokens here keep matras and exclude the danda punctuation marks.
"""
import re

_TOKEN = re.compile(r"(?:[^\W_]|[ऀ-ॣ०-ॿ])+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())
