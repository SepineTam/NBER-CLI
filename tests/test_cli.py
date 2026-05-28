#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : test_cli.py

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nber_cli.cli import _build_parser, _get_version, _parse_paper_id, _resolve_paper_ids, main


class TestGetVersion:
    def test_returns_version_when_package_installed(self):
        with patch("nber_cli.cli.get_version", return_value="0.2.0"):
            assert _get_version() == "0.2.0"

    def test_returns_fallback_when_package_not_installed(self):
        with patch("nber_cli.cli.get_version", side_effect=Exception("not found")):
            assert _get_version() == "0.2.0"


class TestBuildParser:
    def test_parser_creation(self):
        parser = _build_parser()
        assert parser.prog == "nber-cli"

    def test_version_flag(self, capsys):
        parser = _build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "NBER CLI v" in captured.out

    def test_download_subcommand_with_single_id(self):
        parser = _build_parser()
        args = parser.parse_args(["download", "w1234"])
        assert args.command == "download"
        assert args.paper_id == "w1234"
        assert args.save_base == Path.cwd()

    def test_download_subcommand_with_save_base(self):
        parser = _build_parser()
        args = parser.parse_args(["download", "w1234", "--save-base", "/tmp/papers"])
        assert args.save_base == Path("/tmp/papers")

    def test_download_subcommand_with_file_path(self):
        parser = _build_parser()
        args = parser.parse_args(["download", "w1234", "--file", "/tmp/paper.pdf"])
        assert args.file_path == Path("/tmp/paper.pdf")

    def test_download_subcommand_with_batch(self):
        parser = _build_parser()
        args = parser.parse_args(["download", "--batch", "w1234", "w5678"])
        assert args.batch_ids == ["w1234", "w5678"]
        assert args.paper_id is None

    def test_download_without_args(self):
        parser = _build_parser()
        args = parser.parse_args(["download"])
        assert args.paper_id is None
        assert args.batch_ids is None

    def test_info_subcommand_with_paper_id(self):
        parser = _build_parser()
        args = parser.parse_args(["info", "w1234"])
        assert args.command == "info"
        assert args.paper_id == "w1234"
        assert args.show_all is False

    def test_info_subcommand_with_all_flag(self):
        parser = _build_parser()
        args = parser.parse_args(["info", "w1234", "--all"])
        assert args.command == "info"
        assert args.paper_id == "w1234"
        assert args.show_all is True

    def test_info_subcommand_without_args(self):
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["info"])


class TestResolvePaperIds:
    def test_batch_ids_take_priority(self):
        assert _resolve_paper_ids("w1234", ["w5678", "w9012"]) == ["w5678", "w9012"]

    def test_single_id_when_no_batch(self):
        assert _resolve_paper_ids("w1234", None) == ["w1234"]

    def test_empty_list_when_neither(self):
        assert _resolve_paper_ids(None, None) == []

    def test_empty_list_when_both_none(self):
        assert _resolve_paper_ids(None, None) == []


class TestParsePaperId:
    def test_with_w_prefix(self):
        assert _parse_paper_id("w1234") == 1234

    def test_without_prefix(self):
        assert _parse_paper_id("5678") == 5678

    def test_uppercase_w(self):
        assert _parse_paper_id("W9999") == 9999

    def test_invalid_raises_valueerror(self):
        with pytest.raises(ValueError):
            _parse_paper_id("abc")


class TestMainEntrypoint:
    def test_no_command_prints_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, "argv", ["nber-cli"]):
                main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "download" in captured.out

    def test_mix_paper_id_and_batch_raises_error(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, "argv", ["nber-cli", "download", "w1234", "--batch", "w5678"]):
                main()
        assert exc_info.value.code == 2

    def test_batch_with_file_raises_error(self):
        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, "argv", ["nber-cli", "download", "--batch", "w1234", "--file", "/tmp/x.pdf"]):
                main()
        assert exc_info.value.code == 2

    def test_no_paper_id_raises_error(self):
        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, "argv", ["nber-cli", "download"]):
                main()
        assert exc_info.value.code == 2

    def test_multiple_ids_with_file_raises_error(self):
        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, "argv", ["nber-cli", "download", "--batch", "w1234", "w5678", "--file", "/tmp/x.pdf"]):
                main()
        assert exc_info.value.code == 2

    @patch("nber_cli.cli.download_multiple_papers", new_callable=AsyncMock)
    def test_batch_with_single_id_and_no_file_path(self, mock_download):
        mock_result = MagicMock()
        mock_result.paths = [Path("/tmp/w1234.pdf")]
        mock_result.failures = []
        mock_download.return_value = mock_result
        with patch.object(sys, "argv", ["nber-cli", "download", "--batch", "w1234", "--save-base", "/tmp"]):
            main()
        mock_download.assert_called_once_with(["w1234"], Path("/tmp"))

    @patch("nber_cli.cli.download_paper_to_file", new_callable=AsyncMock)
    def test_single_download_with_file_path(self, mock_download):
        mock_download.return_value = Path("/tmp/paper.pdf")
        with patch.object(sys, "argv", ["nber-cli", "download", "w1234", "--file", "/tmp/paper.pdf"]):
            main()
        mock_download.assert_called_once_with("w1234", Path("/tmp/paper.pdf"))

    @patch("nber_cli.cli.download_paper", new_callable=AsyncMock)
    def test_single_download_without_file_path(self, mock_download):
        mock_download.return_value = Path("/tmp/w1234.pdf")
        with patch.object(sys, "argv", ["nber-cli", "download", "w1234", "--save-base", "/tmp"]):
            main()
        mock_download.assert_called_once_with("w1234", Path("/tmp"))

    @patch("nber_cli.cli.download_paper_to_file", new_callable=AsyncMock)
    def test_single_paper_with_file_path(self, mock_download):
        mock_download.return_value = Path("/tmp/custom.pdf")
        with patch.object(sys, "argv", ["nber-cli", "download", "w1234", "--file", "/tmp/custom.pdf"]):
            main()
        mock_download.assert_called_once_with("w1234", Path("/tmp/custom.pdf"))

    @patch("nber_cli.cli.download_multiple_papers", new_callable=AsyncMock)
    def test_batch_download_all_success(self, mock_download):
        mock_result = MagicMock()
        mock_result.paths = [Path("/tmp/w1234.pdf"), Path("/tmp/w5678.pdf")]
        mock_result.failures = []
        mock_download.return_value = mock_result
        with patch.object(sys, "argv", ["nber-cli", "download", "--batch", "w1234", "w5678", "--save-base", "/tmp"]):
            main()
        mock_download.assert_called_once_with(["w1234", "w5678"], Path("/tmp"))

    @patch("nber_cli.cli.download_paper", new_callable=AsyncMock)
    def test_single_paper_no_batch_no_file(self, mock_download):
        mock_download.return_value = Path("/tmp/w1234.pdf")
        with patch.object(sys, "argv", ["nber-cli", "download", "w1234", "--save-base", "/tmp"]):
            main()
        mock_download.assert_called_once_with("w1234", Path("/tmp"))

    @patch("nber_cli.cli.download_multiple_papers", new_callable=AsyncMock)
    def test_batch_download_no_failures(self, mock_download):
        mock_result = MagicMock()
        mock_result.paths = [Path("/tmp/w1234.pdf")]
        mock_result.failures = []
        mock_download.return_value = mock_result
        with patch.object(sys, "argv", ["nber-cli", "download", "--batch", "w1234", "--save-base", "/tmp"]):
            main()
        mock_download.assert_called_once_with(["w1234"], Path("/tmp"))

    @patch("nber_cli.cli.download_multiple_papers", new_callable=AsyncMock)
    def test_batch_download_with_failures_exits_1(self, mock_download, capsys):
        from nber_cli.download import DownloadFailure
        mock_result = MagicMock()
        mock_result.paths = [Path("/tmp/w1234.pdf")]
        mock_result.failures = [
            DownloadFailure(paper_id="w5678", error=Exception("network error")),
        ]
        mock_download.return_value = mock_result
        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, "argv", ["nber-cli", "download", "--batch", "w1234", "w5678", "--save-base", "/tmp"]):
                main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Failed to download w5678" in captured.err
        assert "Downloaded 1 of 2 papers" in captured.err

    @patch("nber_cli.cli.download_multiple_papers", new_callable=AsyncMock)
    def test_batch_download_all_failures_exits_1(self, mock_download, capsys):
        from nber_cli.download import DownloadFailure
        mock_result = MagicMock()
        mock_result.paths = []
        mock_result.failures = [
            DownloadFailure(paper_id="w1234", error=Exception("timeout")),
            DownloadFailure(paper_id="w5678", error=Exception("404")),
        ]
        mock_download.return_value = mock_result
        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, "argv", ["nber-cli", "download", "--batch", "w1234", "w5678", "--save-base", "/tmp"]):
                main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Failed to download w1234" in captured.err
        assert "Failed to download w5678" in captured.err
        assert "Downloaded 0 of 2 papers" in captured.err

    @patch("nber_cli.cli.download_multiple_papers", new_callable=AsyncMock)
    def test_batch_download_error_with_empty_message(self, mock_download, capsys):
        from nber_cli.download import DownloadFailure
        class EmptyError(Exception):
            def __str__(self):
                return ""
        mock_result = MagicMock()
        mock_result.paths = []
        mock_result.failures = [
            DownloadFailure(paper_id="w1234", error=EmptyError()),
        ]
        mock_download.return_value = mock_result
        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, "argv", ["nber-cli", "download", "--batch", "w1234", "--save-base", "/tmp"]):
                main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "EmptyError" in captured.err


class TestMainEntrypointInfo:
    @patch("nber_cli.cli.get_nber", new_callable=AsyncMock)
    def test_info_basic_output(self, mock_get_nber, capsys):
        from nber_cli.core.models import NBER
        mock_get_nber.return_value = NBER(
            paper_id=1234,
            title="Test Title",
            authors=["Author A"],
            date="2024/01/01",
            abstract="Test abstract.",
        )
        with patch.object(sys, "argv", ["nber-cli", "info", "w1234"]):
            main()
        captured = capsys.readouterr()
        assert "Test Title" in captured.out
        assert "Author A" in captured.out
        assert "Test abstract." in captured.out

    @patch("nber_cli.cli.get_nber", new_callable=AsyncMock)
    def test_info_with_all_flag(self, mock_get_nber, capsys):
        from nber_cli.core.models import NBER
        mock_get_nber.return_value = NBER(
            paper_id=1234,
            title="Test Title",
            authors=["Author A"],
            date="2024/01/01",
            abstract="Test abstract.",
            published_version="Published in Journal.",
        )
        with patch.object(sys, "argv", ["nber-cli", "info", "w1234", "--all"]):
            main()
        captured = capsys.readouterr()
        assert "Test Title" in captured.out
        assert "Published in Journal." in captured.out

    @patch("nber_cli.cli.get_nber", new_callable=AsyncMock)
    def test_info_without_w_prefix(self, mock_get_nber, capsys):
        from nber_cli.core.models import NBER
        mock_get_nber.return_value = NBER(
            paper_id=5678,
            title="No Prefix",
            authors=["Author B"],
            date="2024/02/01",
            abstract="Abstract text.",
        )
        with patch.object(sys, "argv", ["nber-cli", "info", "5678"]):
            main()
        mock_get_nber.assert_called_once_with(5678)
        captured = capsys.readouterr()
        assert "No Prefix" in captured.out

    def test_info_invalid_paper_id(self):
        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, "argv", ["nber-cli", "info", "abc"]):
                main()
        assert exc_info.value.code == 2
