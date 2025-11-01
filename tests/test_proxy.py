"""Tests for the ProxyServer."""

from pathlib import Path
from typing import Any, Coroutine
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from devrelay.proxy import ProxyServer


class TestProxyServer:
    """Test cases for ProxyServer."""

    def test_default_initialization(self) -> None:
        """Test ProxyServer initialization with defaults."""
        server = ProxyServer()

        assert server.host == "127.0.0.1"
        assert server.port == 8080
        assert server.confdir == Path.home() / ".mitmproxy"

    def test_custom_initialization(self) -> None:
        """Test ProxyServer initialization with custom values."""
        custom_confdir = Path("/tmp/test-mitmproxy")
        server = ProxyServer(
            host="0.0.0.0",
            port=9090,
            confdir=custom_confdir,
        )

        assert server.host == "0.0.0.0"
        assert server.port == 9090
        assert server.confdir == custom_confdir

    def test_confdir_defaults_to_home_mitmproxy(self) -> None:
        """Test that confdir defaults to ~/.mitmproxy when not specified."""
        server = ProxyServer()
        expected_path = Path.home() / ".mitmproxy"

        assert server.confdir == expected_path

    @pytest.mark.asyncio
    async def test_start_creates_and_runs_master(self) -> None:
        """Test that start() creates DumpMaster and runs it."""
        server = ProxyServer()

        with (
            patch("devrelay.proxy.options.Options") as mock_options,
            patch("devrelay.proxy.dump.DumpMaster") as mock_dump_master,
        ):
            # Setup mocks
            mock_master_instance = MagicMock()
            mock_master_instance.run = AsyncMock()
            mock_dump_master.return_value = mock_master_instance

            # Run start
            await server.start()

            # Verify Options was called with correct parameters
            mock_options.assert_called_once()
            call_kwargs = mock_options.call_args[1]
            assert call_kwargs["listen_host"] == "127.0.0.1"
            assert call_kwargs["listen_port"] == 8080
            assert call_kwargs["http2"] is True
            assert call_kwargs["http3"] is True
            assert call_kwargs["websocket"] is True

            # Verify DumpMaster was created
            mock_dump_master.assert_called_once()

            # Verify all 6 addons were added (CSP, COEP, COOP, CORP, 2x CORS)
            assert mock_master_instance.addons.add.call_count == 6

            # Verify master.run was called
            mock_master_instance.run.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_handles_keyboard_interrupt(self) -> None:
        """Test that start() handles KeyboardInterrupt gracefully."""
        server = ProxyServer()

        with (
            patch("devrelay.proxy.options.Options"),
            patch("devrelay.proxy.dump.DumpMaster") as mock_dump_master,
        ):
            # Setup mocks
            mock_master_instance = MagicMock()
            mock_master_instance.run = AsyncMock(side_effect=KeyboardInterrupt)
            mock_dump_master.return_value = mock_master_instance

            # Run start (should not raise)
            await server.start()

            # Verify shutdown was called
            mock_master_instance.shutdown.assert_called_once()

    def test_run_calls_asyncio_run(self) -> None:
        """Test that run() calls asyncio.run with start()."""
        server = ProxyServer()

        with patch("devrelay.proxy.asyncio.run") as mock_asyncio_run:
            captured: dict[str, Coroutine[Any, Any, Any]] = {}

            def fake_asyncio_run(coro: Coroutine[Any, Any, Any]) -> None:
                # Ensure run() passes a coroutine and close it to avoid warnings.
                captured["coro"] = coro
                coro.close()

            mock_asyncio_run.side_effect = fake_asyncio_run

            server.run()

            # Verify asyncio.run was called with start coroutine
            mock_asyncio_run.assert_called_once()
            assert captured["coro"] is mock_asyncio_run.call_args[0][0]
