"""DevRelay proxy module for removing security headers and handling CORS."""

from devrelay.addons import (
    COEPRemoverAddon,
    COOPRemoverAddon,
    CORPInserterAddon,
    CORSInserterForWebhooksAddon,
    CORSPreflightForWebhooksAddon,
    CSPRemoverAddon,
)

__all__ = [
    "COEPRemoverAddon",
    "COOPRemoverAddon",
    "CORPInserterAddon",
    "CORSInserterForWebhooksAddon",
    "CORSPreflightForWebhooksAddon",
    "CSPRemoverAddon",
]
