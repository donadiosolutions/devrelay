"""Tests for the devrelay CLI."""

from pathlib import Path
from unittest.mock import MagicMock, call, patch

from devrelay import cli


class TestDevRelayCLIClass:
    """Test cases for DevRelayCLI class."""

    def test_cli_init_creates_parser(self) -> None:
        """Test that CLI initialization creates argument parser."""
        cli_instance = cli.DevRelayCLI()
        assert cli_instance.parser is not None
        assert cli_instance.parser.description == "DevRelay - MITM proxy that removes CSP headers"

    def test_parse_args_with_defaults(self) -> None:
        """Test parsing arguments with defaults."""
        cli_instance = cli.DevRelayCLI()
        args = cli_instance.parse_args([])
        assert args.host == "127.0.0.1"
        assert args.port == 8080
        assert args.confdir is None

    def test_parse_args_with_custom_values(self) -> None:
        """Test parsing arguments with custom values."""
        cli_instance = cli.DevRelayCLI()
        args = cli_instance.parse_args(["--host", "0.0.0.0", "--port", "9090", "--confdir", "/tmp/certs"])
        assert args.host == "0.0.0.0"
        assert args.port == 9090
        assert args.confdir == Path("/tmp/certs")

    def test_display_startup_info(self) -> None:
        """Test display_startup_info outputs correct information."""
        cli_instance = cli.DevRelayCLI()
        with patch("builtins.print") as mock_print:
            cli_instance.display_startup_info("127.0.0.1", 8080, None)
            assert mock_print.call_count == 3
            mock_print.assert_has_calls(
                [
                    call("Starting DevRelay proxy on 127.0.0.1:8080"),
                    call(f"Certificate directory: {Path.home() / '.mitmproxy'}"),
                    call("\nPress Ctrl+C to stop the proxy\n"),
                ]
            )

    def test_display_startup_info_with_custom_confdir(self) -> None:
        """Test display_startup_info with custom confdir."""
        cli_instance = cli.DevRelayCLI()
        custom_confdir = Path("/tmp/custom")
        with patch("builtins.print") as mock_print:
            cli_instance.display_startup_info("0.0.0.0", 9090, custom_confdir)
            assert mock_print.call_count == 3
            mock_print.assert_has_calls(
                [
                    call("Starting DevRelay proxy on 0.0.0.0:9090"),
                    call(f"Certificate directory: {custom_confdir}"),
                    call("\nPress Ctrl+C to stop the proxy\n"),
                ]
            )

    def test_run_server_success(self) -> None:
        """Test run_server starts server successfully."""
        cli_instance = cli.DevRelayCLI()
        with patch("devrelay.cli.ProxyServer") as mock_proxy_server:
            mock_server_instance = MagicMock()
            mock_proxy_server.return_value = mock_server_instance

            result = cli_instance.run_server("127.0.0.1", 8080, None)

            mock_proxy_server.assert_called_once_with(host="127.0.0.1", port=8080, confdir=None)
            mock_server_instance.run.assert_called_once()
            assert result == 0

    def test_run_server_keyboard_interrupt(self) -> None:
        """Test run_server handles KeyboardInterrupt."""
        cli_instance = cli.DevRelayCLI()
        with patch("devrelay.cli.ProxyServer") as mock_proxy_server:
            mock_server_instance = MagicMock()
            mock_server_instance.run.side_effect = KeyboardInterrupt
            mock_proxy_server.return_value = mock_server_instance

            with patch("builtins.print"):
                result = cli_instance.run_server("127.0.0.1", 8080, None)

            assert result == 0

    def test_run_server_exception(self) -> None:
        """Test run_server handles exceptions."""
        cli_instance = cli.DevRelayCLI()
        with patch("devrelay.cli.ProxyServer") as mock_proxy_server:
            mock_server_instance = MagicMock()
            mock_server_instance.run.side_effect = Exception("Test error")
            mock_proxy_server.return_value = mock_server_instance

            with patch("builtins.print"):
                result = cli_instance.run_server("127.0.0.1", 8080, None)

            assert result == 1

    def test_execute_with_defaults(self) -> None:
        """Test execute method with default arguments."""
        cli_instance = cli.DevRelayCLI()
        with (
            patch.object(cli_instance, "parse_args") as mock_parse,
            patch.object(cli_instance, "display_startup_info") as mock_display,
            patch.object(cli_instance, "run_server") as mock_run,
        ):
            mock_args = MagicMock()
            mock_args.host = "127.0.0.1"
            mock_args.port = 8080
            mock_args.confdir = None
            mock_parse.return_value = mock_args
            mock_run.return_value = 0

            result = cli_instance.execute()

            mock_parse.assert_called_once_with(None)
            mock_display.assert_called_once_with("127.0.0.1", 8080, None)
            mock_run.assert_called_once_with("127.0.0.1", 8080, None)
            assert result == 0

    def test_execute_with_custom_args(self) -> None:
        """Test execute method with custom arguments."""
        cli_instance = cli.DevRelayCLI()
        with (
            patch.object(cli_instance, "parse_args") as mock_parse,
            patch.object(cli_instance, "display_startup_info") as mock_display,
            patch.object(cli_instance, "run_server") as mock_run,
        ):
            mock_args = MagicMock()
            mock_args.host = "0.0.0.0"
            mock_args.port = 9090
            mock_args.confdir = Path("/tmp/certs")
            mock_parse.return_value = mock_args
            mock_run.return_value = 0

            result = cli_instance.execute(["--host", "0.0.0.0"])

            mock_parse.assert_called_once_with(["--host", "0.0.0.0"])
            mock_display.assert_called_once_with("0.0.0.0", 9090, Path("/tmp/certs"))
            mock_run.assert_called_once_with("0.0.0.0", 9090, Path("/tmp/certs"))
            assert result == 0


class TestDevRelayCLI:
    """Test cases for devrelay CLI."""

    def test_main_starts_server_with_defaults(self) -> None:
        """Test that main() starts server with default arguments."""
        with (
            patch("devrelay.cli.ProxyServer") as mock_proxy_server,
            patch("sys.argv", ["cli.py"]),
        ):
            mock_server_instance = MagicMock()
            mock_proxy_server.return_value = mock_server_instance

            result = cli.main()

            # Verify ProxyServer was created with defaults
            mock_proxy_server.assert_called_once_with(
                host="127.0.0.1",
                port=8080,
                confdir=None,
            )

            # Verify run was called
            mock_server_instance.run.assert_called_once()

            # Verify exit code
            assert result == 0

    def test_main_starts_server_with_custom_args(self) -> None:
        """Test that main() starts server with custom arguments."""
        with (
            patch("devrelay.cli.ProxyServer") as mock_proxy_server,
            patch(
                "sys.argv",
                ["cli.py", "--host", "0.0.0.0", "--port", "9090"],
            ),
        ):
            mock_server_instance = MagicMock()
            mock_proxy_server.return_value = mock_server_instance

            result = cli.main()

            # Verify ProxyServer was created with custom args
            mock_proxy_server.assert_called_once_with(
                host="0.0.0.0",
                port=9090,
                confdir=None,
            )

            # Verify run was called
            mock_server_instance.run.assert_called_once()

            # Verify exit code
            assert result == 0

    def test_main_with_custom_confdir(self) -> None:
        """Test that main() handles custom confdir argument."""
        with (
            patch("devrelay.cli.ProxyServer") as mock_proxy_server,
            patch(
                "sys.argv",
                ["cli.py", "--confdir", "/tmp/custom-certs"],
            ),
        ):
            mock_server_instance = MagicMock()
            mock_proxy_server.return_value = mock_server_instance

            result = cli.main()

            # Verify ProxyServer was created with custom confdir
            call_args = mock_proxy_server.call_args[1]
            assert call_args["confdir"] == Path("/tmp/custom-certs")

            # Verify run was called
            mock_server_instance.run.assert_called_once()

            # Verify exit code
            assert result == 0

    def test_main_handles_keyboard_interrupt(self) -> None:
        """Test that main() handles KeyboardInterrupt gracefully."""
        with (
            patch("devrelay.cli.ProxyServer") as mock_proxy_server,
            patch("sys.argv", ["cli.py"]),
        ):
            mock_server_instance = MagicMock()
            mock_server_instance.run.side_effect = KeyboardInterrupt
            mock_proxy_server.return_value = mock_server_instance

            result = cli.main()

            # Verify exit code is 0
            assert result == 0

    def test_main_handles_exceptions(self) -> None:
        """Test that main() handles exceptions and returns error code."""
        with (
            patch("devrelay.cli.ProxyServer") as mock_proxy_server,
            patch("sys.argv", ["cli.py"]),
        ):
            mock_server_instance = MagicMock()
            mock_server_instance.run.side_effect = Exception("Test error")
            mock_proxy_server.return_value = mock_server_instance

            result = cli.main()

            # Verify exit code is 1
            assert result == 1

    def test_cli_entrypoint(self) -> None:
        """Test cli_entrypoint calls sys.exit with main() result."""
        with (
            patch("devrelay.cli.main") as mock_main,
            patch("sys.exit") as mock_exit,
        ):
            mock_main.return_value = 0
            try:
                cli.cli_entrypoint()
            except SystemExit:
                pass
            mock_main.assert_called_once()
            mock_exit.assert_called_once_with(0)


class TestMainModule:
    """Test cases for __main__ module."""

    def test_main_module_calls_cli_entrypoint(self) -> None:
        """Test that __main__ module calls cli_entrypoint when run as __main__."""
        import subprocess
        import sys

        # Run the module as __main__ using python -m
        result = subprocess.run(
            [sys.executable, "-m", "devrelay", "--help"],
            capture_output=True,
            text=True,
        )

        # Verify it executed successfully and shows help
        assert result.returncode == 0
        assert "DevRelay - MITM proxy" in result.stdout
        assert "--host" in result.stdout
        assert "--port" in result.stdout
