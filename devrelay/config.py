"""Configuration management for DevRelay."""

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from devrelay.addons import validate_addon_names


@dataclass
class Parameter:
    """Definition of a configuration parameter."""

    name: str
    type: type
    default: Any
    help: str


class ConfigLoader:
    """Unified configuration loader that handles both CLI args and YAML file."""

    def __init__(self, config_path: Path | None = None) -> None:
        """
        Initialize the configuration loader.

        Args:
            config_path: Path to YAML config file (default: ~/.mitmproxy/devrelay.yaml)
        """
        self.config_path = config_path or Path.home() / ".mitmproxy" / "devrelay.yaml"
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.default_flow_style = False

        # Define all parameters in one place
        self.parameters = [
            Parameter(
                name="host",
                type=str,
                default="127.0.0.1",
                help="Host address to bind to",
            ),
            Parameter(
                name="port",
                type=int,
                default=8080,
                help="Port to listen on",
            ),
            Parameter(
                name="certdir",
                type=Path,
                default=Path.home() / ".mitmproxy",
                help="Certificate directory",
            ),
            Parameter(
                name="disabled_addons",
                type=list,
                default=[],
                help="Comma-separated list of addons to disable (e.g., CSP,COEP)",
            ),
        ]

        self.parser = self._build_parser()

    def _build_parser(self) -> argparse.ArgumentParser:
        """
        Build ArgumentParser from parameter definitions.

        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            description="DevRelay - MITM proxy that removes CSP headers",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        for param in self.parameters:
            # Special handling for list types (disabled_addons)
            if param.type == list:
                # Use --disable-addon (singular) for better UX
                arg_name = "--disable-addon"
                # action='append' allows repeated usage: --disable-addon CSP --disable-addon COEP
                parser.add_argument(
                    arg_name,
                    action="append",
                    default=None,  # Use None to detect if user provided values
                    help=param.help,
                    dest=param.name,  # Store in disabled_addons
                )
            else:
                parser.add_argument(
                    f"--{param.name}",
                    type=param.type,
                    default=param.default,
                    help=param.help,
                )

        return parser

    def _parse_addon_list(self, raw_value: Any) -> list[str]:
        """
        Parse addon list from CLI or YAML format.

        Handles both comma-separated strings and lists.
        CLI format: --disable-addon CSP,COEP or --disable-addon CSP --disable-addon COEP
        YAML format: disabled_addons: [CSP, COEP] or disabled_addons: CSP,COEP

        Args:
            raw_value: Raw value from CLI or YAML (None, str, or list)

        Returns:
            Parsed list of addon names
        """
        if raw_value is None:
            return []

        # If it's already a list (from action='append' or YAML)
        if isinstance(raw_value, list):
            # Flatten and split comma-separated values
            result = []
            for item in raw_value:
                if isinstance(item, str):
                    # Split by comma and strip whitespace
                    result.extend([x.strip() for x in item.split(",") if x.strip()])
                else:
                    result.append(item)
            return result

        # If it's a string (from YAML), split by comma
        if isinstance(raw_value, str):
            return [x.strip() for x in raw_value.split(",") if x.strip()]

        return []

    def _load_yaml(self) -> dict[str, Any]:
        """
        Load configuration from YAML file.

        Creates file with defaults if it doesn't exist.

        Returns:
            Dictionary of configuration values from YAML

        Raises:
            ValueError: If YAML file is invalid
        """
        # Create directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.config_path.exists():
            # Create file with all defaults (convert Path to str for YAML)
            defaults = {
                param.name: str(param.default) if isinstance(param.default, Path) else param.default
                for param in self.parameters
            }
            with open(self.config_path, "w") as f:
                self.yaml.dump(defaults, f)
            return defaults

        # Load existing file
        try:
            with open(self.config_path) as f:
                data = self.yaml.load(f)
                return data if data is not None else {}
        except Exception as e:
            raise ValueError(f"Failed to load YAML config from {self.config_path}: {e}") from e

    def _validate_value(self, param: Parameter, value: Any) -> Any:
        """
        Validate and convert a configuration value.

        Args:
            param: Parameter definition
            value: Value to validate

        Returns:
            Validated and converted value

        Raises:
            ValueError: If value is invalid
        """
        if value is None:
            # For list types, return empty list instead of None
            if param.type == list:
                return []
            return None

        # Type conversion
        try:
            if param.type == Path:
                return Path(value)
            elif param.type == int:
                try:
                    result = int(value)
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"Invalid value for '{param.name}' in {self.config_path}: "
                        f"expected {param.type.__name__}, got {type(value).__name__} ({value})"
                    ) from e
                # Validate port range
                if param.name == "port" and not (1 <= result <= 65535):
                    raise ValueError(f"Port must be between 1 and 65535, got {result}")
                return result
            elif param.type == str:
                return str(value)
            elif param.type == list:
                # Handle list types (currently only disabled_addons)
                parsed_list = self._parse_addon_list(value)
                # Validate addon names if this is the disabled_addons parameter
                if param.name == "disabled_addons":
                    return validate_addon_names(parsed_list)
                return parsed_list
            else:  # pragma: no cover
                return value
        except (ValueError, TypeError):
            # Re-raise errors (already have good messages)
            raise

    def _update_yaml_file(self, yaml_config: dict[str, Any]) -> None:
        """
        Update YAML file with missing parameters.

        Preserves comments and formatting.

        Args:
            yaml_config: Current YAML configuration
        """
        # Add missing parameters (convert Path to str for YAML)
        for param in self.parameters:
            if param.name not in yaml_config:
                yaml_config[param.name] = str(param.default) if isinstance(param.default, Path) else param.default

        # Always write the config to file
        with open(self.config_path, "w") as f:
            self.yaml.dump(yaml_config, f)

    def get_config(self, args: list[str] | None = None) -> argparse.Namespace:
        """
        Get merged configuration from YAML and CLI args.

        Precedence: CLI args > YAML file > defaults

        Args:
            args: Optional CLI arguments (defaults to sys.argv)

        Returns:
            Namespace with final configuration values

        Raises:
            ValueError: If configuration is invalid
        """
        # Load YAML configuration
        yaml_config = self._load_yaml()

        # Update YAML file with missing parameters
        self._update_yaml_file(yaml_config)

        # Parse CLI arguments
        cli_args = self.parser.parse_args(args)

        # Merge configurations (CLI > YAML > defaults)
        final_config = {}

        for param in self.parameters:
            # Get CLI value
            cli_value = getattr(cli_args, param.name)

            # Check if CLI value is the default (meaning user didn't provide it)
            # For list types, CLI default is None, so check for None explicitly
            if param.type == list:
                is_cli_default = cli_value is None
            else:
                is_cli_default = cli_value == param.default

            if is_cli_default and param.name in yaml_config:
                # Use YAML value if CLI wasn't provided
                yaml_value = yaml_config[param.name]
                final_config[param.name] = self._validate_value(param, yaml_value)
            else:
                # Use CLI value (either user-provided or default)
                final_config[param.name] = self._validate_value(param, cli_value)

        return argparse.Namespace(**final_config)
