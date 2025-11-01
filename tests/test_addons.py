"""
Tests for the addons module.

Tests CSPRemoverAddon, COEPRemoverAddon, COOPRemoverAddon, CORPInserterAddon, CORSInserterForWebhooksAddon,
and CORSPreflightForWebhooksAddon.
"""

from mitmproxy.test import tflow

from devrelay.addons import (
    COEPRemoverAddon,
    COOPRemoverAddon,
    CORPInserterAddon,
    CORSInserterForWebhooksAddon,
    CORSPreflightForWebhooksAddon,
    CSPRemoverAddon,
)


class TestCSPRemoverAddon:
    """Test cases for CSPRemoverAddon."""

    def test_removes_csp_header(self) -> None:
        """Test that Content-Security-Policy header is removed."""
        addon = CSPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add CSP header to response
        assert flow.response is not None
        flow.response.headers["Content-Security-Policy"] = "default-src 'self'"

        # Process the response
        addon.response(flow)

        # Verify CSP header was removed
        assert "content-security-policy" not in flow.response.headers

    def test_removes_csp_report_only_header(self) -> None:
        """Test that Content-Security-Policy-Report-Only header is removed."""
        addon = CSPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add CSP-Report-Only header to response
        assert flow.response is not None
        flow.response.headers["Content-Security-Policy-Report-Only"] = "default-src 'self'"

        # Process the response
        addon.response(flow)

        # Verify CSP-Report-Only header was removed
        assert "content-security-policy-report-only" not in flow.response.headers

    def test_removes_multiple_csp_headers(self) -> None:
        """Test that multiple CSP headers are removed."""
        addon = CSPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add both CSP headers to response
        assert flow.response is not None
        flow.response.headers["Content-Security-Policy"] = "default-src 'self'"
        flow.response.headers["Content-Security-Policy-Report-Only"] = "default-src 'self'"

        # Process the response
        addon.response(flow)

        # Verify both CSP headers were removed
        assert "content-security-policy" not in flow.response.headers
        assert "content-security-policy-report-only" not in flow.response.headers

    def test_handles_flow_without_response(self) -> None:
        """Test that addon handles flows without responses gracefully."""
        addon = CSPRemoverAddon()
        flow = tflow.tflow(resp=False)

        # Should not raise an exception
        addon.response(flow)

    def test_preserves_other_headers(self) -> None:
        """Test that other headers are preserved."""
        addon = CSPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add various headers including CSP
        assert flow.response is not None
        flow.response.headers["Content-Security-Policy"] = "default-src 'self'"
        flow.response.headers["Content-Type"] = "text/html"
        flow.response.headers["Cache-Control"] = "no-cache"

        # Process the response
        addon.response(flow)

        # Verify CSP was removed but others preserved
        assert "content-security-policy" not in flow.response.headers
        assert flow.response.headers["Content-Type"] == "text/html"
        assert flow.response.headers["Cache-Control"] == "no-cache"

    def test_handles_flow_without_csp_headers(self) -> None:
        """Test that flows without CSP headers are handled correctly."""
        addon = CSPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add non-CSP headers
        assert flow.response is not None
        flow.response.headers["Content-Type"] = "text/html"

        # Process the response
        addon.response(flow)

        # Verify Content-Type is still present
        assert flow.response.headers["Content-Type"] == "text/html"


class TestCORSPreflightForWebhooksAddon:
    """Test cases for CORSPreflightForWebhooksAddon."""

    def test_rewrites_405_options_request(self) -> None:
        """Test that OPTIONS request with 405 is rewritten to 204."""
        addon = CORSPreflightForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"OPTIONS"),
            resp=tflow.tresp(status_code=405),
        )

        # Process the response
        addon.response(flow)

        # Verify status was changed to 204
        assert flow.response is not None
        assert flow.response.status_code == 204
        assert flow.response.reason == "No Content"

    def test_adds_cors_headers(self) -> None:
        """Test that CORS headers are added to rewritten response."""
        addon = CORSPreflightForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"OPTIONS"),
            resp=tflow.tresp(status_code=405),
        )

        # Process the response
        addon.response(flow)

        # Verify CORS headers were added
        assert flow.response is not None
        assert flow.response.headers["Access-Control-Allow-Origin"] == "*"
        assert flow.response.headers["Access-Control-Allow-Methods"] == "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
        assert flow.response.headers["Access-Control-Allow-Headers"] == "*"
        assert flow.response.headers["Access-Control-Max-Age"] == "86400"
        assert flow.response.headers["Access-Control-Expose-Headers"] == "*"

    def test_clears_response_body(self) -> None:
        """Test that response body is cleared."""
        addon = CORSPreflightForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"OPTIONS"),
            resp=tflow.tresp(status_code=405, content=b"Method Not Allowed"),
        )

        # Process the response
        addon.response(flow)

        # Verify body was cleared
        assert flow.response is not None
        assert flow.response.content == b""

    def test_ignores_non_options_requests(self) -> None:
        """Test that non-OPTIONS requests are ignored."""
        addon = CORSPreflightForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"GET"),
            resp=tflow.tresp(status_code=405),
        )

        # Store original status
        assert flow.response is not None
        original_status = flow.response.status_code

        # Process the response
        addon.response(flow)

        # Verify nothing changed
        assert flow.response is not None
        assert flow.response.status_code == original_status
        assert "Access-Control-Allow-Origin" not in flow.response.headers

    def test_ignores_options_with_non_405_status(self) -> None:
        """Test that OPTIONS requests with non-405 status are ignored."""
        addon = CORSPreflightForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"OPTIONS"),
            resp=tflow.tresp(status_code=200),
        )

        # Store original status
        assert flow.response is not None
        original_status = flow.response.status_code

        # Process the response
        addon.response(flow)

        # Verify nothing changed
        assert flow.response is not None
        assert flow.response.status_code == original_status
        assert "Access-Control-Allow-Origin" not in flow.response.headers

    def test_ignores_options_with_404_status(self) -> None:
        """Test that OPTIONS requests with 404 status are ignored."""
        addon = CORSPreflightForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"OPTIONS"),
            resp=tflow.tresp(status_code=404),
        )

        # Process the response
        addon.response(flow)

        # Verify nothing changed
        assert flow.response is not None
        assert flow.response.status_code == 404
        assert "Access-Control-Allow-Origin" not in flow.response.headers

    def test_handles_flow_without_response(self) -> None:
        """Test that addon handles flows without responses gracefully."""
        addon = CORSPreflightForWebhooksAddon()
        flow = tflow.tflow(resp=False)

        # Should not raise an exception
        addon.response(flow)

    def test_post_request_with_405_ignored(self) -> None:
        """Test that POST request with 405 is not modified."""
        addon = CORSPreflightForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=405),
        )

        # Process the response
        addon.response(flow)

        # Verify nothing changed (only OPTIONS should be rewritten)
        assert flow.response is not None
        assert flow.response.status_code == 405
        assert "Access-Control-Allow-Origin" not in flow.response.headers

    def test_preserves_existing_headers(self) -> None:
        """Test that existing headers are preserved when rewriting."""
        addon = CORSPreflightForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"OPTIONS"),
            resp=tflow.tresp(status_code=405),
        )

        # Add some existing headers
        assert flow.response is not None
        flow.response.headers["Server"] = "nginx/1.0"
        flow.response.headers["X-Custom-Header"] = "custom-value"

        # Process the response
        addon.response(flow)

        # Verify existing headers were preserved
        assert flow.response.headers["Server"] == "nginx/1.0"
        assert flow.response.headers["X-Custom-Header"] == "custom-value"
        # And CORS headers were added
        assert flow.response.headers["Access-Control-Allow-Origin"] == "*"


class TestCOEPRemoverAddon:
    """Test cases for COEPRemoverAddon."""

    def test_removes_coep_header(self) -> None:
        """Test that Cross-Origin-Embedder-Policy header is removed."""
        addon = COEPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add COEP header to response
        assert flow.response is not None
        flow.response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        # Process the response
        addon.response(flow)

        # Verify COEP header was removed
        assert "cross-origin-embedder-policy" not in flow.response.headers

    def test_removes_coep_report_only_header(self) -> None:
        """Test that Cross-Origin-Embedder-Policy-Report-Only header is removed."""
        addon = COEPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add COEP-Report-Only header to response
        assert flow.response is not None
        flow.response.headers["Cross-Origin-Embedder-Policy-Report-Only"] = "require-corp"

        # Process the response
        addon.response(flow)

        # Verify COEP-Report-Only header was removed
        assert "cross-origin-embedder-policy-report-only" not in flow.response.headers

    def test_removes_multiple_coep_headers(self) -> None:
        """Test that multiple COEP headers are removed."""
        addon = COEPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add both COEP headers to response
        assert flow.response is not None
        flow.response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        flow.response.headers["Cross-Origin-Embedder-Policy-Report-Only"] = "require-corp"

        # Process the response
        addon.response(flow)

        # Verify both COEP headers were removed
        assert "cross-origin-embedder-policy" not in flow.response.headers
        assert "cross-origin-embedder-policy-report-only" not in flow.response.headers

    def test_handles_flow_without_response(self) -> None:
        """Test that addon handles flows without responses gracefully."""
        addon = COEPRemoverAddon()
        flow = tflow.tflow(resp=False)

        # Should not raise an exception
        addon.response(flow)

    def test_preserves_other_headers(self) -> None:
        """Test that other headers are preserved."""
        addon = COEPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add various headers including COEP
        assert flow.response is not None
        flow.response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        flow.response.headers["Content-Type"] = "text/html"
        flow.response.headers["Cache-Control"] = "no-cache"

        # Process the response
        addon.response(flow)

        # Verify COEP was removed but others preserved
        assert "cross-origin-embedder-policy" not in flow.response.headers
        assert flow.response.headers["Content-Type"] == "text/html"
        assert flow.response.headers["Cache-Control"] == "no-cache"

    def test_handles_flow_without_coep_headers(self) -> None:
        """Test that flows without COEP headers are handled correctly."""
        addon = COEPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add non-COEP headers
        assert flow.response is not None
        flow.response.headers["Content-Type"] = "text/html"

        # Process the response
        addon.response(flow)

        # Verify Content-Type is still present
        assert flow.response.headers["Content-Type"] == "text/html"


class TestCOOPRemoverAddon:
    """Test cases for COOPRemoverAddon."""

    def test_removes_coop_header(self) -> None:
        """Test that Cross-Origin-Opener-Policy header is removed."""
        addon = COOPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add COOP header to response
        assert flow.response is not None
        flow.response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        # Process the response
        addon.response(flow)

        # Verify COOP header was removed
        assert "cross-origin-opener-policy" not in flow.response.headers

    def test_removes_coop_report_only_header(self) -> None:
        """Test that Cross-Origin-Opener-Policy-Report-Only header is removed."""
        addon = COOPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add COOP-Report-Only header to response
        assert flow.response is not None
        flow.response.headers["Cross-Origin-Opener-Policy-Report-Only"] = "same-origin"

        # Process the response
        addon.response(flow)

        # Verify COOP-Report-Only header was removed
        assert "cross-origin-opener-policy-report-only" not in flow.response.headers

    def test_removes_multiple_coop_headers(self) -> None:
        """Test that multiple COOP headers are removed."""
        addon = COOPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add both COOP headers to response
        assert flow.response is not None
        flow.response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        flow.response.headers["Cross-Origin-Opener-Policy-Report-Only"] = "same-origin"

        # Process the response
        addon.response(flow)

        # Verify both COOP headers were removed
        assert "cross-origin-opener-policy" not in flow.response.headers
        assert "cross-origin-opener-policy-report-only" not in flow.response.headers

    def test_handles_flow_without_response(self) -> None:
        """Test that addon handles flows without responses gracefully."""
        addon = COOPRemoverAddon()
        flow = tflow.tflow(resp=False)

        # Should not raise an exception
        addon.response(flow)

    def test_preserves_other_headers(self) -> None:
        """Test that other headers are preserved."""
        addon = COOPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add various headers including COOP
        assert flow.response is not None
        flow.response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        flow.response.headers["Content-Type"] = "text/html"
        flow.response.headers["Cache-Control"] = "no-cache"

        # Process the response
        addon.response(flow)

        # Verify COOP was removed but others preserved
        assert "cross-origin-opener-policy" not in flow.response.headers
        assert flow.response.headers["Content-Type"] == "text/html"
        assert flow.response.headers["Cache-Control"] == "no-cache"

    def test_handles_flow_without_coop_headers(self) -> None:
        """Test that flows without COOP headers are handled correctly."""
        addon = COOPRemoverAddon()
        flow = tflow.tflow(resp=True)

        # Add non-COOP headers
        assert flow.response is not None
        flow.response.headers["Content-Type"] = "text/html"

        # Process the response
        addon.response(flow)

        # Verify Content-Type is still present
        assert flow.response.headers["Content-Type"] == "text/html"


class TestCORPInserterAddon:
    """Test cases for CORPInserterAddon."""

    def test_adds_corp_header_for_post_200(self) -> None:
        """Test that CORP header is added for POST with 200 status."""
        addon = CORPInserterAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=200),
        )

        # Process the response
        addon.response(flow)

        # Verify CORP header was added
        assert flow.response is not None
        assert flow.response.headers["Cross-Origin-Resource-Policy"] == "cross-origin"

    def test_adds_corp_header_for_put_201(self) -> None:
        """Test that CORP header is added for PUT with 201 status."""
        addon = CORPInserterAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"PUT"),
            resp=tflow.tresp(status_code=201),
        )

        # Process the response
        addon.response(flow)

        # Verify CORP header was added
        assert flow.response is not None
        assert flow.response.headers["Cross-Origin-Resource-Policy"] == "cross-origin"

    def test_adds_corp_header_for_patch_204(self) -> None:
        """Test that CORP header is added for PATCH with 204 status."""
        addon = CORPInserterAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"PATCH"),
            resp=tflow.tresp(status_code=204),
        )

        # Process the response
        addon.response(flow)

        # Verify CORP header was added
        assert flow.response is not None
        assert flow.response.headers["Cross-Origin-Resource-Policy"] == "cross-origin"

    def test_adds_corp_header_for_delete_200(self) -> None:
        """Test that CORP header is added for DELETE with 200 status."""
        addon = CORPInserterAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"DELETE"),
            resp=tflow.tresp(status_code=200),
        )

        # Process the response
        addon.response(flow)

        # Verify CORP header was added
        assert flow.response is not None
        assert flow.response.headers["Cross-Origin-Resource-Policy"] == "cross-origin"

    def test_adds_corp_header_for_post_1xx(self) -> None:
        """Test that CORP header is added for POST with 1XX status."""
        addon = CORPInserterAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=100),
        )

        # Process the response
        addon.response(flow)

        # Verify CORP header was added
        assert flow.response is not None
        assert flow.response.headers["Cross-Origin-Resource-Policy"] == "cross-origin"

    def test_ignores_get_request(self) -> None:
        """Test that CORP header is NOT added for GET requests."""
        addon = CORPInserterAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"GET"),
            resp=tflow.tresp(status_code=200),
        )

        # Process the response
        addon.response(flow)

        # Verify CORP header was NOT added
        assert flow.response is not None
        assert "Cross-Origin-Resource-Policy" not in flow.response.headers

    def test_ignores_post_with_404(self) -> None:
        """Test that CORP header is NOT added for POST with 404 status."""
        addon = CORPInserterAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=404),
        )

        # Process the response
        addon.response(flow)

        # Verify CORP header was NOT added
        assert flow.response is not None
        assert "Cross-Origin-Resource-Policy" not in flow.response.headers

    def test_ignores_post_with_500(self) -> None:
        """Test that CORP header is NOT added for POST with 500 status."""
        addon = CORPInserterAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=500),
        )

        # Process the response
        addon.response(flow)

        # Verify CORP header was NOT added
        assert flow.response is not None
        assert "Cross-Origin-Resource-Policy" not in flow.response.headers

    def test_ignores_post_with_301(self) -> None:
        """Test that CORP header is NOT added for POST with 301 status."""
        addon = CORPInserterAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=301),
        )

        # Process the response
        addon.response(flow)

        # Verify CORP header was NOT added
        assert flow.response is not None
        assert "Cross-Origin-Resource-Policy" not in flow.response.headers

    def test_handles_flow_without_response(self) -> None:
        """Test that addon handles flows without responses gracefully."""
        addon = CORPInserterAddon()
        flow = tflow.tflow(resp=False)

        # Should not raise an exception
        addon.response(flow)

    def test_preserves_existing_headers(self) -> None:
        """Test that existing headers are preserved."""
        addon = CORPInserterAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=200),
        )

        # Add existing headers
        assert flow.response is not None
        flow.response.headers["Content-Type"] = "application/json"
        flow.response.headers["Cache-Control"] = "no-cache"

        # Process the response
        addon.response(flow)

        # Verify existing headers were preserved
        assert flow.response.headers["Content-Type"] == "application/json"
        assert flow.response.headers["Cache-Control"] == "no-cache"
        # And CORP header was added
        assert flow.response.headers["Cross-Origin-Resource-Policy"] == "cross-origin"


class TestCORSInserterForWebhooksAddon:
    """Test cases for CORSInserterForWebhooksAddon."""

    def test_adds_cors_headers_for_post_200(self) -> None:
        """Test that CORS headers are added for POST with 200 status."""
        addon = CORSInserterForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=200),
        )

        # Process the response
        addon.response(flow)

        # Verify CORS headers were added
        assert flow.response is not None
        assert flow.response.headers["Access-Control-Allow-Origin"] == "*"
        assert flow.response.headers["Access-Control-Allow-Methods"] == "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
        assert flow.response.headers["Access-Control-Allow-Headers"] == "*"
        assert flow.response.headers["Access-Control-Max-Age"] == "86400"
        assert flow.response.headers["Access-Control-Expose-Headers"] == "*"

    def test_adds_cors_headers_for_put_201(self) -> None:
        """Test that CORS headers are added for PUT with 201 status."""
        addon = CORSInserterForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"PUT"),
            resp=tflow.tresp(status_code=201),
        )

        # Process the response
        addon.response(flow)

        # Verify CORS headers were added
        assert flow.response is not None
        assert flow.response.headers["Access-Control-Allow-Origin"] == "*"

    def test_adds_cors_headers_for_patch_204(self) -> None:
        """Test that CORS headers are added for PATCH with 204 status."""
        addon = CORSInserterForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"PATCH"),
            resp=tflow.tresp(status_code=204),
        )

        # Process the response
        addon.response(flow)

        # Verify CORS headers were added
        assert flow.response is not None
        assert flow.response.headers["Access-Control-Allow-Origin"] == "*"

    def test_adds_cors_headers_for_delete_200(self) -> None:
        """Test that CORS headers are added for DELETE with 200 status."""
        addon = CORSInserterForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"DELETE"),
            resp=tflow.tresp(status_code=200),
        )

        # Process the response
        addon.response(flow)

        # Verify CORS headers were added
        assert flow.response is not None
        assert flow.response.headers["Access-Control-Allow-Origin"] == "*"

    def test_adds_cors_headers_for_post_1xx(self) -> None:
        """Test that CORS headers are added for POST with 1XX status."""
        addon = CORSInserterForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=100),
        )

        # Process the response
        addon.response(flow)

        # Verify CORS headers were added
        assert flow.response is not None
        assert flow.response.headers["Access-Control-Allow-Origin"] == "*"

    def test_ignores_get_request(self) -> None:
        """Test that CORS headers are NOT added for GET requests."""
        addon = CORSInserterForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"GET"),
            resp=tflow.tresp(status_code=200),
        )

        # Process the response
        addon.response(flow)

        # Verify CORS headers were NOT added
        assert flow.response is not None
        assert "Access-Control-Allow-Origin" not in flow.response.headers

    def test_ignores_post_with_404(self) -> None:
        """Test that CORS headers are NOT added for POST with 404 status."""
        addon = CORSInserterForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=404),
        )

        # Process the response
        addon.response(flow)

        # Verify CORS headers were NOT added
        assert flow.response is not None
        assert "Access-Control-Allow-Origin" not in flow.response.headers

    def test_ignores_post_with_500(self) -> None:
        """Test that CORS headers are NOT added for POST with 500 status."""
        addon = CORSInserterForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=500),
        )

        # Process the response
        addon.response(flow)

        # Verify CORS headers were NOT added
        assert flow.response is not None
        assert "Access-Control-Allow-Origin" not in flow.response.headers

    def test_ignores_post_with_301(self) -> None:
        """Test that CORS headers are NOT added for POST with 301 status."""
        addon = CORSInserterForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=301),
        )

        # Process the response
        addon.response(flow)

        # Verify CORS headers were NOT added
        assert flow.response is not None
        assert "Access-Control-Allow-Origin" not in flow.response.headers

    def test_handles_flow_without_response(self) -> None:
        """Test that addon handles flows without responses gracefully."""
        addon = CORSInserterForWebhooksAddon()
        flow = tflow.tflow(resp=False)

        # Should not raise an exception
        addon.response(flow)

    def test_preserves_existing_headers(self) -> None:
        """Test that existing headers are preserved."""
        addon = CORSInserterForWebhooksAddon()
        flow = tflow.tflow(
            req=tflow.treq(method=b"POST"),
            resp=tflow.tresp(status_code=200),
        )

        # Add existing headers
        assert flow.response is not None
        flow.response.headers["Content-Type"] = "application/json"
        flow.response.headers["Cache-Control"] = "no-cache"

        # Process the response
        addon.response(flow)

        # Verify existing headers were preserved
        assert flow.response.headers["Content-Type"] == "application/json"
        assert flow.response.headers["Cache-Control"] == "no-cache"
        # And CORS headers were added
        assert flow.response.headers["Access-Control-Allow-Origin"] == "*"
