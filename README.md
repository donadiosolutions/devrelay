# DevRelay

A MITM (Man-in-the-Middle) proxy that removes security headers from HTTP requests and responses, allowing for easier
web development and testing.

## Features

- Supports TLS 1.2 or greater
- HTTP/2 and HTTP/3 support
- WebSocket support
- Automatic certificate management in `~/.mitmproxy`
- Simple CLI interface

## Installation

### Option 1: Install with pipx (Recommended)

[pipx](<https://pipx.pypa.io/>) installs the package in an isolated environment and makes it available globally:

```bash
# Install from local directory
pipx install .

# Or install directly from git repository
pipx install git+https://github.com/yourusername/devrelay.git
```

### Option 2: Install with pip

```bash
# Install globally (may require sudo/admin)
pip install .

# Or install in user directory
pip install --user .

# Or install in development mode
pip install -e .
```

### Option 3: Development Setup

For development with all dev tools:

```bash
# Using make (requires uv)
make dev

# Or manually with pip
pip install -e ".[dev]"
```

## Quick Start

### Prerequisites

- Python 3.13 or later
- For development: [uv](<https://github.com/astral-sh/uv>) package manager (optional)

### Running the Proxy

After installation, start the proxy with default settings (localhost:8080):

```bash
# If installed with pip/pipx
devrelay

# Or run as a Python module
python -m devrelay

# For development setup
make run
```

Run with custom options:

```bash
devrelay --host 0.0.0.0 --port 9090

# Or with Python module
python -m devrelay --host 0.0.0.0 --port 9090
```

### Configure Your Browser

To use the proxy, configure your browser to use it:

1. Set HTTP/HTTPS proxy to `127.0.0.1:8080` (or your custom host/port)
2. On first use, you'll need to install the mitmproxy certificate:
   - Visit <http://mitm.it> in your proxied browser
   - Follow the instructions to install the certificate for your OS

## CLI Options

```text
devrelay [-h] [--host HOST] [--port PORT] [--confdir CONFDIR]

Options:
  -h, --help         Show help message
  --host HOST        Host address to bind to (default: 127.0.0.1)
  --port PORT        Port to listen on (default: 8080)
  --confdir CONFDIR  Certificate directory (default: ~/.mitmproxy)
```

## Development

### Available Make Targets

```bash
make help       # Show all available targets
make venv       # Create virtual environment
make install    # Install production dependencies
make dev        # Install development dependencies and pre-commit hooks
make test       # Run tests with coverage
make format     # Format code with black
make lint       # Lint code with flake8
make lintmd     # Lint markdown files with pymarkdownlnt
make typecheck  # Type check with pyright
make check      # Run all checks (format, lint, lintmd, typecheck, test)
make run        # Run the devrelay proxy
make clean      # Remove virtual environment and cache files
```

### Running Tests

```bash
make test
```

This runs pytest with coverage reporting. Coverage reports are generated in:

- Terminal output
- `htmlcov/index.html` (HTML report)
- `coverage.xml` (XML report)

### Code Quality

Format code:

```bash
make format
```

Run linter:

```bash
make lint
```

Run type checker:

```bash
make typecheck
```

Run all checks at once:

```bash
make check
```

## Project Structure

```text
devrelay/
├── devrelay/             # Main package
│   ├── __init__.py       # Module exports
│   ├── __main__.py       # Entry point for python -m devrelay
│   ├── addons.py         # Security header removal addons
│   ├── cli.py            # Command-line interface
│   └── proxy.py          # Proxy server setup
├── tests/                # Test suite
│   ├── __init__.py
│   ├── test_addons.py    # Addon tests
│   ├── test_proxy.py     # Proxy server tests
│   └── test_devrelay.py  # CLI tests
├── pyproject.toml        # Project configuration
├── Makefile              # Build automation
├── .gitignore            # Git ignore patterns
├── README.md             # Human documentation
└── AGENTS.md             # AI agent documentation
```

## How It Works

DevRelay uses [mitmproxy](<https://mitmproxy.org/>) to intercept HTTP/HTTPS traffic and modify responses on-the-fly.
The proxy includes several addons that remove security headers:

- **CSPRemoverAddon**: Removes Content-Security-Policy headers
- **COEPRemoverAddon**: Removes Cross-Origin-Embedder-Policy headers
- **COOPRemoverAddon**: Removes Cross-Origin-Opener-Policy headers
- **CORPInserterAddon**: Adds Cross-Origin-Resource-Policy headers to mutations
- **CORSInserterForWebhooksAddon**: Adds permissive CORS headers to successful mutations
- **CORSPreflightForWebhooksAddon**: Handles failed OPTIONS requests with CORS headers

This is useful for:

- Testing web applications that have strict security policies
- Developing browser extensions that would otherwise be blocked
- Debugging third-party websites with restrictive headers
- Testing webhook integrations with CORS issues

## Security Warning

This tool removes security headers and should only be used for development and testing purposes. Do not use this
proxy for general web browsing or on production systems.

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please ensure all tests pass and code is formatted before submitting PRs:

```bash
make check
```
