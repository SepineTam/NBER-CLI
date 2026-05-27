"""Tests for __main__.py entry point."""

import sys
from unittest.mock import patch


class TestMainEntryPoint:
    def test_main_imports_and_runs(self):
        with patch.object(sys, "argv", ["nber-cli"]):
            with patch("nber_cli.main") as mock_cli_main:
                mock_cli_main.return_value = None
                import nber_cli.__main__
                nber_cli.__main__.main()
                mock_cli_main.assert_called_once()
