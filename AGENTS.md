# AGENTS.md

## Setup
```bash
uv sync                                    # install deps + venv
uv tool install . --force --reinstall      # install `ath` globally (~/.local/bin/ath)
```

Requires `ripgrep` (`rg`) on the system (`sudo dnf install ripgrep`).

## Commands
```bash
uv run ath <term>               # dev run (always reads source, no reinstall needed)
ath <term>                      # production (after uv tool install)
ath --py fraise                 # filter by extension
ath -g py -g js regex           # multiple filters
ath --help                      # list all --ext flags
```

After any code change, to update the global install:
```bash
uv tool install . --force --reinstall && hash -r
```

## Keybindings
| Key | Action |
|-----|--------|
| `j`/`k` | Navigate matches |
| `ctrl+e` | Open file in `$EDITOR` at match line (defaults to `vim`) |
| `/` | Focus search input |
| `q` | Quit |

No tests, linter, or typechecker configured yet.

## Architecture
- `ath/searcher.py` — calls `rg --json` to find matches; `load_context()` reads ±10 lines from disk. Accepts optional `extensions` list passed as `-g` flags to rg.
- `ath/tui.py` — Textual 8.x TUI: left pane = match list, right pane = file content with highlighting. Editor launched via `self.suspend()` + `subprocess.run`.
- `ath/main.py` — CLI entry: argparse parses extension flags (`--py`, `--rs`, ..., `-g`) and passes them to `AthApp`. 30+ built-in extension shortcuts in `EXT_FLAGS` dict.
- Root `main.py` — trampoline for `uv run python main.py`

## Gotchas
- **Textual 8.x** `ListView.Selected` uses `event.control.index`, NOT `event.item_index`
- `self.suspend()` is a context manager (`with self.suspend(): ...`), no `self.resume()` needed
- The entry point **must** live inside the `ath/` package (`ath.main:main`) for `uv tool install` to find it. Root `main.py` is only for dev runs.
- `rg` is hard dependency — `search()` raises `RuntimeError` if not found
- CSS is inline in `AthApp` class (no external stylesheet)
