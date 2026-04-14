"""File helpers and lightweight adapters."""

from __future__ import annotations

from io import BytesIO


class NamedBytesIO(BytesIO):
    def __init__(self, raw: bytes, name: str):
        super().__init__(raw)
        self.name = name


def extract_snippet(text: str, start: int, length: int = 180) -> str:
    left = max(0, start - 60)
    right = min(len(text), start + length)
    return text[left:right].strip()
