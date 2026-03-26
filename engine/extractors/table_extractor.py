"""Table extraction helpers for OpenGraph AI.

TODO: Support schema validation and typed parsing.
"""

import csv
from pathlib import Path


def extract_table(path: str) -> list[dict[str, str]]:
    """Extract rows from a CSV file.

    TODO: Handle malformed files and non-CSV formats.
    """
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]
