# DevRelay - Agent Documentation

Technical documentation for AI coding agents working on this project.

## Project Overview

Type: Python 3.13 daemon
Purpose: MITM proxy that removes cleans security headers from HTTP responses to help development and testing.
Primary library: mitmproxy 11.0+
Package manager: uv (native mode, not uv pip)
Build system: hatchling

## Architecture

### Module Structure

```text
devrelay/
├── __init__.py          # Exports: COEPRemoverAddon, COOPRemoverAddon, CORPInserterAddon, CORSInserterForWebhooksAddon,
│                        # CORSPreflightForWebhooksAddon, CSPRemoverAddon
├── addons.py            # All addon classes (CSP, COEP, COOP, CORP, and CORS handling)
├── proxy.py             # Server configuration and startup
└── cli.py               # CLI entry point with argparse
tests/                   # pytest test suite
├── test_addons.py       # Tests for all addons (CSP, COEP, COOP, CORP, and CORS)
├── test_proxy.py        # ProxyServer tests
└── test_devrelay.py        # CLI tests
```

### Key Components

#### ProxyServer (devrelay/proxy.py)

Type: async server wrapper
Test file: tests/test_proxy.py
Configuration:

- Default listen: 127.0.0.1:8080
- TLS: 1.2+
- Protocols: HTTP/1.x, HTTP/2, HTTP/3, WebSocket
- Cert dir: ~/.mitmproxy
- Loads CSPRemoverAddon, COEPRemoverAddon, COOPRemoverAddon, CORPInserterAddon, CORSInserterForWebhooksAddon, and
  CORSPreflightForWebhooksAddon

#### Addons (devrelay/addons.py)

Type: mitmproxy addon class
Entry points: `response(self, flow: http.HTTPFlow) -> None`
Test file: tests/test_addons.py

##### CSPRemoverAddon

Test class: TestCSPRemoverAddon
Behavior:

- Intercepts all HTTP responses
- Removes headers (case-insensitive):
  - `content-security-policy`
  - `content-security-policy-report-only`
- Preserves all other headers
- Handles None responses gracefully

##### COEPRemoverAddon

Test class: TestCOEPRemoverAddon
Behavior:

- Intercepts all HTTP responses
- Removes headers (case-insensitive):
  - `cross-origin-embedder-policy`
  - `cross-origin-embedder-policy-report-only`
- Preserves all other headers
- Handles None responses gracefully

##### COOPRemoverAddon

Test class: TestCOOPRemoverAddon
Behavior:

- Intercepts all HTTP responses
- Removes headers (case-insensitive):
  - `cross-origin-opener-policy`
  - `cross-origin-opener-policy-report-only`
- Preserves all other headers
- Handles None responses gracefully

##### CORPInserterAddon

Test class: TestCORPInserterAddon
Behavior:

- Intercepts HTTP responses to mutation requests (POST, PUT, PATCH, DELETE)
- Only processes successful responses (1XX or 2XX status codes)
- Adds header: `Cross-Origin-Resource-Policy: cross-origin`
- Preserves all other headers
- Handles None responses gracefully
- Ignores GET and other non-mutation methods
- Ignores 3XX, 4XX, and 5XX status codes

##### CORSInserterForWebhooksAddon

Test class: TestCORSInserterForWebhooksAddon
Behavior:

- Intercepts HTTP responses to mutation requests (POST, PUT, PATCH, DELETE)
- Only processes successful responses (1XX or 2XX status codes)
- Adds permissive CORS headers:
  - `Access-Control-Allow-Origin: *`
  - `Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD`
  - `Access-Control-Allow-Headers: *`
  - `Access-Control-Max-Age: 86400`
  - `Access-Control-Expose-Headers: *`
- Preserves all other headers
- Handles None responses gracefully
- Ignores GET and other non-mutation methods
- Ignores 3XX, 4XX, and 5XX status codes

##### CORSPreflightForWebhooksAddon

Test class: TestCORSPreflightForWebhooksAddon
Behavior:

- Intercepts OPTIONS requests that returned 405 Method Not Allowed
- Rewrites response to 204 No Content
- Adds permissive CORS headers:
  - `Access-Control-Allow-Origin: *`
  - `Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD`
  - `Access-Control-Allow-Headers: *`
  - `Access-Control-Max-Age: 86400`
  - `Access-Control-Expose-Headers: *`
- Clears response body
- Ignores non-OPTIONS requests and non-405 responses

#### CLI (devrelay/cli.py)

Entry point: `main() -> int`
Script entry: `devrelay` (configured in pyproject.toml)
Framework: argparse
Class: DevRelayCLI
Arguments:

- `--host` (str, default: 127.0.0.1)
- `--port` (int, default: 8080)
- `--confdir` (Path, default: None -> ~/.mitmproxy)

## Development Workflow

### Setup

The `make dev` command automatically installs pre-commit hooks that run on git commit to check for:

- Secrets and credentials (gitleaks)
- Trailing whitespace
- End-of-file fixers
- Code formatting (black in check mode)
- Markdown linting (pymarkdownlnt in check mode)

### Quality Checks

Testing: pytest with asyncio support
Type checking: pyright in strict mode
Code style: black and pymarkdownlint

```bash
make format
make lint
make lintmd
make typecheck
make test
make check # All of the above
```

## Making Changes

### Adding Features to the Addons

1. Modify `devrelay/addons.py`
2. Implement new methods or modify `response()` in the relevant addon class
3. Add corresponding tests in `tests/test_addons.py`
4. Run `make check` to verify

### Modifying Proxy Configuration

1. Update `ProxyServer.__init__()` or `start()` in `devrelay/proxy.py`
2. Add tests in `tests/test_proxy.py`
3. Update CLI args in `devrelay/cli.py` if needed
4. Update README.md if user-facing

### Adding Dependencies

1. Edit `pyproject.toml` dependencies or optional-dependencies
2. Run `make dev` to install

### Writing Tests

Pattern: use mitmproxy.test.tflow for creating test flows

```python
from mitmproxy.test import tflow

flow = tflow.tflow(resp=True)  # Creates flow with response
flow.response.headers["Header-Name"] = "value"
```

Requirements:

- All new code must have tests
- Coverage should not decrease
- Use type hints in all test functions

## Common Tasks

### Create New Addon

1. Edit `devrelay/addons.py` -> add to `csp_headers` list in CSPRemoverAddon
2. Add test in `tests/test_addons.py` in TestCSPRemoverAddon class
3. Run `make check` (not just `make test`)

### Add CLI Argument

1. Edit `devrelay/cli.py` -> add to argparse in DevRelayCLI class
2. Pass to ProxyServer constructor
3. Update ProxyServer to accept parameter
4. Add tests in `tests/test_devrelay.py`
5. Update README.md
6. Run `make check` to ensure 100% coverage

## Critical Requirements

**BEFORE FINISHING ANY TASK:**

1. Run `make check`
2. Ensure 0 errors, 0 warnings (except external lib warnings)
3. Verify 100% **line AND branch** coverage
4. All checks must pass (format, lint, typecheck, test)

### Coding Standards

- Type hints are required (strict mode via pyright)
- All public APIs must have docstrings
- Tests are required for ALL new code
- Use `uv` commands, not `pip` directly
- Virtual environment is at `.venv/`
- Don't modify certificate handling (security critical)
- Follow existing code patterns and structure

### Quality Gates

The project enforces:

- `fail_under = 100` in coverage config
- `typeCheckingMode = "strict"` in pyright
- `flake8` with max-line-length=120
- `pymarkdownlnt` with MD013 enabled (line_length=120, code blocks exempt)
- `black` formatting with line-length=120 must not change files

If `make check` fails, your task is incomplete. Fix all issues.
