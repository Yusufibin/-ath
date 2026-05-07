from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

CONTEXT = 10


@dataclass
class Match:
    file: str
    line_number: int
    line_content: str


def search(root: Path, term: str, extensions: list[str] | None = None) -> list[Match]:
    cmd = ["rg", "--json", "--no-heading"]
    if extensions:
        for ext in extensions:
            cmd.extend(["-g", f"*.{ext}"])
    cmd.extend(["--", term])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=root)
    except FileNotFoundError:
        raise RuntimeError(
            "ripgrep (rg) is required. Install it: sudo dnf install ripgrep"
        )

    matches: list[Match] = []
    for line in proc.stdout.splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "match":
            continue
        data = entry["data"]
        path_text = data["path"]["text"]
        ln = data["line_number"]
        content = data["lines"]["text"].rstrip("\n")
        matches.append(Match(
            file=path_text,
            line_number=ln,
            line_content=content,
        ))

    return matches


def load_context(root: Path, match: Match, n: int = CONTEXT) -> tuple[
    list[tuple[int, str]], list[tuple[int, str]]
]:
    """Return (context_before, context_after) for a match."""
    filepath = root / match.file
    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return [], []

    idx = match.line_number - 1
    before_start = max(0, idx - n)
    after_end = min(len(lines), idx + n + 1)

    before = [(j + 1, lines[j]) for j in range(before_start, idx)]
    after = [(j + 1, lines[j]) for j in range(idx + 1, after_end)]
    return before, after
