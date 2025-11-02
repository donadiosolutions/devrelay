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
