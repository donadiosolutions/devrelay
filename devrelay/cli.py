"""DevRelay CLI"""

import argparse
import sys
from pathlib import Path
from typing import NoReturn

from devrelay.proxy import ProxyServer


class DevRelayCLI:
    """CLI for DevRelay proxy server."""

    def __init__(self) -> None:
        """Initialize the CLI with argument parser."""
        self.parser = argparse.ArgumentParser(
            description="DevRelay - MITM proxy that removes CSP headers",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        self._setup_arguments()

    def _setup_arguments(self) -> None:
        """Configure CLI arguments."""
        self.parser.add_argument(
            "--host",
            type=str,
            default="127.0.0.1",
            help="Host address to bind to",
        )
        self.parser.add_argument(
            "--port",
            type=int,
            default=8080,
            help="Port to listen on",
        )
        self.parser.add_argument(
            "--confdir",
            type=Path,
            default=None,
            help="Configuration directory for certificates (default: ~/.mitmproxy)",
        )

    def parse_args(self, args: list[str] | None = None) -> argparse.Namespace:
        """
        Parse command-line arguments.

        Args:
            args: Optional list of arguments to parse (defaults to sys.argv)

        Returns:
            Parsed arguments namespace
        """
        return self.parser.parse_args(args)

    def display_startup_info(self, host: str, port: int, confdir: Path | None) -> None:
        """
        Display startup information to the user.

        Args:
            host: Host address being used
            port: Port number being used
            confdir: Configuration directory path (or None for default)
        """
        print(f"Starting DevRelay proxy on {host}:{port}")
        print(f"Certificate directory: {confdir or Path.home() / '.mitmproxy'}")
        print("\nPress Ctrl+C to stop the proxy\n")

    def run_server(self, host: str, port: int, confdir: Path | None) -> int:
        """
        Start and run the proxy server.

        Args:
            host: Host address to bind to
            port: Port number to listen on
            confdir: Configuration directory for certificates

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            server = ProxyServer(
                host=host,
                port=port,
                confdir=confdir,
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
        parsed_args = self.parse_args(args)
        self.display_startup_info(parsed_args.host, parsed_args.port, parsed_args.confdir)
        return self.run_server(parsed_args.host, parsed_args.port, parsed_args.confdir)


def main() -> int:
    """Main CLI entry point."""
    cli = DevRelayCLI()
    return cli.execute()


def cli_entrypoint() -> NoReturn:
    """Entry point for console script."""
    sys.exit(main())


if __name__ == "__main__":
    cli_entrypoint()
