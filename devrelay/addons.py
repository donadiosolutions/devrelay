"""DevRelay proxy addons for security header manipulation"""

from mitmproxy import http


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
