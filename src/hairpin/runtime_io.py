"""Helpers for reading Hairpin source and data files."""

from hairpin.types import HairpinError


def read_text_file(path: str) -> str:
    """Read a UTF-8 text file or raise a HairpinError with a user-facing message."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeError) as exc:
        raise HairpinError(f"Cannot read file '{path}': {exc}") from None
