import pytest
from unittest.mock import patch
from io import StringIO
from ath.main import main, EXT_FLAGS


class TestEXT_FLAGS:
    def test_ext_flags_defined(self):
        assert isinstance(EXT_FLAGS, dict)
        assert len(EXT_FLAGS) > 30

    def test_common_extensions_present(self):
        expected = ["py", "rs", "js", "ts", "go", "md", "json", "yaml"]
        for ext in expected:
            assert ext in EXT_FLAGS

    def test_extension_descriptions(self):
        for ext, desc in EXT_FLAGS.items():
            assert isinstance(ext, str)
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestMain:
    def test_main_entry_point(self):
        import ath.main
        assert hasattr(ath.main, "main")
        assert callable(ath.main.main)

    @patch("sys.stdout", new_callable=StringIO)
    def test_argparse_help(self, mock_stdout):
        import sys
        import argparse
        from io import StringIO
        from ath.main import main

        old_argv = sys.argv
        old_stdout = sys.stdout
        sys.argv = ["ath", "--help"]
        sys.stdout = StringIO()
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
            output = sys.stdout.getvalue()
            assert "ath" in output.lower()
        finally:
            sys.argv = old_argv
            sys.stdout = old_stdout