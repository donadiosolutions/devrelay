"""DevRelay proxy server configuration and startup."""

import asyncio
from pathlib import Path

from mitmproxy import options
from mitmproxy.tools import dump

from devrelay.addons import (
    COEPRemoverAddon,
    COOPRemoverAddon,
    CORPInserterAddon,
    CORSInserterForWebhooksAddon,
    CORSPreflightForWebhooksAddon,
    CSPRemoverAddon,
)


class ProxyServer:
    """
    MITM proxy server that removes security headers for easier testing.

    Configured to listen on port 8080 with support for:
    - TLS 1.2 or greater
    - HTTP/2 and HTTP/3
    - WebSocket connections
    - Certificate storage in ~/.mitmproxy

    Enabled addons:
    - CSPRemoverAddon: Removes Content-Security-Policy headers
    - COEPRemoverAddon: Removes Cross-Origin-Embedder-Policy headers
    - COOPRemoverAddon: Removes Cross-Origin-Opener-Policy headers
    - CORPInserterAddon: Adds Cross-Origin-Resource-Policy header to successful mutations
    - CORSInserterForWebhooksAddon: Adds CORS headers to successful mutations
    - CORSPreflightForWebhooksAddon: Rewrites failed OPTIONS requests with CORS headers
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        certdir: Path = Path.home() / ".mitmproxy",
        disabled_addons: list[str] | None = None,
    ) -> None:
        """
        Initialize the proxy server.

        Args:
            host: Host address to bind to (default: 127.0.0.1)
            port: Port to listen on (default: 8080)
            certdir: Certificate directory (default: ~/.mitmproxy)
            disabled_addons: List of addon class names to disable (default: None)
        """
        self.host = host
        self.port = port
        self.certdir = certdir
        self.disabled_addons = disabled_addons or []

    async def start(self) -> None:
        """Start the proxy server."""
        # Configure mitmproxy options
        opts = options.Options(
            listen_host=self.host,
            listen_port=self.port,
            confdir=str(self.certdir),
            # TLS settings
            ssl_insecure=False,  # Verify upstream certificates
            # Protocol support
            http2=True,  # Enable HTTP/2
            http3=True,  # Enable HTTP/3
            websocket=True,  # Enable WebSocket
        )

        # Create master with our addons
        master = dump.DumpMaster(
            opts,
            with_termlog=True,
            with_dumper=False,
        )

        # Define all available addons
        available_addons = {
            "CSPRemoverAddon": CSPRemoverAddon(),
            "COEPRemoverAddon": COEPRemoverAddon(),
            "COOPRemoverAddon": COOPRemoverAddon(),
            "CORPInserterAddon": CORPInserterAddon(),
            "CORSInserterForWebhooksAddon": CORSInserterForWebhooksAddon(),
            "CORSPreflightForWebhooksAddon": CORSPreflightForWebhooksAddon(),
        }

        # Load only enabled addons (not in disabled list)
        for addon_name, addon_instance in available_addons.items():
            if addon_name not in self.disabled_addons:
                master.addons.add(addon_instance)

        try:
            await master.run()
        except KeyboardInterrupt:
            master.shutdown()

    def run(self) -> None:
        """Run the proxy server (blocking)."""
        asyncio.run(self.start())
