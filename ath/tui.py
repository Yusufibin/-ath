from __future__ import annotations

import re
import os
import shutil
import subprocess
from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static

from .searcher import Match, load_context, search

CONTEXT = 10


def _build_file_view(root: Path, match: Match, term: str) -> Text:
    filepath = root / match.file
    if not filepath.exists():
        return Text("(file not found or unreadable)")

    before, after = load_context(root, match, n=CONTEXT)

    all_lines = before + [(match.line_number, match.line_content)] + after
    if not all_lines:
        return Text("(file not found or unreadable)")

    text = Text()
    max_ln = max(ln for ln, _ in all_lines)
    ln_width = len(str(max_ln))

    for ln, content in before:
        prefix = f"{ln:>{ln_width}} │ "
        text.append(prefix, style="dim")
        text.append(_highlight_line(content, term))
        text.append("\n")

    prefix = f"{match.line_number:>{ln_width}} ▶ "
    text.append(prefix, style="bold yellow")
    text.append(_highlight_line(match.line_content, term, match_style="bold reverse yellow"))
    text.append("\n")

    for ln, content in after:
        prefix = f"{ln:>{ln_width}} │ "
        text.append(prefix, style="dim")
        text.append(_highlight_line(content, term))
        text.append("\n")

    return text


def _highlight_line(
    content: str, term: str, match_style: str = "bold yellow"
) -> Text:
    text = Text()
    if not term:
        text.append(content)
        return text
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    last = 0
    for m in pattern.finditer(content):
        text.append(content[last:m.start()])
        text.append(m.group(), style=match_style)
        last = m.end()
    text.append(content[last:])
    return text


def _truncate(s: str, max_len: int = 60) -> str:
    s = s.strip()
    if max_len <= 0:
        return "..."
    if len(s) > max_len:
        return s[:max_len - 3] + "..."
    return s


class FileView(Static):
    """Displays file content with highlighted matches."""


class MatchList(ListView):
    """List of matches (left pane)."""


class AthApp(App):
    CSS = """
    #search-input {
        dock: top;
        margin: 1 2 0 2;
        height: 3;
        border: solid $accent;
    }

    #search-input:focus {
        border: solid $secondary;
    }

    #panes {
        height: 1fr;
    }

    #files-pane {
        width: 2fr;
        border: solid $surface-lighten-1;
    }

    #files-header {
        text-style: bold;
        color: $secondary;
        padding: 0 1;
        height: 1;
    }

    #match-count {
        text-style: italic;
        color: $text-muted;
        padding: 0 1;
        height: 1;
    }

    #view-pane {
        width: 3fr;
        border: solid $surface-lighten-1;
        padding: 1 2;
    }

    #view-header {
        text-style: bold;
        color: $primary;
        padding: 0 1;
        height: 1;
    }

    #view-content {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("q", "quit", "Quit"),
        ("/", "focus_search", "Search"),
        ("ctrl+e", "open_editor", "Edit"),
    ]

    def __init__(self, initial_term: str = "", extensions: list[str] | None = None):
        super().__init__()
        self._initial_term = initial_term
        self._extensions = extensions
        self._matches: list[Match] = []
        self._selected_idx: int = 0
        self._root = Path.cwd()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Input(
            value=self._initial_term,
            placeholder="Search term...",
            id="search-input",
        )
        with Horizontal(id="panes"):
            with Vertical(id="files-pane"):
                yield Label("Matches", id="files-header")
                yield Label("No results yet", id="match-count")
                yield MatchList(id="match-list")
            with Vertical(id="view-pane"):
                yield Label("File View", id="view-header")
                yield VerticalScroll(FileView(id="view-content"))
        yield Footer()

    def on_mount(self) -> None:
        if self._initial_term:
            self._run_search(self._initial_term)

    @on(Input.Submitted)
    def on_search_submit(self, event: Input.Submitted) -> None:
        term = event.value.strip()
        if term:
            self._run_search(term)
        self.query_one("#match-list", MatchList).focus()

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_open_editor(self) -> None:
        if not self._matches:
            return
        match = self._matches[self._selected_idx]
        editor = os.environ.get("EDITOR", "nvim")
        vim_family = {"vim", "nvim", "vi", "gvim", "mvim"}
        if editor not in vim_family:
            fallback = shutil.which("nvim") or shutil.which("vim") or None
            if fallback:
                editor = fallback
            else:
                editor = "vim"
        filepath = self._root / match.file
        with self.suspend():
            subprocess.run([editor, f"+{match.line_number}", str(filepath)])

    def action_cursor_down(self) -> None:
        if isinstance(self.focused, MatchList):
            self._move_selection(1)

    def action_cursor_up(self) -> None:
        if isinstance(self.focused, MatchList):
            self._move_selection(-1)

    def _move_selection(self, delta: int) -> None:
        if not self._matches:
            return
        self._selected_idx = (self._selected_idx + delta) % len(self._matches)
        lst = self.query_one("#match-list", MatchList)
        lst.index = self._selected_idx
        self._show_match(self._matches[self._selected_idx])

    def _run_search(self, term: str) -> None:
        self._matches = search(self._root, term, extensions=self._extensions)
        self._selected_idx = 0

        lst = self.query_one("#match-list", MatchList)
        lst.clear()
        for m in self._matches:
            snippet = _truncate(m.line_content)
            lst.append(ListItem(Label(f"{m.file}:{m.line_number}  {snippet}")))

        if not self._matches:
            self.query_one("#match-count", Label).update("No matches found")
            self.query_one("#view-content", FileView).update("")
            return

        self.query_one("#match-count", Label).update(
            f"{len(self._matches)} matches  -  j/k navigate  / search  q quit"
        )
        lst.index = 0
        lst.focus()
        self._show_match(self._matches[0])

    def _show_match(self, match: Match) -> None:
        term = self.query_one("#search-input", Input).value
        view = _build_file_view(self._root, match, term)
        self.query_one("#view-content", FileView).update(view)

    @on(ListView.Selected)
    def on_match_selected(self, event: ListView.Selected) -> None:
        if self._matches and event.control.index is not None:
            idx = event.control.index
            if 0 <= idx < len(self._matches):
                self._selected_idx = idx
                self._show_match(self._matches[idx])
