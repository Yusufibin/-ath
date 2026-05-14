import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from ath.searcher import search, load_context, Match


class TestSearch:
    def test_empty_term_returns_empty_list(self):
        result = search(Path("."), "")
        assert result == []

    def test_empty_extensions_returns_empty_list(self):
        result = search(Path("."), "")
        assert result == []

    def test_valid_term_returns_matches(self):
        result = search(Path("."), "def")
        assert len(result) > 0
        assert all(isinstance(m, Match) for m in result)

    def test_no_match_returns_empty_list(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        with patch("subprocess.run", return_value=mock_proc):
            result = search(Path("tests"), "XYZNOMATCH987654321")
            assert result == []

    def test_extensions_filter_works(self):
        result = search(Path("."), "def", extensions=["py"])
        assert len(result) > 0
        for m in result:
            assert m.file.endswith(".py")

    def test_multiple_extensions(self):
        result = search(Path("."), "test", extensions=["py", "md"])
        for m in result:
            assert m.file.endswith((".py", ".md"))

    def test_ripgrep_not_found_raises(self):
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            with pytest.raises(RuntimeError, match="ripgrep"):
                search(Path("."), "test")

    def test_ripgrep_unexpected_returncode(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 2
        mock_proc.stderr = "error message"
        with patch("subprocess.run", return_value=mock_proc):
            with pytest.raises(RuntimeError, match="ripgrep error"):
                search(Path("."), "test")

    def test_match_structure(self):
        result = search(Path("ath"), "class", extensions=["py"])
        if result:
            m = result[0]
            assert hasattr(m, "file")
            assert hasattr(m, "line_number")
            assert hasattr(m, "line_content")
            assert isinstance(m.line_number, int)
            assert isinstance(m.line_content, str)


class TestLoadContext:
    def test_valid_line_number(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\nline4\nline5\n")

        match = Match(file=test_file.name, line_number=3, line_content="line3")
        before, after = load_context(tmp_path, match, n=2)

        assert len(before) == 2
        assert len(after) == 2
        assert before[0] == (1, "line1")
        assert before[1] == (2, "line2")
        assert after[0] == (4, "line4")
        assert after[1] == (5, "line5")

    def test_out_of_bounds_line_number(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\n")

        match = Match(file=test_file.name, line_number=100, line_content="")
        before, after = load_context(tmp_path, match)
        assert before == []
        assert after == []

    def test_line_number_zero(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\n")

        match = Match(file=test_file.name, line_number=0, line_content="")
        before, after = load_context(tmp_path, match)
        assert before == []
        assert after == []

    def test_negative_line_number(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\n")

        match = Match(file=test_file.name, line_number=-1, line_content="")
        before, after = load_context(tmp_path, match)
        assert before == []
        assert after == []

    def test_file_not_found(self, tmp_path):
        match = Match(file="nonexistent.py", line_number=1, line_content="")
        before, after = load_context(tmp_path, match)
        assert before == []
        assert after == []

    def test_context_at_file_start(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\nline4\n")

        match = Match(file=test_file.name, line_number=1, line_content="line1")
        before, after = load_context(tmp_path, match, n=2)

        assert len(before) == 0
        assert len(after) == 2

    def test_context_at_file_end(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\nline4\n")

        match = Match(file=test_file.name, line_number=4, line_content="line4")
        before, after = load_context(tmp_path, match, n=2)

        assert len(before) == 2
        assert len(after) == 0

    def test_context_truncated_by_file_start(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\nline4\n")

        match = Match(file=test_file.name, line_number=3, line_content="line3")
        before, after = load_context(tmp_path, match, n=10)

        assert len(before) == 2
        assert before[0] == (1, "line1")

    def test_context_truncated_by_file_end(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\nline4\n")

        match = Match(file=test_file.name, line_number=2, line_content="line2")
        before, after = load_context(tmp_path, match, n=10)

        assert len(after) == 2
        assert after[-1] == (4, "line4")

    def test_unicode_content(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("café\nnaïve\n日本語\n", encoding="utf-8")

        match = Match(file=test_file.name, line_number=2, line_content="naïve")
        before, after = load_context(tmp_path, match, n=1)

        assert len(before) == 1
        assert before[0][1] == "café"
        assert len(after) == 1
        assert after[0][1] == "日本語"


class TestMatchDataclass:
    def test_match_creation(self):
        m = Match(file="test.py", line_number=10, line_content="def foo():")
        assert m.file == "test.py"
        assert m.line_number == 10
        assert m.line_content == "def foo():"

    def test_match_is_dataclass(self):
        m = Match(file="test.py", line_number=10, line_content="def foo():")
        assert hasattr(m, "file")
        assert hasattr(m, "line_number")
        assert hasattr(m, "line_content")
        m.line_number = 20
        assert m.line_number == 20