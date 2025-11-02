"""DevRelay proxy addons for security header manipulation"""

import difflib
from mitmproxy import http

# Addon name mapping for user-friendly names
# Maps both short names and full class names to canonical class names
ADDON_NAME_MAP = {
    # Short names (case will be normalized to uppercase for lookup)
    "CSP": "CSPRemoverAddon",
    "COEP": "COEPRemoverAddon",
    "COOP": "COOPRemoverAddon",
    "CORP": "CORPInserterAddon",
    "CORSINSERTER": "CORSInserterForWebhooksAddon",
    "CORSPREFLIGHT": "CORSPreflightForWebhooksAddon",
    # Full class names (for completeness)
    "CSPREMOVERADDON": "CSPRemoverAddon",
    "COEPREMOVERADDON": "COEPRemoverAddon",
    "COOPREMOVERADDON": "COOPRemoverAddon",
    "CORPINSERTERADDON": "CORPInserterAddon",
    "CORSINSERTERFORWEBHOOKSADDON": "CORSInserterForWebhooksAddon",
    "CORSPREFLIGHTFORWEBHOOKSADDON": "CORSPreflightForWebhooksAddon",
}

# All valid addon class names
ALL_ADDON_NAMES = [
    "CSPRemoverAddon",
    "COEPRemoverAddon",
    "COOPRemoverAddon",
    "CORPInserterAddon",
    "CORSInserterForWebhooksAddon",
    "CORSPreflightForWebhooksAddon",
]


def validate_addon_names(addon_names: list[str]) -> list[str]:
    """
    Validate and normalize addon names to canonical class names.

    Accepts both short names (e.g., "CSP", "COEP") and full class names
    (e.g., "CSPRemoverAddon"). Case-insensitive matching is supported.

    Args:
        addon_names: List of addon names to validate

    Returns:
        List of canonical addon class names

    Raises:
        ValueError: If any addon name is invalid, with a suggestion for the first invalid name
    """
    validated = []

    for name in addon_names:
        # Normalize to uppercase for case-insensitive lookup
        normalized = name.upper()

        # Check if it's a valid addon name
        if normalized in ADDON_NAME_MAP:
            canonical_name = ADDON_NAME_MAP[normalized]
            validated.append(canonical_name)
        else:
            # Invalid name - provide a suggestion using fuzzy matching
            # Get all possible input names (both short and full)
            all_possible_names = list(ADDON_NAME_MAP.keys())

            # Find close matches (case-insensitive)
            close_matches = difflib.get_close_matches(normalized, all_possible_names, n=1, cutoff=0.6)

            if close_matches:
                # Suggest the canonical class name for the close match
                suggested_canonical = ADDON_NAME_MAP[close_matches[0]]
                # Find a user-friendly version (prefer short names)
                user_friendly = None
                for key, value in ADDON_NAME_MAP.items():
                    if value == suggested_canonical and len(key) <= 15:  # Prefer short names
                        user_friendly = key
                        break
                if user_friendly is None:
                    user_friendly = suggested_canonical

                raise ValueError(f"Unknown addon '{name}'. Did you mean '{user_friendly}'?")
            else:
                # No close match - list all valid options
                valid_short_names = ["CSP", "COEP", "COOP", "CORP", "CORSInserter", "CORSPreflight"]
                raise ValueError(f"Unknown addon '{name}'. Valid addons: {', '.join(valid_short_names)}")

    return validated


class CSPRemoverAddon:
    """
    Addon that removes Content-Security-Policy headers from HTTP responses.

    This addon intercepts all HTTP responses and removes any CSP-related headers
    to allow modification of web content that would otherwise be restricted.
    """

    def response(self, flow: http.HTTPFlow) -> None:
        """
        Process HTTP response and remove CSP headers.

        Args:
            flow: The HTTP flow containing the request and response.
        """
        if flow.response is None:
            return

        # Headers to remove (case-insensitive)
        csp_headers = [
            "content-security-policy",
            "content-security-policy-report-only",
        ]

        # Remove CSP headers from response
        for header in csp_headers:
            if header in flow.response.headers:
                del flow.response.headers[header]


class CORSPreflightForWebhooksAddon:
    """
    Addon that rewrites failed OPTIONS requests to return permissive CORS headers.

    This addon intercepts HTTP OPTIONS requests that returned with 405 Method
    Not Allowed and rewrites them to return 204 No Content with CORS headers
    that allow any origin, method, and headers. This is useful for testing
    webhooks that don't properly support CORS preflight requests.
    """

    def response(self, flow: http.HTTPFlow) -> None:
        """
        Process HTTP response and rewrite failed OPTIONS requests.

        Args:
            flow: The HTTP flow containing the request and response.
        """
        if flow.response is None:
            return

        # Only handle OPTIONS requests that returned 405 Method Not Allowed
        if flow.request.method != "OPTIONS":
            return

        if flow.response.status_code != 405:
            return

        # Rewrite the response to 204 No Content
        flow.response.status_code = 204
        flow.response.reason = "No Content"

        # Clear the response body
        flow.response.content = b""

        # Add permissive CORS headers
        flow.response.headers["Access-Control-Allow-Origin"] = "*"
        flow.response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
        flow.response.headers["Access-Control-Allow-Headers"] = "*"
        flow.response.headers["Access-Control-Max-Age"] = "86400"
        flow.response.headers["Access-Control-Expose-Headers"] = "*"


class COEPRemoverAddon:
    """
    Addon that removes Cross-Origin-Embedder-Policy headers from HTTP responses.

    This addon intercepts all HTTP responses and removes any COEP-related headers
    to allow embedding of cross-origin resources that would otherwise be blocked.
    """

    def response(self, flow: http.HTTPFlow) -> None:
        """
        Process HTTP response and remove COEP headers.

        Args:
            flow: The HTTP flow containing the request and response.
        """
        if flow.response is None:
            return

        # Headers to remove (case-insensitive)
        coep_headers = [
            "cross-origin-embedder-policy",
            "cross-origin-embedder-policy-report-only",
        ]

        # Remove COEP headers from response
        for header in coep_headers:
            if header in flow.response.headers:
                del flow.response.headers[header]


class COOPRemoverAddon:
    """
    Addon that removes Cross-Origin-Opener-Policy headers from HTTP responses.

    This addon intercepts all HTTP responses and removes any COOP-related headers
    to allow cross-origin window interactions that would otherwise be restricted.
    """

    def response(self, flow: http.HTTPFlow) -> None:
        """
        Process HTTP response and remove COOP headers.

        Args:
            flow: The HTTP flow containing the request and response.
        """
        if flow.response is None:
            return

        # Headers to remove (case-insensitive)
        coop_headers = [
            "cross-origin-opener-policy",
            "cross-origin-opener-policy-report-only",
        ]

        # Remove COOP headers from response
        for header in coop_headers:
            if header in flow.response.headers:
                del flow.response.headers[header]


class CORPInserterAddon:
    """
    Addon that adds Cross-Origin-Resource-Policy header to successful mutation requests.

    This addon intercepts HTTP responses to POST, PUT, PATCH, or DELETE requests
    that returned with 1XX or 2XX status codes and adds the CORP header with
    value 'cross-origin' to allow cross-origin resource sharing.
    """

    def response(self, flow: http.HTTPFlow) -> None:
        """
        Process HTTP response and add CORP header for successful mutations.

        Args:
            flow: The HTTP flow containing the request and response.
        """
        if flow.response is None:
            return

        # Only handle mutation methods
        mutation_methods = ["POST", "PUT", "PATCH", "DELETE"]
        if flow.request.method not in mutation_methods:
            return

        # Only handle successful responses (1XX or 2XX)
        status_code = flow.response.status_code
        if not (100 <= status_code < 300):
            return

        # Add Cross-Origin-Resource-Policy header
        flow.response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"


class CORSInserterForWebhooksAddon:
    """
    Addon that adds permissive CORS headers to successful mutation requests.

    This addon intercepts HTTP responses to POST, PUT, PATCH, or DELETE requests
    that returned with 1XX or 2XX status codes and adds permissive CORS headers
    to allow cross-origin requests from any origin.
    """

    def response(self, flow: http.HTTPFlow) -> None:
        """
        Process HTTP response and add CORS headers for successful mutations.

        Args:
            flow: The HTTP flow containing the request and response.
        """
        if flow.response is None:
            return

        # Only handle mutation methods
        mutation_methods = ["POST", "PUT", "PATCH", "DELETE"]
        if flow.request.method not in mutation_methods:
            return

        # Only handle successful responses (1XX or 2XX)
        status_code = flow.response.status_code
        if not (100 <= status_code < 300):
            return

        # Add permissive CORS headers
        flow.response.headers["Access-Control-Allow-Origin"] = "*"
        flow.response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
        flow.response.headers["Access-Control-Allow-Headers"] = "*"
        flow.response.headers["Access-Control-Max-Age"] = "86400"
        flow.response.headers["Access-Control-Expose-Headers"] = "*"
