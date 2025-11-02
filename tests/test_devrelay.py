"""Tests for the devrelay CLI."""

from pathlib import Path
from unittest.mock import MagicMock, call, patch

from devrelay import cli


class TestDevRelayCLIClass:
    """Test cases for DevRelayCLI class."""

    def test_cli_init_creates_config_loader(self) -> None:
        """Test that CLI initialization creates config loader."""
        cli_instance = cli.DevRelayCLI()
        assert cli_instance.config_loader is not None
        assert cli_instance.config_loader.parser.description == "DevRelay - MITM proxy that removes CSP headers"

    def test_cli_init_with_custom_config_path(self) -> None:
        """Test that CLI initialization accepts custom config path."""
        custom_path = Path("/tmp/custom.yaml")
        cli_instance = cli.DevRelayCLI(config_path=custom_path)
        assert cli_instance.config_loader.config_path == custom_path

    def test_display_startup_info(self) -> None:
        """Test display_startup_info outputs correct information."""
        cli_instance = cli.DevRelayCLI()
        with patch("builtins.print") as mock_print:
            cli_instance.display_startup_info("127.0.0.1", 8080, Path.home() / ".mitmproxy")
            assert mock_print.call_count == 3
            mock_print.assert_has_calls(
                [
                    call("Starting DevRelay proxy on 127.0.0.1:8080"),
                    call(f"Certificate directory: {Path.home() / '.mitmproxy'}"),
                    call("\nPress Ctrl+C to stop the proxy\n"),
                ]
            )

    def test_display_startup_info_with_custom_certdir(self) -> None:
        """Test display_startup_info with custom certdir."""
        cli_instance = cli.DevRelayCLI()
        custom_certdir = Path("/tmp/custom")
        with patch("builtins.print") as mock_print:
            cli_instance.display_startup_info("0.0.0.0", 9090, custom_certdir)
            assert mock_print.call_count == 3
            mock_print.assert_has_calls(
                [
                    call("Starting DevRelay proxy on 0.0.0.0:9090"),
                    call(f"Certificate directory: {custom_certdir}"),
                    call("\nPress Ctrl+C to stop the proxy\n"),
                ]
            )

    def test_run_server_success(self) -> None:
        """Test run_server starts server successfully."""
        cli_instance = cli.DevRelayCLI()
        with patch("devrelay.cli.ProxyServer") as mock_proxy_server:
            mock_server_instance = MagicMock()
            mock_proxy_server.return_value = mock_server_instance

            result = cli_instance.run_server("127.0.0.1", 8080, Path.home() / ".mitmproxy")

            mock_proxy_server.assert_called_once_with(host="127.0.0.1", port=8080, certdir=Path.home() / ".mitmproxy")
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
                result = cli_instance.run_server("127.0.0.1", 8080, Path.home() / ".mitmproxy")

            assert result == 0

    def test_run_server_exception(self) -> None:
        """Test run_server handles exceptions."""
        cli_instance = cli.DevRelayCLI()
        with patch("devrelay.cli.ProxyServer") as mock_proxy_server:
            mock_server_instance = MagicMock()
            mock_server_instance.run.side_effect = Exception("Test error")
            mock_proxy_server.return_value = mock_server_instance

            with patch("builtins.print"):
                result = cli_instance.run_server("127.0.0.1", 8080, Path.home() / ".mitmproxy")

            assert result == 1

    def test_execute_with_defaults(self) -> None:
        """Test execute method with default arguments."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            cli_instance = cli.DevRelayCLI(config_path=config_path)
            with (
                patch.object(cli_instance, "display_startup_info") as mock_display,
                patch.object(cli_instance, "run_server") as mock_run,
            ):
                mock_run.return_value = 0

                result = cli_instance.execute([])

                mock_display.assert_called_once_with("127.0.0.1", 8080, Path.home() / ".mitmproxy")
                mock_run.assert_called_once_with("127.0.0.1", 8080, Path.home() / ".mitmproxy")
                assert result == 0

    def test_execute_with_custom_args(self) -> None:
        """Test execute method with custom arguments."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            cli_instance = cli.DevRelayCLI(config_path=config_path)
            with (
                patch.object(cli_instance, "display_startup_info") as mock_display,
                patch.object(cli_instance, "run_server") as mock_run,
            ):
                mock_run.return_value = 0

                result = cli_instance.execute(["--host", "0.0.0.0", "--port", "9090", "--certdir", "/tmp/certs"])

                mock_display.assert_called_once_with("0.0.0.0", 9090, Path("/tmp/certs"))
                mock_run.assert_called_once_with("0.0.0.0", 9090, Path("/tmp/certs"))
                assert result == 0

    def test_execute_with_config_error(self) -> None:
        """Test execute method handles configuration errors."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            cli_instance = cli.DevRelayCLI(config_path=config_path)

            with patch("builtins.print") as mock_print:
                result = cli_instance.execute(["--port", "99999"])

                # Should print error and return 1
                assert result == 1
                mock_print.assert_called_once()
                call_args = mock_print.call_args[0][0]
                assert "Configuration error:" in call_args
                assert "Port must be between 1 and 65535" in call_args


class TestDevRelayCLI:
    """Test cases for devrelay CLI."""

    def test_main_starts_server_with_defaults(self) -> None:
        """Test that main() starts server with default arguments."""
        with (
            patch("devrelay.cli.DevRelayCLI") as mock_cli_class,
            patch("sys.argv", ["cli.py"]),
        ):
            mock_cli_instance = MagicMock()
            mock_cli_class.return_value = mock_cli_instance
            mock_cli_instance.execute.return_value = 0

            result = cli.main()

            # Verify CLI was created and executed
            mock_cli_class.assert_called_once()
            mock_cli_instance.execute.assert_called_once()

            # Verify exit code
            assert result == 0

    def test_main_starts_server_with_custom_args(self) -> None:
        """Test that main() starts server with custom arguments."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            with patch(
                "sys.argv",
                ["cli.py", "--host", "0.0.0.0", "--port", "9090"],
            ):
                # Create a real CLI instance with temp config
                with patch.object(
                    cli.DevRelayCLI,
                    "__init__",
                    lambda self: setattr(self, "config_loader", None) or None,  # pyright: ignore
                ):
                    test_cli = cli.DevRelayCLI()
                    test_cli.config_loader = __import__("devrelay.config", fromlist=["ConfigLoader"]).ConfigLoader(
                        config_path=config_path
                    )

                    with (
                        patch.object(test_cli, "display_startup_info") as mock_display,
                        patch.object(test_cli, "run_server") as mock_run,
                    ):
                        mock_run.return_value = 0
                        result = test_cli.execute()

                        # Verify display was called with custom args
                        mock_display.assert_called_once_with("0.0.0.0", 9090, Path.home() / ".mitmproxy")
                        mock_run.assert_called_once_with("0.0.0.0", 9090, Path.home() / ".mitmproxy")

                        # Verify exit code
                        assert result == 0

    def test_main_with_custom_certdir(self) -> None:
        """Test that main() handles custom certdir argument."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            with patch(
                "sys.argv",
                ["cli.py", "--certdir", "/tmp/custom-certs"],
            ):
                # Create a real CLI instance with temp config
                with patch.object(
                    cli.DevRelayCLI,
                    "__init__",
                    lambda self: setattr(self, "config_loader", None) or None,  # pyright: ignore
                ):
                    test_cli = cli.DevRelayCLI()
                    test_cli.config_loader = __import__("devrelay.config", fromlist=["ConfigLoader"]).ConfigLoader(
                        config_path=config_path
                    )

                    with (
                        patch.object(test_cli, "display_startup_info") as mock_display,
                        patch.object(test_cli, "run_server") as mock_run,
                    ):
                        mock_run.return_value = 0
                        result = test_cli.execute()

                        # Verify display was called with custom certdir
                        call_args = mock_display.call_args[0]
                        assert call_args[2] == Path("/tmp/custom-certs")
                        assert result == 0

    def test_main_handles_keyboard_interrupt(self) -> None:
        """Test that main() handles KeyboardInterrupt gracefully."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            with (
                patch("devrelay.cli.ProxyServer") as mock_proxy_server,
                patch("sys.argv", ["cli.py"]),
            ):
                mock_server_instance = MagicMock()
                mock_server_instance.run.side_effect = KeyboardInterrupt
                mock_proxy_server.return_value = mock_server_instance

                # Create a real CLI instance with temp config
                test_cli = cli.DevRelayCLI(config_path=config_path)
                result = test_cli.execute()

                # Verify exit code is 0
                assert result == 0

    def test_main_handles_exceptions(self) -> None:
        """Test that main() handles exceptions and returns error code."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            with (
                patch("devrelay.cli.ProxyServer") as mock_proxy_server,
                patch("sys.argv", ["cli.py"]),
            ):
                mock_server_instance = MagicMock()
                mock_server_instance.run.side_effect = Exception("Test error")
                mock_proxy_server.return_value = mock_server_instance

                # Create a real CLI instance with temp config
                test_cli = cli.DevRelayCLI(config_path=config_path)

                with patch("builtins.print"):
                    result = test_cli.execute()

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
