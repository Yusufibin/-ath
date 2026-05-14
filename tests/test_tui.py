import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from ath.searcher import Match
from ath.tui import _highlight_line, _truncate, _build_file_view


class TestHighlightLine:
    def test_empty_term(self):
        result = _highlight_line("some content", "")
        assert str(result) == "some content"

    def test_none_term(self):
        result = _highlight_line("some content", None)
        assert str(result) == "some content"

    def test_simple_match(self):
        result = _highlight_line("def main():", "def")
        assert "def" in str(result)

    def test_case_insensitive_match(self):
        result = _highlight_line("DEF main():", "def")
        assert "DEF" in str(result)

    def test_multiple_matches(self):
        result = _highlight_line("def def def", "def")
        text = str(result)
        assert text.count("def") == 3

    def test_no_match(self):
        result = _highlight_line("some content", "xyz")
        assert str(result) == "some content"

    def test_match_at_start(self):
        result = _highlight_line("def something", "def")
        text = str(result)
        assert text.startswith("def")

    def test_match_at_end(self):
        result = _highlight_line("something def", "def")
        text = str(result)
        assert text.endswith("def")

    def test_match_style_applied(self):
        from rich.text import Text
        result = _highlight_line("def foo", "def", match_style="bold red")
        text = str(result)
        assert "def" in text

    def test_unicode_content(self):
        result = _highlight_line("café def", "def")
        assert "def" in str(result)

    def test_special_regex_characters(self):
        result = _highlight_line("test [a-z] case", "[a-z]")
        assert "[a-z]" in str(result)

    def test_empty_content(self):
        result = _highlight_line("", "test")
        assert str(result) == ""

    def test_match_whole_string(self):
        result = _highlight_line("def", "def")
        assert str(result) == "def"


class TestTruncate:
    def test_short_string(self):
        result = _truncate("short")
        assert result == "short"

    def test_exact_max_length(self):
        result = _truncate("a" * 60)
        assert result == "a" * 60

    def test_truncate_long_string(self):
        result = _truncate("a" * 100)
        assert len(result) == 60
        assert result.endswith("...")

    def test_whitespace_trimming(self):
        result = _truncate("  hello  ")
        assert result == "hello"

    def test_max_len_custom(self):
        result = _truncate("a" * 50, max_len=30)
        assert len(result) == 30
        assert result.endswith("...")

    def test_max_len_zero(self):
        result = _truncate("hello", max_len=0)
        assert result == "..."

    def test_empty_string(self):
        result = _truncate("")
        assert result == ""


class TestBuildFileView:
    def test_empty_term(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\n")

        match = Match(file="test.py", line_number=2, line_content="line2")
        result = _build_file_view(tmp_path, match, "")
        assert "line2" in str(result)

    def test_valid_match(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\n")

        match = Match(file="test.py", line_number=2, line_content="line2")
        result = _build_file_view(tmp_path, match, "line")
        assert "line2" in str(result)

    def test_file_not_found(self, tmp_path):
        match = Match(file="nonexistent.py", line_number=1, line_content="test")
        result = _build_file_view(tmp_path, match, "test")
        assert "not found" in str(result).lower() or "unreadable" in str(result).lower()

    def test_context_lines(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\nline4\nline5\n")

        match = Match(file="test.py", line_number=3, line_content="line3")
        result = _build_file_view(tmp_path, match, "")
        text = str(result)
        assert "line1" in text
        assert "line2" in text
        assert "line3" in text
        assert "line4" in text

    def test_line_number_display(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\n")

        match = Match(file="test.py", line_number=2, line_content="line2")
        result = _build_file_view(tmp_path, match, "")
        text = str(result)
        assert "2" in text or "2" in repr(result)


class TestTuiImports:
    def test_ath_app_importable(self):
        from ath.tui import AthApp
        assert AthApp is not None

    def test_match_list_importable(self):
        from ath.tui import MatchList
        assert MatchList is not None

    def test_file_view_importable(self):
        from ath.tui import FileView
        assert FileView is not None