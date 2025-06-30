import pytest
from assertpy import assert_that
from pydantic import BaseModel, ValidationError

from ignite.models.common import Identifier


class TestModel(BaseModel):
    """Test model with Identifier field."""

    identifier: Identifier


class TestValidIdentifiers:
    """Test cases for valid identifier patterns."""

    @pytest.mark.parametrize(
        "identifier",
        ["test", "Test", "myIdentifier", "user123", "api_v1", "service-name"],
    )
    def test_starts_with_letter(self, identifier):
        """Test that valid identifiers start with a letter."""
        model = TestModel(identifier=identifier)
        assert_that(model.identifier).is_equal_to(identifier)

    @pytest.mark.parametrize(
        "identifier",
        [
            "user_name",
            "api_version",
            "test_123",
            "My_Identifier",
        ],
    )
    def test_with_underscores(self, identifier):
        """Test that valid identifiers can contain underscores."""
        model = TestModel(identifier=identifier)
        assert_that(model.identifier).is_equal_to(identifier)

    @pytest.mark.parametrize(
        "identifier",
        [
            "user-name",
            "api-version",
            "test-123",
            "My-Identifier",
        ],
    )
    def test_with_hyphens(self, identifier):
        """Test that valid identifiers can contain hyphens."""
        model = TestModel(identifier=identifier)
        assert_that(model.identifier).is_equal_to(identifier)

    @pytest.mark.parametrize(
        "identifier",
        [
            "user123",
            "api2",
            "test_456",
            "service-789",
            "v1",
            "version2",
        ],
    )
    def test_with_numbers(self, identifier):
        """Test that valid identifiers can contain numbers after first character."""
        model = TestModel(identifier=identifier)
        assert_that(model.identifier).is_equal_to(identifier)

    @pytest.mark.parametrize("identifier", ["a", "Z"])
    def test_single_letter(self, identifier):
        """Test edge case with single letter identifier."""
        model = TestModel(identifier=identifier)
        assert_that(model.identifier).is_equal_to(identifier)

    def test_long_identifier(self):
        """Test edge case with long identifier."""
        long_identifier = "a" + "b" * 100
        model = TestModel(identifier=long_identifier)
        assert_that(model.identifier).is_equal_to(long_identifier)

    def test_mixed_case(self):
        """Test edge case with mixed case identifier."""
        mixed_identifier = "MyIdentifier123_Test-API"
        model = TestModel(identifier=mixed_identifier)
        assert_that(model.identifier).is_equal_to(mixed_identifier)


class TestInvalidStartCharacters:
    """Test cases for invalid starting characters."""

    @pytest.mark.parametrize(
        "identifier",
        [
            "123test",
            "0identifier",
            "9user",
        ],
    )
    def test_starts_with_number(self, identifier):
        """Test that identifiers cannot start with a number."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(identifier=identifier)

    @pytest.mark.parametrize(
        "identifier",
        [
            "_test",
            "_identifier",
            "_user123",
        ],
    )
    def test_starts_with_underscore(self, identifier):
        """Test that identifiers cannot start with an underscore."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(identifier=identifier)

    @pytest.mark.parametrize(
        "identifier",
        [
            "-test",
            "-identifier",
            "-user123",
        ],
    )
    def test_starts_with_hyphen(self, identifier):
        """Test that identifiers cannot start with a hyphen."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(identifier=identifier)


class TestInvalidEndCharacters:
    """Test cases for invalid ending characters."""

    @pytest.mark.parametrize(
        "identifier",
        [
            "test-",
            "user_",
        ],
    )
    def test_ends_with_special_character(self, identifier):
        """Test that identifiers cannot end with hyphen or underscore."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(identifier=identifier)


class TestInvalidSpecialCharacters:
    """Test cases for invalid special characters."""

    @pytest.mark.parametrize(
        "identifier",
        [
            "test@",
            "user#",
            "api$",
            "service%",
            "name&",
            "value*",
            "data+",
            "config=",
            "path/",
            "file\\",
            "query?",
            "param!",
            "flag|",
            "option~",
            "setting`",
            "env'",
            'var"',
            "func(",
            "method)",
            "class[",
            "type]",
            "struct{",
            "union}",
            "enum<",
            "alias>",
            "typedef;",
            "const:",
            "static,",
            "extern.",
        ],
    )
    def test_special_characters(self, identifier):
        """Test that identifiers cannot contain special characters."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(identifier=identifier)


class TestInvalidWhitespace:
    """Test cases for invalid whitespace and control characters."""

    def test_empty_string(self):
        """Test that identifiers cannot be empty."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(identifier="     ")

    @pytest.mark.parametrize(
        "identifier",
        [
            "test name",
            "user name",
            "api version",
            "service name",
            " test",
            "test ",
            " test ",
        ],
    )
    def test_spaces(self, identifier):
        """Test that identifiers cannot contain spaces."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(identifier=identifier)

    @pytest.mark.parametrize(
        "identifier",
        [
            " ",
            "\t",
            "\n",
            "\r",
        ],
    )
    def test_whitespace_only(self, identifier):
        """Test that identifiers cannot be whitespace only."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(identifier=identifier)


class TestInvalidUnicode:
    """Test cases for invalid unicode characters."""

    @pytest.mark.parametrize(
        "identifier",
        [
            "tést",
            "usér",
            "sérvice",
            "café",
            "naïve",
            "résumé",
            "cœur",
            "façade",
        ],
    )
    def test_unicode_characters(self, identifier):
        """Test that identifiers cannot contain unicode characters."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(identifier=identifier)
