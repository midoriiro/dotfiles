import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.common import Identifier
from ignite.models.container import Env, EnvType


class TestValidEnv:
    """Test cases for valid environment variable configurations."""

    @pytest.mark.parametrize(
        "key,value",
        [
            ("DATABASE_URL", "postgresql://localhost:5432/mydb"),
            ("API_KEY", "secret-key-123"),
            ("DEBUG", "true"),
            ("PORT", "8080"),
            ("NODE_ENV", "production"),
        ],
    )
    def test_valid_env_with_value(self, key, value):
        """Test that valid environment variables with values are accepted."""
        env = Env(key=key, value=value)
        assert_that(env.key).is_equal_to(key)
        assert_that(env.value).is_equal_to(value)
        assert_that(env.type).is_equal_to(EnvType.REMOTE)

    @pytest.mark.parametrize(
        "key",
        [
            "DATABASE_URL",
            "API_KEY",
            "DEBUG",
            "PORT",
            "NODE_ENV",
        ],
    )
    def test_valid_env_without_value(self, key):
        """Test that valid environment variables without values are accepted."""
        env = Env(key=key)
        assert_that(env.key).is_equal_to(key)
        assert_that(env.value).is_none()
        assert_that(env.type).is_equal_to(EnvType.REMOTE)

    def test_env_with_container_type(self):
        """Test that environment variables with container type are accepted."""
        env = Env(
            key="DATABASE_URL",
            value="postgresql://localhost:5432/mydb",
            type=EnvType.CONTAINER,
        )
        assert_that(env.key).is_equal_to("DATABASE_URL")
        assert_that(env.value).is_equal_to("postgresql://localhost:5432/mydb")
        assert_that(env.type).is_equal_to(EnvType.CONTAINER)

    def test_env_with_remote_type_explicit(self):
        """Test that environment variables with explicit remote type are accepted."""
        env = Env(
            key="DATABASE_URL",
            value="postgresql://localhost:5432/mydb",
            type=EnvType.REMOTE,
        )
        assert_that(env.key).is_equal_to("DATABASE_URL")
        assert_that(env.value).is_equal_to("postgresql://localhost:5432/mydb")
        assert_that(env.type).is_equal_to(EnvType.REMOTE)


class TestEnvValidation:
    """Test cases for environment variable validation rules."""

    def test_env_with_empty_key(self):
        """Test that environment variables with empty keys are rejected."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            Env(key="")

    def test_env_with_invalid_key_pattern(self):
        """Test that environment variables with invalid key patterns are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Env(key="invalid-key@")

    def test_env_with_too_long_key(self):
        """Test that environment variables with keys longer than 256 characters are rejected."""
        long_key = "a" * 257
        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            Env(key=long_key)

    def test_env_with_too_short_value(self):
        """Test that environment variables with values shorter than 1 character are rejected."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            Env(key="VALID_KEY", value="")

    def test_env_with_too_long_value(self):
        """Test that environment variables with values longer than 256 characters are rejected."""
        long_value = "a" * 257
        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            Env(key="VALID_KEY", value=long_value)


class TestEnvCompose:
    """Test cases for environment variable composition."""

    def test_compose_remote_env_with_value(self):
        """Test that remote environment variables with values are composed correctly."""
        env = Env(
            key="DATABASE_URL",
            value="postgresql://localhost:5432/mydb",
            type=EnvType.REMOTE,
        )
        result = env.compose()
        expected = {"remoteEnv": {"DATABASE_URL": "postgresql://localhost:5432/mydb"}}
        assert_that(result).is_equal_to(expected)

    def test_compose_remote_env_without_value(self):
        """Test that remote environment variables without values are composed correctly."""
        env = Env(key="DEBUG", type=EnvType.REMOTE)
        result = env.compose()
        expected = {"remoteEnv": {"DEBUG": None}}
        assert_that(result).is_equal_to(expected)

    def test_compose_container_env_with_value(self):
        """Test that container environment variables with values are composed correctly."""
        env = Env(
            key="DATABASE_URL",
            value="postgresql://localhost:5432/mydb",
            type=EnvType.CONTAINER,
        )
        result = env.compose()
        expected = {
            "containerEnv": {"DATABASE_URL": "postgresql://localhost:5432/mydb"}
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_container_env_without_value(self):
        """Test that container environment variables without values are composed correctly."""
        env = Env(key="DEBUG", type=EnvType.CONTAINER)
        result = env.compose()
        expected = {"containerEnv": {"DEBUG": None}}
        assert_that(result).is_equal_to(expected)

    def test_compose_default_remote_type(self):
        """Test that environment variables default to remote type when not specified."""
        env = Env(key="DATABASE_URL", value="postgresql://localhost:5432/mydb")
        result = env.compose()
        expected = {"remoteEnv": {"DATABASE_URL": "postgresql://localhost:5432/mydb"}}
        assert_that(result).is_equal_to(expected)


class TestEnvEdgeCases:
    """Test cases for environment variable edge cases."""

    def test_env_with_minimal_valid_key(self):
        """Test that environment variables with minimal valid keys are accepted."""
        env = Env(key="a")
        assert_that(env.key).is_equal_to("a")
        assert_that(env.value).is_none()
        assert_that(env.type).is_equal_to(EnvType.REMOTE)

    def test_env_with_long_valid_key(self):
        """Test that environment variables with long valid keys are accepted."""
        long_key = "a" * 256
        env = Env(key=long_key)
        assert_that(env.key).is_equal_to(long_key)
        assert_that(env.value).is_none()
        assert_that(env.type).is_equal_to(EnvType.REMOTE)

    def test_env_with_minimal_valid_value(self):
        """Test that environment variables with minimal valid values are accepted."""
        env = Env(key="KEY", value="a")
        assert_that(env.key).is_equal_to("KEY")
        assert_that(env.value).is_equal_to("a")
        assert_that(env.type).is_equal_to(EnvType.REMOTE)

    def test_env_with_long_valid_value(self):
        """Test that environment variables with long valid values are accepted."""
        long_value = "a" * 256
        env = Env(key="KEY", value=long_value)
        assert_that(env.key).is_equal_to("KEY")
        assert_that(env.value).is_equal_to(long_value)
        assert_that(env.type).is_equal_to(EnvType.REMOTE)

    def test_env_with_special_characters_in_key(self):
        """Test that environment variables with valid special characters in keys are accepted."""
        env = Env(key="API_KEY_123")
        assert_that(env.key).is_equal_to("API_KEY_123")
        assert_that(env.value).is_none()
        assert_that(env.type).is_equal_to(EnvType.REMOTE)

    def test_env_with_special_characters_in_value(self):
        """Test that environment variables with valid special characters in values are accepted."""
        env = Env(key="URL", value="https://example.com/path?param=value")
        assert_that(env.key).is_equal_to("URL")
        assert_that(env.value).is_equal_to("https://example.com/path?param=value")
        assert_that(env.type).is_equal_to(EnvType.REMOTE)


class TestEnvFeatureInheritance:
    """Test cases for Env feature inheritance."""

    def test_env_feature_name(self):
        """Test that Env has the correct feature name."""
        assert_that(Env.feature_name()).is_equal_to("env")

    def test_env_inherits_from_feature(self):
        """Test that Env inherits from Feature base class."""
        env = Env(key="TEST_KEY")
        assert_that(env).is_instance_of(Env)
        # Verify that compose method is implemented
        result = env.compose()
        assert_that(result).is_instance_of(dict)
