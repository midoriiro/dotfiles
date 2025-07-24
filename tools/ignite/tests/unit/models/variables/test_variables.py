from unittest.mock import Mock, patch

import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.variables import CommandVariable, StringVariable, Variables


class TestValidVariables:
    """Test cases for valid Variables configurations."""

    def test_single_string_variable(self):
        """Test Variables with a single StringVariable."""
        variables = Variables({"var": StringVariable("test value")})
        assert_that(variables.root).contains_key("var")
        assert_that(variables.root["var"]).is_instance_of(StringVariable)

    def test_single_command_variable(self):
        """Test Variables with a single CommandVariable."""
        variables = Variables({"cmd": CommandVariable("$(echo test)")})
        assert_that(variables.root).contains_key("cmd")
        assert_that(variables.root["cmd"]).is_instance_of(CommandVariable)

    def test_mixed_variable_types(self):
        """Test Variables with both StringVariable and CommandVariable."""
        variables = Variables(
            {
                "name": StringVariable("test name"),
                "version": CommandVariable("$(git describe --tags)"),
                "env": StringVariable("development"),
            }
        )
        assert_that(variables.root).contains_key("name")
        assert_that(variables.root).contains_key("version")
        assert_that(variables.root).contains_key("env")
        assert_that(variables.root["name"]).is_instance_of(StringVariable)
        assert_that(variables.root["version"]).is_instance_of(CommandVariable)
        assert_that(variables.root["env"]).is_instance_of(StringVariable)

    @pytest.mark.parametrize(
        "identifier",
        [
            "abc",
            "test",
            "myvar",
            "api-version",
            "user-name",
            "service-url",
        ],
    )
    def test_valid_identifiers(self, identifier):
        """Test that valid identifiers are accepted."""
        variables = Variables({identifier: StringVariable("test value")})
        assert_that(variables.root).contains_key(identifier)

    def test_multiple_variables_with_hyphens(self):
        """Test Variables with multiple hyphenated identifiers."""
        variables = Variables(
            {
                "api-key": StringVariable("secret123"),
                "db-host": StringVariable("localhost"),
                "cache-ttl": StringVariable("3600"),
            }
        )
        assert_that(variables.root).is_length(3)
        assert_that(variables.root).contains("api-key")
        assert_that(variables.root).contains("db-host")
        assert_that(variables.root).contains("cache-ttl")

    def test_long_identifier_names(self):
        """Test Variables with long identifier names (up to 50 chars)."""
        long_identifier = "a" + "b" * 47 + "c"  # 49 characters, valid
        variables = Variables({long_identifier: StringVariable("test value")})
        assert_that(variables.root).contains_key(long_identifier)


class TestInvalidVariables:
    """Test cases for invalid Variables configurations."""

    def test_empty_variables_dictionary(self):
        """Test that empty variables dictionary is valid."""
        with pytest.raises(ValidationError, match="should have at least 1 item"):
            Variables({})

    @pytest.mark.parametrize(
        "identifier",
        [
            "a",
            "ab",
            "A",
            "AB",
            "123",
            "_test",
            "-test",
            "test_",
            "test-",
            "test123",
            "testVar",
            "test_var",
            "test.var",
            "test@var",
        ],
    )
    def test_invalid_identifiers(self, identifier):
        """Test that invalid identifiers are rejected."""
        with pytest.raises(ValidationError):
            Variables({identifier: StringVariable("test value")})

    def test_identifier_too_long(self):
        """Test that identifiers longer than 50 characters are rejected."""
        long_identifier = "a" * 51  # 51 characters, invalid
        with pytest.raises(ValidationError):
            Variables({long_identifier: StringVariable("test value")})

    def test_identifier_with_uppercase(self):
        """Test that identifiers with uppercase letters are rejected."""
        with pytest.raises(ValidationError):
            Variables({"testVar": StringVariable("test value")})

    def test_identifier_with_numbers(self):
        """Test that identifiers with numbers are rejected."""
        with pytest.raises(ValidationError):
            Variables({"test123": StringVariable("test value")})

    def test_identifier_with_underscores(self):
        """Test that identifiers with underscores are rejected."""
        with pytest.raises(ValidationError):
            Variables({"test_var": StringVariable("test value")})


class TestVariablesResolve:
    """Test cases for Variables resolve method."""

    @patch.object(StringVariable, "resolve")
    def test_resolve_empty_variables(self, mock_resolve):
        """Test resolving empty variables dictionary."""
        variables = Variables.model_construct({})
        result = variables.resolve()

        assert_that(result).is_empty()
        mock_resolve.assert_not_called()

    @patch.object(StringVariable, "resolve")
    def test_resolve_single_string_variable(self, mock_resolve):
        """Test resolving single StringVariable."""
        mock_resolve.return_value = "resolved string value"

        variables = Variables({"name": StringVariable("test name")})
        result = variables.resolve()

        assert_that(result).contains_key("name")
        assert_that(result["name"]).is_equal_to("resolved string value")
        mock_resolve.assert_called_once()

    @patch.object(CommandVariable, "resolve")
    def test_resolve_single_command_variable(self, mock_resolve):
        """Test resolving single CommandVariable."""
        mock_resolve.return_value = "command output"

        variables = Variables({"version": CommandVariable("$(git describe --tags)")})
        result = variables.resolve()

        assert_that(result).contains_key("version")
        assert_that(result["version"]).is_equal_to("command output")
        mock_resolve.assert_called_once()

    @patch.object(CommandVariable, "resolve")
    @patch.object(StringVariable, "resolve")
    def test_resolve_mixed_variables(self, mock_string_resolve, mock_command_resolve):
        """Test resolving mixed StringVariable and CommandVariable."""
        mock_string_resolve.side_effect = ["string value 1", "string value 2"]
        mock_command_resolve.return_value = "command output"

        variables = Variables(
            {
                "name": StringVariable("test name"),
                "version": CommandVariable("$(git describe --tags)"),
                "env": StringVariable("development"),
            }
        )
        result = variables.resolve()

        assert_that(result).is_length(3)
        assert_that(result["name"]).is_equal_to("string value 1")
        assert_that(result["version"]).is_equal_to("command output")
        assert_that(result["env"]).is_equal_to("string value 2")
        assert_that(mock_string_resolve.call_count).is_equal_to(2)
        mock_command_resolve.assert_called_once()

    @patch.object(StringVariable, "resolve")
    def test_resolve_multiple_string_variables(self, mock_resolve):
        """Test resolving multiple StringVariables."""
        mock_resolve.side_effect = ["value1", "value2", "value3"]

        variables = Variables(
            {
                "first": StringVariable("first value"),
                "second": StringVariable("second value"),
                "third": StringVariable("third value"),
            }
        )
        result = variables.resolve()

        assert_that(result).is_length(3)
        assert_that(result["first"]).is_equal_to("value1")
        assert_that(result["second"]).is_equal_to("value2")
        assert_that(result["third"]).is_equal_to("value3")
        assert_that(mock_resolve.call_count).is_equal_to(3)

    @patch.object(CommandVariable, "resolve")
    def test_resolve_multiple_command_variables(self, mock_resolve):
        """Test resolving multiple CommandVariables."""
        mock_resolve.side_effect = ["output1", "output2", "output3"]

        variables = Variables(
            {
                "version": CommandVariable("$(git describe --tags)"),
                "branch": CommandVariable("$(git branch --show-current)"),
                "commit": CommandVariable("$(git rev-parse HEAD)"),
            }
        )
        result = variables.resolve()

        assert_that(result).is_length(3)
        assert_that(result["version"]).is_equal_to("output1")
        assert_that(result["branch"]).is_equal_to("output2")
        assert_that(result["commit"]).is_equal_to("output3")
        assert_that(mock_resolve.call_count).is_equal_to(3)

    def test_resolve_returns_dict_with_string_values(self):
        """Test that resolve always returns Dict[str, str]."""
        variables = Variables(
            {
                "name": StringVariable("test name"),
                "version": CommandVariable("$(echo v1.0.0)"),
            }
        )

        # We'll mock the resolve methods to ensure predictable output
        with patch.object(
            StringVariable, "resolve", return_value="string result"
        ), patch.object(CommandVariable, "resolve", return_value="command result"):

            result = variables.resolve()

            assert_that(result).is_instance_of(dict)
            for key, value in result.items():
                assert_that(key).is_instance_of(str)
                assert_that(value).is_instance_of(str)


class TestVariablesErrorHandling:
    """Test cases for Variables error handling."""

    def test_resolve_with_invalid_variable_type(self):
        """Test that resolve raises ValueError for invalid variable types."""
        # This is a bit of a hack since we can't normally create Variables with invalid types
        # due to Pydantic validation, but we test the runtime error handling
        variables = Variables({"test": StringVariable("test value")})

        # Manually insert an invalid type to test error handling
        variables.root["test"] = "invalid_type"

        with pytest.raises(ValueError, match="Invalid variable type"):
            variables.resolve()

    @patch.object(StringVariable, "resolve")
    def test_resolve_propagates_variable_errors(self, mock_resolve):
        """Test that resolve propagates errors from individual variable resolution."""
        mock_resolve.side_effect = ValueError("String variable resolution failed")

        variables = Variables({"name": StringVariable("test name")})

        with pytest.raises(ValueError, match="String variable resolution failed"):
            variables.resolve()

    @patch.object(CommandVariable, "resolve")
    def test_resolve_propagates_command_errors(self, mock_resolve):
        """Test that resolve propagates errors from command variable resolution."""
        mock_resolve.side_effect = ValueError("Command execution failed")

        variables = Variables({"version": CommandVariable("$(invalid_command)")})

        with pytest.raises(ValueError, match="Command execution failed"):
            variables.resolve()


class TestVariablesEdgeCases:
    """Test cases for Variables edge cases and boundary conditions."""

    def test_variables_with_hyphenated_identifiers(self):
        """Test Variables with all valid hyphenated identifier patterns."""
        variables = Variables(
            {
                "api-key": StringVariable("secret"),
                "db-host": StringVariable("localhost"),
                "cache-timeout": StringVariable("3600"),
                "service-host": StringVariable("localhost"),
            }
        )

        with patch.object(
            StringVariable,
            "resolve",
            side_effect=["secret", "localhost", "3600", "localhost"],
        ):
            result = variables.resolve()

            assert_that(result).is_length(4)
            assert_that(result["api-key"]).is_equal_to("secret")
            assert_that(result["db-host"]).is_equal_to("localhost")
            assert_that(result["cache-timeout"]).is_equal_to("3600")
            assert_that(result["service-host"]).is_equal_to("localhost")

    def test_minimum_identifier_length(self):
        """Test Variables with minimum length identifiers (3 characters)."""
        variables = Variables(
            {
                "api": StringVariable("test1"),
                "env": StringVariable("test2"),
                "url": StringVariable("test3"),
            }
        )

        with patch.object(
            StringVariable, "resolve", side_effect=["test1", "test2", "test3"]
        ):
            result = variables.resolve()

            assert_that(result).is_length(3)
            assert_that(result["api"]).is_equal_to("test1")
            assert_that(result["env"]).is_equal_to("test2")
            assert_that(result["url"]).is_equal_to("test3")

    def test_large_variables_dictionary(self):
        """Test Variables with many entries."""
        # Create a dictionary with 20 variables
        variable_dict = {}
        expected_values = []

        for i in range(20):
            identifier = f"var-{chr(97 + i)}"  # var-a, var-b, ..., var-t
            variable_dict[identifier] = StringVariable(f"value{i}")
            expected_values.append(f"resolved{i}")

        variables = Variables(variable_dict)

        with patch.object(StringVariable, "resolve", side_effect=expected_values):
            result = variables.resolve()

            assert_that(result).is_length(20)
            for i in range(20):
                identifier = f"var-{chr(97 + i)}"
                assert_that(result[identifier]).is_equal_to(f"resolved{i}")
