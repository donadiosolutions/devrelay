"""DevRelay CLI"""

import sys
from pathlib import Path
from typing import NoReturn

from devrelay.config import ConfigLoader
from devrelay.proxy import ProxyServer


class DevRelayCLI:
    """CLI for DevRelay proxy server."""

    def __init__(self, config_path: Path | None = None) -> None:
        """
        Initialize the CLI with configuration loader.

        Args:
            config_path: Optional path to YAML config file (default: ~/.mitmproxy/devrelay.yaml)
        """
        self.config_loader = ConfigLoader(config_path=config_path)

    def display_startup_info(self, host: str, port: int, certdir: Path, disabled_addons: list[str]) -> None:
        """
        Display startup information to the user.

        Args:
            host: Host address being used
            port: Port number being used
            certdir: Certificate directory path
            disabled_addons: List of disabled addon names
        """
        print(f"Starting DevRelay proxy on {host}:{port}")
        print(f"Certificate directory: {certdir}")
        if disabled_addons:
            print(f"Disabled addons: {', '.join(disabled_addons)}")
        print("\nPress Ctrl+C to stop the proxy\n")

    def run_server(self, host: str, port: int, certdir: Path, disabled_addons: list[str]) -> int:
        """
        Start and run the proxy server.

        Args:
            host: Host address to bind to
            port: Port number to listen on
            certdir: Certificate directory
            disabled_addons: List of addon class names to disable

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            server = ProxyServer(
                host=host,
                port=port,
                certdir=certdir,
                disabled_addons=disabled_addons,
            )
            server.run()
        except KeyboardInterrupt:
            print("\nShutting down...")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        return 0

    def execute(self, args: list[str] | None = None) -> int:
        """
        Execute the CLI with the given arguments.

        Args:
            args: Optional list of arguments (defaults to sys.argv)

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            config = self.config_loader.get_config(args)
            self.display_startup_info(config.host, config.port, config.certdir, config.disabled_addons)
            return self.run_server(config.host, config.port, config.certdir, config.disabled_addons)
        except ValueError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            return 1


def main() -> int:
    """Main CLI entry point."""
    cli = DevRelayCLI()
    return cli.execute()


def cli_entrypoint() -> NoReturn:
    """Entry point for console script."""
    sys.exit(main())


if __name__ == "__main__":
    cli_entrypoint()
