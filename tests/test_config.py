"""Tests for the configuration loader."""

import tempfile
from pathlib import Path

import pytest

from devrelay.config import ConfigLoader, Parameter


class TestParameter:
    """Test cases for Parameter dataclass."""

    def test_parameter_creation(self) -> None:
        """Test creating a Parameter instance."""
        param = Parameter(
            name="test_param",
            type=str,
            default="default_value",
            help="Test parameter help text",
        )
        assert param.name == "test_param"
        assert param.type == str
        assert param.default == "default_value"
        assert param.help == "Test parameter help text"


class TestConfigLoader:
    """Test cases for ConfigLoader class."""

    def test_init_creates_default_config_path(self) -> None:
        """Test that initialization creates default config path."""
        loader = ConfigLoader()
        expected_path = Path.home() / ".mitmproxy" / "devrelay.yaml"
        assert loader.config_path == expected_path

    def test_init_accepts_custom_config_path(self) -> None:
        """Test that initialization accepts custom config path."""
        custom_path = Path("/tmp/custom.yaml")
        loader = ConfigLoader(config_path=custom_path)
        assert loader.config_path == custom_path

    def test_build_parser_creates_all_arguments(self) -> None:
        """Test that parser is built with all parameters."""
        loader = ConfigLoader()
        parser = loader.parser

        # Parse empty args to get defaults
        args = parser.parse_args([])
        assert args.host == "127.0.0.1"
        assert args.port == 8080
        assert args.certdir == Path.home() / ".mitmproxy"

    def test_build_parser_accepts_custom_values(self) -> None:
        """Test that parser accepts custom argument values."""
        loader = ConfigLoader()
        parser = loader.parser

        args = parser.parse_args(["--host", "0.0.0.0", "--port", "9090", "--certdir", "/tmp/certs"])
        assert args.host == "0.0.0.0"
        assert args.port == 9090
        assert args.certdir == Path("/tmp/certs")

    def test_load_yaml_creates_file_with_defaults(self) -> None:
        """Test that loading creates YAML file with defaults if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            config = loader._load_yaml()  # pyright: ignore[reportPrivateUsage]  # pyright: ignore[reportPrivateUsage]

            # Verify file was created
            assert config_path.exists()

            # Verify defaults were written (certdir is stored as string in YAML)
            assert config["host"] == "127.0.0.1"
            assert config["port"] == 8080
            assert config["certdir"] == str(Path.home() / ".mitmproxy")

    def test_load_yaml_reads_existing_file(self) -> None:
        """Test that loading reads existing YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create file with custom values
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                f.write("host: 10.0.0.1\n")
                f.write("port: 7070\n")
                f.write("certdir: /custom/path\n")

            config = loader._load_yaml()  # pyright: ignore[reportPrivateUsage]

            assert config["host"] == "10.0.0.1"
            assert config["port"] == 7070
            assert config["certdir"] == "/custom/path"

    def test_load_yaml_handles_empty_file(self) -> None:
        """Test that loading handles empty YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create empty file
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.touch()

            config = loader._load_yaml()  # pyright: ignore[reportPrivateUsage]

            assert config == {}

    def test_load_yaml_raises_on_invalid_yaml(self) -> None:
        """Test that loading raises ValueError on invalid YAML syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create file with invalid YAML
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                f.write("invalid: yaml: content: here\n")
                f.write("  bad indentation\n")

            with pytest.raises(ValueError, match="Failed to load YAML config"):
                loader._load_yaml()  # pyright: ignore[reportPrivateUsage]

    def test_validate_value_validates_string(self) -> None:
        """Test that validation handles string values."""
        loader = ConfigLoader()
        param = Parameter(name="test", type=str, default="default", help="help")

        assert loader._validate_value(param, "test_value") == "test_value"  # pyright: ignore[reportPrivateUsage]
        assert loader._validate_value(param, 123) == "123"  # pyright: ignore[reportPrivateUsage]
        assert loader._validate_value(param, None) is None  # pyright: ignore[reportPrivateUsage]

    def test_validate_value_validates_int(self) -> None:
        """Test that validation handles integer values."""
        loader = ConfigLoader()
        param = Parameter(name="test", type=int, default=0, help="help")

        assert loader._validate_value(param, 42) == 42  # pyright: ignore[reportPrivateUsage]
        assert loader._validate_value(param, "42") == 42  # pyright: ignore[reportPrivateUsage]
        assert loader._validate_value(param, None) is None  # pyright: ignore[reportPrivateUsage]

    def test_validate_value_validates_port_range(self) -> None:
        """Test that validation enforces port range constraints."""
        loader = ConfigLoader()
        param = Parameter(name="port", type=int, default=8080, help="help")

        assert loader._validate_value(param, 1) == 1  # pyright: ignore[reportPrivateUsage]
        assert loader._validate_value(param, 8080) == 8080  # pyright: ignore[reportPrivateUsage]
        assert loader._validate_value(param, 65535) == 65535  # pyright: ignore[reportPrivateUsage]

        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            loader._validate_value(param, 0)  # pyright: ignore[reportPrivateUsage]

        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            loader._validate_value(param, 65536)  # pyright: ignore[reportPrivateUsage]

        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            loader._validate_value(param, -1)  # pyright: ignore[reportPrivateUsage]

    def test_validate_value_validates_path(self) -> None:
        """Test that validation handles Path values."""
        loader = ConfigLoader()
        param = Parameter(name="test", type=Path, default=None, help="help")

        assert loader._validate_value(param, "/tmp/test") == Path("/tmp/test")  # pyright: ignore[reportPrivateUsage]
        assert loader._validate_value(param, Path("/tmp/test")) == Path(  # pyright: ignore[reportPrivateUsage]
            "/tmp/test"
        )
        assert loader._validate_value(param, None) is None  # pyright: ignore[reportPrivateUsage]

    def test_validate_value_raises_on_invalid_type(self) -> None:
        """Test that validation raises on invalid type conversion."""
        loader = ConfigLoader()
        param = Parameter(name="test", type=int, default=0, help="help")

        with pytest.raises(ValueError, match="Invalid value for 'test'"):
            loader._validate_value(param, "not_a_number")  # pyright: ignore[reportPrivateUsage]

    def test_update_yaml_file_adds_missing_parameters(self) -> None:
        """Test that update adds missing parameters to YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create file with only some parameters
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                f.write("host: 10.0.0.1\n")

            yaml_config = {"host": "10.0.0.1"}
            loader._update_yaml_file(yaml_config)  # pyright: ignore[reportPrivateUsage]

            # Reload and verify all parameters are present
            with open(config_path) as f:
                content = f.read()
                assert "host: 10.0.0.1" in content
                assert "port: 8080" in content
                assert "certdir:" in content

    def test_update_yaml_file_preserves_existing_values(self) -> None:
        """Test that update preserves existing parameter values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            yaml_config = {"host": "10.0.0.1", "port": 7070, "certdir": None}
            loader._update_yaml_file(yaml_config)  # pyright: ignore[reportPrivateUsage]

            # Reload and verify values are preserved
            reloaded = loader._load_yaml()  # pyright: ignore[reportPrivateUsage]
            assert reloaded["host"] == "10.0.0.1"
            assert reloaded["port"] == 7070
            assert reloaded["certdir"] is None

    def test_update_yaml_file_preserves_comments(self) -> None:
        """Test that update preserves comments in YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create file with comments
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                f.write("# This is a comment\n")
                f.write("host: 10.0.0.1  # Inline comment\n")

            yaml_config = loader._load_yaml()  # pyright: ignore[reportPrivateUsage]
            loader._update_yaml_file(yaml_config)  # pyright: ignore[reportPrivateUsage]

            # Verify comments are preserved (ruamel.yaml preserves comments)
            with open(config_path) as f:
                content = f.read()
                assert "# This is a comment" in content or "This is a comment" in content

    def test_get_config_with_defaults(self) -> None:
        """Test getting configuration with all defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            config = loader.get_config([])

            assert config.host == "127.0.0.1"
            assert config.port == 8080
            assert config.certdir == Path.home() / ".mitmproxy"

    def test_get_config_with_yaml_overrides(self) -> None:
        """Test getting configuration with YAML file overrides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create file with custom values
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                loader.yaml.dump({"host": "10.0.0.1", "port": 7070, "certdir": "/custom"}, f)

            config = loader.get_config([])

            assert config.host == "10.0.0.1"
            assert config.port == 7070
            assert config.certdir == Path("/custom")

    def test_get_config_with_cli_overrides(self) -> None:
        """Test getting configuration with CLI argument overrides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create file with some values
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                loader.yaml.dump({"host": "10.0.0.1", "port": 7070, "certdir": None}, f)

            # CLI should override YAML
            config = loader.get_config(["--host", "0.0.0.0", "--port", "9090"])

            assert config.host == "0.0.0.0"
            assert config.port == 9090
            assert config.certdir is None

    def test_get_config_precedence(self) -> None:
        """Test that configuration precedence is CLI > YAML > defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create YAML with some overrides
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                loader.yaml.dump({"host": "10.0.0.1", "port": 7070, "certdir": None}, f)

            # Provide only --host via CLI
            config = loader.get_config(["--host", "192.168.1.1"])

            # host should come from CLI, port from YAML, certdir from YAML
            assert config.host == "192.168.1.1"
            assert config.port == 7070
            assert config.certdir is None

    def test_get_config_creates_yaml_if_missing(self) -> None:
        """Test that get_config creates YAML file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            config = loader.get_config([])

            assert config_path.exists()
            assert config.host == "127.0.0.1"
            assert config.port == 8080
            assert config.certdir == Path.home() / ".mitmproxy"

    def test_get_config_updates_yaml_with_missing_params(self) -> None:
        """Test that get_config updates YAML with missing parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create file with only one parameter
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                f.write("host: 10.0.0.1\n")

            loader.get_config([])

            # Verify all parameters are now in file
            with open(config_path) as f:
                content = f.read()
                assert "host: 10.0.0.1" in content
                assert "port: 8080" in content
                assert "certdir:" in content

    def test_get_config_raises_on_invalid_yaml_value(self) -> None:
        """Test that get_config raises ValueError on invalid YAML values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create file with invalid port value
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                loader.yaml.dump({"host": "127.0.0.1", "port": 99999, "certdir": None}, f)

            with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
                loader.get_config([])

    def test_get_config_validates_cli_args(self) -> None:
        """Test that get_config validates CLI argument values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
                loader.get_config(["--port", "0"])

    def test_get_config_with_certdir_as_string_in_yaml(self) -> None:
        """Test that certdir string in YAML is converted to Path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create file with certdir as string
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                loader.yaml.dump({"host": "127.0.0.1", "port": 8080, "certdir": "/tmp/certs"}, f)

            config = loader.get_config([])

            assert isinstance(config.certdir, Path)
            assert config.certdir == Path("/tmp/certs")

    def test_parameter_definitions_match_defaults(self) -> None:
        """Test that all parameter definitions have correct defaults."""
        loader = ConfigLoader()

        # Verify we have the expected parameters
        param_names = [p.name for p in loader.parameters]
        assert "host" in param_names
        assert "port" in param_names
        assert "certdir" in param_names
        assert "disabled_addons" in param_names

        # Verify defaults
        for param in loader.parameters:
            if param.name == "host":
                assert param.default == "127.0.0.1"
                assert param.type == str
            elif param.name == "port":
                assert param.default == 8080
                assert param.type == int
            elif param.name == "certdir":
                assert param.default == Path.home() / ".mitmproxy"
                assert param.type == Path
            elif param.name == "disabled_addons":
                assert param.default == []
                assert param.type == list

    def test_parse_addon_list_with_none(self) -> None:
        """Test that parse_addon_list handles None value."""
        loader = ConfigLoader()
        result = loader._parse_addon_list(None)  # pyright: ignore[reportPrivateUsage]
        assert result == []

    def test_parse_addon_list_with_list(self) -> None:
        """Test that parse_addon_list handles list value."""
        loader = ConfigLoader()
        result = loader._parse_addon_list(["CSP", "COEP"])  # pyright: ignore[reportPrivateUsage]
        assert result == ["CSP", "COEP"]

    def test_parse_addon_list_with_comma_separated_string(self) -> None:
        """Test that parse_addon_list handles comma-separated string."""
        loader = ConfigLoader()
        result = loader._parse_addon_list("CSP,COEP,COOP")  # pyright: ignore[reportPrivateUsage]
        assert result == ["CSP", "COEP", "COOP"]

    def test_parse_addon_list_with_whitespace(self) -> None:
        """Test that parse_addon_list strips whitespace."""
        loader = ConfigLoader()
        result = loader._parse_addon_list("CSP, COEP , COOP")  # pyright: ignore[reportPrivateUsage]
        assert result == ["CSP", "COEP", "COOP"]

    def test_parse_addon_list_with_mixed_format(self) -> None:
        """Test that parse_addon_list handles list with comma-separated items."""
        loader = ConfigLoader()
        result = loader._parse_addon_list(["CSP,COEP", "COOP"])  # pyright: ignore[reportPrivateUsage]
        assert result == ["CSP", "COEP", "COOP"]

    def test_parse_addon_list_with_empty_string(self) -> None:
        """Test that parse_addon_list handles empty string."""
        loader = ConfigLoader()
        result = loader._parse_addon_list("")  # pyright: ignore[reportPrivateUsage]
        assert result == []

    def test_parse_addon_list_filters_empty_items(self) -> None:
        """Test that parse_addon_list filters out empty items."""
        loader = ConfigLoader()
        result = loader._parse_addon_list("CSP,,COEP,")  # pyright: ignore[reportPrivateUsage]
        assert result == ["CSP", "COEP"]

    def test_validate_value_for_disabled_addons_valid(self) -> None:
        """Test that validate_value validates disabled_addons correctly."""
        loader = ConfigLoader()
        param = Parameter(name="disabled_addons", type=list, default=[], help="help")

        result = loader._validate_value(param, ["CSP", "COEP"])  # pyright: ignore[reportPrivateUsage]
        assert result == ["CSPRemoverAddon", "COEPRemoverAddon"]

    def test_validate_value_for_disabled_addons_invalid(self) -> None:
        """Test that validate_value raises on invalid addon name."""
        loader = ConfigLoader()
        param = Parameter(name="disabled_addons", type=list, default=[], help="help")

        with pytest.raises(ValueError, match="Unknown addon"):
            loader._validate_value(param, ["InvalidAddon"])  # pyright: ignore[reportPrivateUsage]

    def test_validate_value_for_disabled_addons_none(self) -> None:
        """Test that validate_value returns empty list for None."""
        loader = ConfigLoader()
        param = Parameter(name="disabled_addons", type=list, default=[], help="help")

        result = loader._validate_value(param, None)  # pyright: ignore[reportPrivateUsage]
        assert result == []

    def test_get_config_with_disabled_addons_from_cli(self) -> None:
        """Test getting configuration with disabled_addons from CLI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            config = loader.get_config(["--disable-addon", "CSP", "--disable-addon", "COEP"])

            assert config.disabled_addons == ["CSPRemoverAddon", "COEPRemoverAddon"]

    def test_get_config_with_disabled_addons_comma_separated(self) -> None:
        """Test getting configuration with comma-separated disabled_addons."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            config = loader.get_config(["--disable-addon", "CSP,COEP"])

            assert config.disabled_addons == ["CSPRemoverAddon", "COEPRemoverAddon"]

    def test_get_config_with_disabled_addons_mixed_format(self) -> None:
        """Test getting configuration with mixed CLI format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            config = loader.get_config(["--disable-addon", "CSP,COEP", "--disable-addon", "COOP"])

            assert config.disabled_addons == ["CSPRemoverAddon", "COEPRemoverAddon", "COOPRemoverAddon"]

    def test_get_config_with_disabled_addons_from_yaml(self) -> None:
        """Test getting configuration with disabled_addons from YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create YAML with disabled_addons
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                loader.yaml.dump({"disabled_addons": ["CSP", "COEP"]}, f)

            config = loader.get_config([])

            assert config.disabled_addons == ["CSPRemoverAddon", "COEPRemoverAddon"]

    def test_get_config_with_disabled_addons_cli_overrides_yaml(self) -> None:
        """Test that CLI disabled_addons override YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            # Create YAML with disabled_addons
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                loader.yaml.dump({"disabled_addons": ["CSP"]}, f)

            config = loader.get_config(["--disable-addon", "COEP"])

            # CLI should override YAML
            assert config.disabled_addons == ["COEPRemoverAddon"]

    def test_get_config_with_disabled_addons_invalid_name(self) -> None:
        """Test that invalid addon name in CLI raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            with pytest.raises(ValueError, match="Unknown addon"):
                loader.get_config(["--disable-addon", "InvalidAddon"])

    def test_get_config_with_disabled_addons_case_insensitive(self) -> None:
        """Test that disabled_addons are case-insensitive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            config = loader.get_config(["--disable-addon", "csp,COEP"])

            assert config.disabled_addons == ["CSPRemoverAddon", "COEPRemoverAddon"]

    def test_get_config_with_empty_disabled_addons(self) -> None:
        """Test that empty disabled_addons returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yaml"
            loader = ConfigLoader(config_path=config_path)

            config = loader.get_config([])

            assert config.disabled_addons == []

    def test_build_parser_includes_disable_addon_argument(self) -> None:
        """Test that parser includes --disable-addon argument."""
        loader = ConfigLoader()
        parser = loader.parser

        # Test that --disable-addon is accepted
        args = parser.parse_args(["--disable-addon", "CSP"])
        assert args.disabled_addons == ["CSP"]

    def test_build_parser_disable_addon_allows_multiple(self) -> None:
        """Test that --disable-addon can be used multiple times."""
        loader = ConfigLoader()
        parser = loader.parser

        args = parser.parse_args(["--disable-addon", "CSP", "--disable-addon", "COEP"])
        assert args.disabled_addons == ["CSP", "COEP"]

    def test_parse_addon_list_with_non_string_items(self) -> None:
        """Test that parse_addon_list handles non-string items in list."""
        loader = ConfigLoader()
        # This tests the else branch at line 129 where item is not a string
        result = loader._parse_addon_list([123, 456])  # pyright: ignore[reportPrivateUsage]
        assert result == [123, 456]

    def test_parse_addon_list_with_non_standard_type(self) -> None:
        """Test that parse_addon_list returns empty list for non-standard types."""
        loader = ConfigLoader()
        # This tests line 136 where raw_value is neither None, list, nor string
        result = loader._parse_addon_list(123)  # pyright: ignore[reportPrivateUsage]
        assert result == []

    def test_validate_value_for_list_type_not_disabled_addons(self) -> None:
        """Test that validate_value returns parsed list for non-disabled_addons list params."""
        loader = ConfigLoader()
        # Create a parameter with type list but not named disabled_addons
        param = Parameter(name="other_list", type=list, default=[], help="help")

        result = loader._validate_value(param, ["item1", "item2"])  # pyright: ignore[reportPrivateUsage]
        # Should return the parsed list without validation
        assert result == ["item1", "item2"]
