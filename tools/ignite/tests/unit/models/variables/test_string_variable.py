import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.variables import StringVariable


class TestValidStringVariables:
    """Test cases for valid string variable patterns."""

    @pytest.mark.parametrize(
        "value",
        [
            "abc",
            "test",
            "hello world",
            "user name",
            "api version",
        ],
    )
    def test_letters_and_spaces(self, value):
        """Test that valid string variables can contain letters and spaces."""
        variable = StringVariable(value)
        assert_that(variable.root).is_equal_to(value)
        assert_that(variable.resolve()).is_equal_to(value)

    @pytest.mark.parametrize(
        "value",
        [
            "test123",
            "user456",
            "api2",
            "version1",
            "abc123def",
        ],
    )
    def test_letters_and_numbers(self, value):
        """Test that valid string variables can contain letters and numbers."""
        variable = StringVariable(value)
        assert_that(variable.root).is_equal_to(value)
        assert_that(variable.resolve()).is_equal_to(value)

    @pytest.mark.parametrize(
        "value",
        [
            "test_name",
            "user_id",
            "api_version",
            "my_variable",
            "test_123",
        ],
    )
    def test_with_underscores(self, value):
        """Test that valid string variables can contain underscores."""
        variable = StringVariable(value)
        assert_that(variable.root).is_equal_to(value)
        assert_that(variable.resolve()).is_equal_to(value)

    @pytest.mark.parametrize(
        "value",
        [
            "test-name",
            "user-id",
            "api-version",
            "my-variable",
            "test-123",
        ],
    )
    def test_with_hyphens(self, value):
        """Test that valid string variables can contain hyphens."""
        variable = StringVariable(value)
        assert_that(variable.root).is_equal_to(value)
        assert_that(variable.resolve()).is_equal_to(value)

    @pytest.mark.parametrize(
        "value",
        [
            "test_name-123 with spaces",
            "user-id_456",
            "api version_2-test",
            "my variable-test_123",
        ],
    )
    def test_mixed_characters(self, value):
        """Test that valid string variables can contain mixed valid characters."""
        variable = StringVariable(value)
        assert_that(variable.root).is_equal_to(value)
        assert_that(variable.resolve()).is_equal_to(value)

    def test_minimum_length(self):
        """Test edge case with minimum length (3 characters)."""
        value = "abc"
        variable = StringVariable(value)
        assert_that(variable.root).is_equal_to(value)
        assert_that(variable.resolve()).is_equal_to(value)

    def test_maximum_length(self):
        """Test edge case with maximum length (50 characters)."""
        value = "a" * 50  # Exactly 50 characters
        variable = StringVariable(value)
        assert_that(variable.root).is_equal_to(value)
        assert_that(variable.resolve()).is_equal_to(value)

    def test_resolve_method(self):
        """Test that resolve method returns the correct string value."""
        test_values = [
            "simple test",
            "test_with_underscores",
            "test-with-hyphens",
            "test123numbers",
            "complex test_123-value",
        ]

        for value in test_values:
            variable = StringVariable(value)
            assert_that(variable.resolve()).is_equal_to(value)
            assert_that(variable.resolve()).is_instance_of(str)


class TestInvalidStringVariables:
    """Test cases for invalid string variable patterns."""

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "a",
        ],
    )
    def test_too_short(self, value):
        """Test that string variables cannot be shorter than 2 characters."""
        with pytest.raises(ValidationError, match="at least 2 characters"):
            StringVariable(value)

    def test_too_long(self):
        """Test that string variables cannot be longer than 50 characters."""
        value = "a" * 51  # 51 characters
        with pytest.raises(ValidationError, match="at most 50 characters"):
            StringVariable(value)

    @pytest.mark.parametrize(
        "value",
        [
            "test@email",
            "user#123",
            "api$value",
            "name%test",
            "value&test",
            "data*test",
            "config+test",
            "setting=test",
            "path/test",
            "file\\test",
            "query?test",
            "param!test",
            "flag|test",
            "option~test",
            "setting`test",
            "env'test",
            'var"test',
            "func(test)",
            "method[test]",
            "class{test}",
            "type<test>",
            "alias;test",
            "const:test",
            "static,test",
            "extern.test",
        ],
    )
    def test_invalid_special_characters(self, value):
        """Test that string variables cannot contain invalid special characters."""
        with pytest.raises(ValidationError, match="should match pattern"):
            StringVariable(value)

    @pytest.mark.parametrize(
        "value",
        [
            "tést",
            "usér",
            "sérvice",
            "café",
            "naïve",
            "résumé",
            "cœur",
            "façade",
            "münchen",
            "ñoño",
        ],
    )
    def test_unicode_characters(self, value):
        """Test that string variables cannot contain unicode characters."""
        with pytest.raises(ValidationError, match="should match pattern"):
            StringVariable(value)

    @pytest.mark.parametrize(
        "value",
        [
            "test\nline",
            "test\tvalue",
            "test\rreturn",
            "test\x00null",
            "test\x0bvertical",
        ],
    )
    def test_control_characters(self, value):
        """Test that string variables cannot contain control characters."""
        with pytest.raises(ValidationError, match="should match pattern"):
            StringVariable(value)


class TestStringVariableEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_only_spaces(self):
        """Test string variable with only spaces (valid as spaces are allowed)."""
        value = "   "  # 3 spaces
        variable = StringVariable(value)
        assert_that(variable.root).is_equal_to(value)
        assert_that(variable.resolve()).is_equal_to(value)

    def test_spaces_at_boundaries(self):
        """Test string variable with spaces at start and end."""
        value = " test value "
        variable = StringVariable(value)
        assert_that(variable.root).is_equal_to(value)
        assert_that(variable.resolve()).is_equal_to(value)

    def test_only_numbers(self):
        """Test string variable with only numbers."""
        value = "123"
        variable = StringVariable(value)
        assert_that(variable.root).is_equal_to(value)
        assert_that(variable.resolve()).is_equal_to(value)

    def test_only_hyphens_and_underscores(self):
        """Test string variable with only hyphens and underscores."""
        value = "_-_"
        variable = StringVariable(value)
        assert_that(variable.root).is_equal_to(value)
        assert_that(variable.resolve()).is_equal_to(value)

    def test_case_sensitivity(self):
        """Test that string variables preserve case."""
        test_cases = [
            "ABC",
            "abc",
            "AbC",
            "Test Case",
            "MixedCASE_test-123",
        ]

        for value in test_cases:
            variable = StringVariable(value)
            assert_that(variable.root).is_equal_to(value)
            assert_that(variable.resolve()).is_equal_to(value)
