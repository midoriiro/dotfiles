import pytest
from assertpy import assert_that
from pydantic import BaseModel, ValidationError

from ignite.models.fs import UserFile


class TestModel(BaseModel):
    """Test model with UserFile field."""

    user_file: UserFile


class TestUserFileValidation:
    """Tests for basic UserFile validation constraints."""

    @pytest.mark.parametrize(
        "user_file",
        [
            ".test",
            ".valid",
            ".identifier",
        ],
    )
    def test_valid_user_file_has_leading_dot(self, user_file):
        """Test that valid user files have a leading dot."""
        model = TestModel(user_file=user_file)
        assert_that(model.user_file).is_equal_to(user_file)

    def test_invalid_user_file_empty_string(self):
        """Test that user files cannot be empty."""
        with pytest.raises(ValidationError, match="have at least 2 character"):
            TestModel(user_file="")

    def test_invalid_user_file_only_dot(self):
        """Test that user files cannot be just a dot."""
        with pytest.raises(ValidationError, match="should have at least 2 characters"):
            TestModel(user_file=".")


class TestUserFilePattern:
    """Tests for UserFile pattern validation."""

    @pytest.mark.parametrize(
        "user_file",
        [
            "test",
            "valid",
            "identifier",
        ],
    )
    def test_invalid_user_file_missing_leading_dot(self, user_file):
        """Test that user files must have a leading dot."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(user_file=user_file)

    @pytest.mark.parametrize(
        "user_file",
        [
            "..test",
            "...test",
            "..valid",
        ],
    )
    def test_invalid_user_file_multiple_leading_dots(self, user_file):
        """Test that user files cannot have multiple leading dots."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(user_file=user_file)


class TestUserFileEdgeCases:
    """Tests for UserFile edge cases and special characters."""

    @pytest.mark.parametrize(
        "user_file",
        [
            "test.",
            "valid.",
            "identifier.",
        ],
    )
    def test_invalid_user_file_trailing_dot(self, user_file):
        """Test that user files cannot have a trailing dot."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(user_file=user_file)

    @pytest.mark.parametrize(
        "user_file",
        [
            "test.valid",
            "valid.identifier",
            "a.b",
        ],
    )
    def test_invalid_user_file_dot_in_middle(self, user_file):
        """Test that user files cannot have a dot in the middle."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(user_file=user_file)

    @pytest.mark.parametrize(
        "user_file",
        [
            " .test",
            "  .test",
            "\t.test",
            "\n.test",
            "\r.test",
        ],
    )
    def test_invalid_user_file_whitespace_before_dot(self, user_file):
        """Test that user files cannot have whitespace before the leading dot."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(user_file=user_file)

    @pytest.mark.parametrize(
        "user_file",
        [
            ". test",
            ".  test",
            ".\ttest",
            ".\ntest",
            ".\rtest",
        ],
    )
    def test_invalid_user_file_whitespace_after_dot(self, user_file):
        """Test that user files cannot have whitespace after the leading dot."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(user_file=user_file)
