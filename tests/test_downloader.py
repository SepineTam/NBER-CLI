#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : test_downloader.py

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nber_cli.download import (
    DownloadBatchResult,
    DownloadFailure,
    _create_connector,
    download_multiple_papers,
    download_paper,
    download_paper_to_file,
)


class _MockContextManager:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, *args):
        return False


def _mock_session(response_content: bytes = b"fake pdf content", *, raise_error=None):
    """Build a minimal mock aiohttp ClientSession."""
    mock_response = MagicMock()
    if raise_error is not None:
        mock_response.raise_for_status.side_effect = raise_error
    mock_response.read = AsyncMock(return_value=response_content)

    mock_session = MagicMock()
    mock_session.get.return_value = _MockContextManager(mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    return mock_session


async def _no_retry(loader):
    """Helper to bypass _retry_async in tests."""
    return await loader()


class TestCreateConnector:
    @pytest.mark.asyncio
    async def test_returns_tcp_connector(self):
        connector = _create_connector()
        assert connector is not None
        await connector.close()


class TestDownloadPaperToFile:
    @pytest.mark.asyncio
    async def test_successful_download(self, tmp_path):
        output_file = tmp_path / "w1234.pdf"
        fake_session = _mock_session(response_content=b"pdf bytes")

        with patch("nber_cli.download.ClientSession", return_value=fake_session):
            with patch("nber_cli.download._retry_async", side_effect=_no_retry):
                with patch("nber_cli.download._USER_AGENT") as mock_ua:
                    mock_ua.random = "Mozilla/5.0"
                    result = await download_paper_to_file("w1234", output_file, restrict_dir=False)

        assert result == output_file
        assert output_file.read_bytes() == b"pdf bytes"

    @pytest.mark.asyncio
    async def test_creates_parent_directories(self, tmp_path):
        output_file = tmp_path / "sub" / "dir" / "w1234.pdf"
        fake_session = _mock_session(response_content=b"pdf bytes")

        with patch("nber_cli.download.ClientSession", return_value=fake_session):
            with patch("nber_cli.download._retry_async", side_effect=_no_retry):
                with patch("nber_cli.download._USER_AGENT") as mock_ua:
                    mock_ua.random = "Mozilla/5.0"
                    result = await download_paper_to_file("w1234", output_file, restrict_dir=False)

        assert result == output_file
        assert output_file.exists()

    @pytest.mark.asyncio
    async def test_http_404_raises_error(self, tmp_path):
        output_file = tmp_path / "w1234.pdf"
        from aiohttp import ClientResponseError
        fake_session = _mock_session(
            raise_error=ClientResponseError(
                request_info=MagicMock(), history=(), status=404, message="Not Found"
            )
        )

        with patch("nber_cli.download.ClientSession", return_value=fake_session):
            with patch("nber_cli.download._retry_async", side_effect=_no_retry):
                with patch("nber_cli.download._USER_AGENT") as mock_ua:
                    mock_ua.random = "Mozilla/5.0"
                    with pytest.raises(ClientResponseError) as exc_info:
                        await download_paper_to_file("w1234", output_file, restrict_dir=False)
                    assert exc_info.value.status == 404

    @pytest.mark.asyncio
    async def test_http_500_raises_error(self, tmp_path):
        output_file = tmp_path / "w1234.pdf"
        from aiohttp import ClientResponseError
        fake_session = _mock_session(
            raise_error=ClientResponseError(
                request_info=MagicMock(), history=(), status=500, message="Internal Error"
            )
        )

        with patch("nber_cli.download.ClientSession", return_value=fake_session):
            with patch("nber_cli.download._retry_async", side_effect=_no_retry):
                with patch("nber_cli.download._USER_AGENT") as mock_ua:
                    mock_ua.random = "Mozilla/5.0"
                    with pytest.raises(ClientResponseError) as exc_info:
                        await download_paper_to_file("w1234", output_file, restrict_dir=False)
                    assert exc_info.value.status == 500

    @pytest.mark.asyncio
    async def test_network_timeout(self, tmp_path):
        output_file = tmp_path / "w1234.pdf"
        fake_session = _mock_session(raise_error=asyncio.TimeoutError("connection timed out"))

        with patch("nber_cli.download.ClientSession", return_value=fake_session):
            with patch("nber_cli.download._retry_async", side_effect=_no_retry):
                with patch("nber_cli.download._USER_AGENT") as mock_ua:
                    mock_ua.random = "Mozilla/5.0"
                    with pytest.raises(asyncio.TimeoutError):
                        await download_paper_to_file("w1234", output_file, restrict_dir=False)

    @pytest.mark.asyncio
    async def test_read_error(self, tmp_path):
        output_file = tmp_path / "w1234.pdf"
        fake_session = _mock_session(raise_error=ConnectionError("broken pipe"))

        with patch("nber_cli.download.ClientSession", return_value=fake_session):
            with patch("nber_cli.download._retry_async", side_effect=_no_retry):
                with patch("nber_cli.download._USER_AGENT") as mock_ua:
                    mock_ua.random = "Mozilla/5.0"
                    with pytest.raises(ConnectionError):
                        await download_paper_to_file("w1234", output_file, restrict_dir=False)

    @pytest.mark.asyncio
    async def test_url_construction(self, tmp_path):
        output_file = tmp_path / "w9999.pdf"
        fake_session = _mock_session(response_content=b"pdf")

        with patch("nber_cli.download.ClientSession", return_value=fake_session):
            with patch("nber_cli.download._retry_async", side_effect=_no_retry):
                with patch("nber_cli.download._USER_AGENT") as mock_ua:
                    mock_ua.random = "Mozilla/5.0"
                    await download_paper_to_file("w9999", output_file, restrict_dir=False)

        assert fake_session.get.call_count == 1
        assert fake_session.get.call_args.args[0] == "https://www.nber.org/papers/w9999.pdf"

    @pytest.mark.asyncio
    async def test_user_agent_header(self, tmp_path):
        output_file = tmp_path / "w1234.pdf"
        fake_session = _mock_session(response_content=b"pdf")

        with patch("nber_cli.download.ClientSession", return_value=fake_session) as mock_client_session:
            with patch("nber_cli.download._retry_async", side_effect=_no_retry):
                with patch("nber_cli.download._USER_AGENT") as mock_ua:
                    mock_ua.random = "TestAgent/1.0"
                    await download_paper_to_file("w1234", output_file, restrict_dir=False)

        mock_client_session.assert_called_once()
        call_kwargs = mock_client_session.call_args.kwargs
        assert call_kwargs["headers"] == {"User-Agent": "TestAgent/1.0"}

    @pytest.mark.asyncio
    async def test_with_provided_session(self, tmp_path):
        output_file = tmp_path / "w1234.pdf"
        fake_session = _mock_session(response_content=b"session pdf")

        with patch("nber_cli.download._USER_AGENT") as mock_ua:
            mock_ua.random = "Mozilla/5.0"
            result = await download_paper_to_file("w1234", output_file, session=fake_session, restrict_dir=False)

        assert result == output_file
        assert output_file.read_bytes() == b"session pdf"


class TestDownloadPaper:
    @pytest.mark.asyncio
    async def test_download_paper_uses_correct_filename(self, tmp_path):
        with patch("nber_cli.download.download_paper_to_file") as mock_download:
            mock_download.return_value = tmp_path / "w1234.pdf"
            result = await download_paper("w1234", tmp_path, restrict_dir=False)
            assert result == tmp_path / "w1234.pdf"
            mock_download.assert_called_once_with("w1234", tmp_path / "w1234.pdf", session=None, restrict_dir=False)

    @pytest.mark.asyncio
    async def test_download_paper_with_session(self, tmp_path):
        fake_session = MagicMock()
        with patch("nber_cli.download.download_paper_to_file") as mock_download:
            mock_download.return_value = tmp_path / "w1234.pdf"
            result = await download_paper("w1234", tmp_path, session=fake_session, restrict_dir=False)
            assert result == tmp_path / "w1234.pdf"
            mock_download.assert_called_once_with("w1234", tmp_path / "w1234.pdf", session=fake_session, restrict_dir=False)


class TestDownloadMultiplePapers:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("concurrency", [0, -1, True])
    async def test_rejects_invalid_concurrency_immediately(self, tmp_path, concurrency):
        with patch("nber_cli.download.ClientSession") as mock_session:
            with pytest.raises(ValueError, match="positive integer"):
                await download_multiple_papers(
                    ["w1234"],
                    tmp_path,
                    restrict_dir=False,
                    concurrency=concurrency,
                )

        mock_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_file_concurrency_falls_back_without_hanging(
        self, tmp_path, isolated_nber_home
    ):
        from nber_cli.config import NBERCLIConfig

        config_path = isolated_nber_home / ".nber-cli" / "config.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text('{"download": {"concurrency": 0}}')
        runtime_config = NBERCLIConfig.from_config_file()

        with (
            patch("nber_cli.download.NBER_CLI_CONFIG", runtime_config),
            patch(
                "nber_cli.download.download_paper",
                new_callable=AsyncMock,
                return_value=tmp_path / "w1234.pdf",
            ),
        ):
            result = await asyncio.wait_for(
                download_multiple_papers(["w1234"], tmp_path, restrict_dir=False),
                timeout=0.2,
            )

        assert runtime_config.download_concurrency == 3
        assert result.paths == [tmp_path / "w1234.pdf"]

    @pytest.mark.asyncio
    async def test_all_success(self, tmp_path):
        with patch("nber_cli.download.download_paper") as mock_download:
            mock_download.side_effect = [
                tmp_path / "w1234.pdf",
                tmp_path / "w5678.pdf",
            ]
            result = await download_multiple_papers(["w1234", "w5678"], tmp_path, restrict_dir=False)
            assert len(result.paths) == 2
            assert len(result.failures) == 0
            assert result.paths == [tmp_path / "w1234.pdf", tmp_path / "w5678.pdf"]

    @pytest.mark.asyncio
    async def test_all_failure(self, tmp_path):
        with patch("nber_cli.download.download_paper") as mock_download:
            mock_download.side_effect = [
                Exception("network error"),
                Exception("timeout"),
            ]
            result = await download_multiple_papers(["w1234", "w5678"], tmp_path, restrict_dir=False)
            assert len(result.paths) == 0
            assert len(result.failures) == 2
            assert result.failures[0].paper_id == "w1234"
            assert result.failures[1].paper_id == "w5678"

    @pytest.mark.asyncio
    async def test_partial_failure(self, tmp_path):
        with patch("nber_cli.download.download_paper") as mock_download:
            mock_download.side_effect = [
                tmp_path / "w1234.pdf",
                Exception("not found"),
            ]
            result = await download_multiple_papers(["w1234", "w5678"], tmp_path, restrict_dir=False)
            assert len(result.paths) == 1
            assert len(result.failures) == 1
            assert result.paths[0] == tmp_path / "w1234.pdf"
            assert result.failures[0].paper_id == "w5678"
            assert str(result.failures[0].error) == "not found"

    @pytest.mark.asyncio
    async def test_single_paper(self, tmp_path):
        with patch("nber_cli.download.download_paper") as mock_download:
            mock_download.return_value = tmp_path / "w1234.pdf"
            result = await download_multiple_papers(["w1234"], tmp_path, restrict_dir=False)
            assert len(result.paths) == 1
            assert len(result.failures) == 0

    @pytest.mark.asyncio
    async def test_empty_list(self, tmp_path):
        result = await download_multiple_papers([], tmp_path, restrict_dir=False)
        assert len(result.paths) == 0
        assert len(result.failures) == 0

    @pytest.mark.asyncio
    async def test_cancelled_error_handled(self, tmp_path):
        with patch("nber_cli.download.download_paper") as mock_download:
            mock_download.side_effect = [
                tmp_path / "w1234.pdf",
                asyncio.CancelledError("task cancelled"),
            ]
            result = await download_multiple_papers(["w1234", "w5678"], tmp_path, restrict_dir=False)
            assert len(result.paths) == 1
            assert len(result.failures) == 1
            assert result.failures[0].paper_id == "w5678"
            assert isinstance(result.failures[0].error, asyncio.CancelledError)

    @pytest.mark.asyncio
    async def test_concurrent_execution(self, tmp_path):
        active_count = [0]
        max_active = [0]
        lock = asyncio.Lock()

        async def slow_download(paper_id, save_base, session=None, *, restrict_dir=True):
            async with lock:
                active_count[0] += 1
                max_active[0] = max(max_active[0], active_count[0])
            await asyncio.sleep(0.05)
            async with lock:
                active_count[0] -= 1
            return save_base / f"{paper_id}.pdf"

        with patch("nber_cli.download.download_paper", side_effect=slow_download):
            result = await download_multiple_papers(["w1", "w2", "w3"], tmp_path, restrict_dir=False)

        assert len(result.paths) == 3
        assert len(result.failures) == 0
        assert max_active[0] >= 2


class TestDownloadBatchResult:
    def test_dataclass_creation(self):
        paths = [Path("/tmp/a.pdf")]
        failures = [DownloadFailure("w1", Exception("err"))]
        result = DownloadBatchResult(paths=paths, failures=failures)
        assert result.paths == paths
        assert result.failures == failures

    def test_empty_result(self):
        result = DownloadBatchResult(paths=[], failures=[])
        assert result.paths == []
        assert result.failures == []


class TestPathValidation:
    def test_validate_paper_id_accepts_w_prefix(self):
        from nber_cli.download import _validate_paper_id
        _validate_paper_id("w1234")  # should not raise

    def test_validate_paper_id_accepts_bare_digits(self):
        from nber_cli.download import _validate_paper_id
        _validate_paper_id("1234")  # should not raise

    def test_validate_paper_id_rejects_path_traversal(self):
        from nber_cli.download import _validate_paper_id
        with pytest.raises(ValueError, match="invalid paper ID"):
            _validate_paper_id("w1234/../etc")

    def test_validate_download_path_rejects_outside_cwd(self):
        from nber_cli.download import _validate_download_path
        with pytest.raises(ValueError, match="outside the current directory"):
            _validate_download_path(Path("/tmp/outside.pdf"))

    def test_validate_download_path_allows_cwd_subdir(self):
        from nber_cli.download import _validate_download_path
        _validate_download_path(Path("sub") / "dir" / "w1234.pdf")  # should not raise

    def test_download_paper_to_file_restricts_by_default(self, tmp_path):
        output_file = tmp_path / "w1234.pdf"
        with pytest.raises(ValueError, match="outside the current directory"):
            asyncio.run(download_paper_to_file("w1234", output_file))

    def test_download_paper_to_file_allows_any_path_with_restrict_false(self, tmp_path):
        output_file = tmp_path / "w1234.pdf"
        fake_session = _mock_session(response_content=b"pdf bytes")

        with patch("nber_cli.download.ClientSession", return_value=fake_session):
            with patch("nber_cli.download._retry_async", side_effect=_no_retry):
                with patch("nber_cli.download._USER_AGENT") as mock_ua:
                    mock_ua.random = "Mozilla/5.0"
                    result = asyncio.run(download_paper_to_file("w1234", output_file, restrict_dir=False))

        assert result == output_file

    def test_download_paper_restricts_by_default(self, tmp_path):
        with pytest.raises(ValueError, match="outside the current directory"):
            asyncio.run(download_paper("w1234", tmp_path))

    def test_download_multiple_papers_restricts_by_default(self, tmp_path):
        with pytest.raises(ValueError, match="outside the current directory"):
            asyncio.run(download_multiple_papers(["w1234"], tmp_path))


class TestDownloadFailure:
    def test_dataclass_creation(self):
        error = Exception("test error")
        failure = DownloadFailure(paper_id="w1234", error=error)
        assert failure.paper_id == "w1234"
        assert failure.error is error

    def test_str_representation(self):
        error = ValueError("invalid paper")
        failure = DownloadFailure(paper_id="w1234", error=error)
        assert str(failure.error) == "invalid paper"
