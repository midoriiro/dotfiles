import re
import pytest
from pydantic import BaseModel, ValidationError
from assertpy import assert_that

from ignite.models.fs import AllFile, ReservedFileName


class TestModel(BaseModel):
    """Test model with AllFile field."""
    all_file: AllFile


class TestAllFileValidation:
    """Test basic validation of AllFile field."""

    def test_valid_all_file(self):
        """Test that valid all file accepts the exact reserved value."""
        model = TestModel(all_file=ReservedFileName.ALL)
        assert_that(model.all_file).is_equal_to(ReservedFileName.ALL)
        assert_that(model.all_file).is_equal_to("$all")

    def test_valid_all_file_string(self):
        """Test that valid all file accepts the string value directly."""
        model = TestModel(all_file="$all")
        assert_that(model.all_file).is_equal_to("$all")

    @pytest.mark.parametrize("all_file", [
        "all",
        "ALL",
        "$ALL",
        "$All",
        "$alls",
        "all$",
        " $all",
        "$all ",
        "\t$all",
        "$all\t",
        "\n$all",
        "$all\n",
        "",
        "test",
        ".test",
        "ref",
        "$ref",
    ])
    def test_invalid_all_file_values(self, all_file):
        """Test that all file only accepts the exact '$all' value."""
        with pytest.raises(ValidationError, match=f"should be {re.escape(ReservedFileName.ALL.__repr__())}"):
            TestModel(all_file=all_file)


class TestAllFileSensitivity:
    """Test sensitivity of AllFile field to case and whitespace."""

    def test_all_file_case_sensitive(self):
        """Test that all file is case sensitive."""
        with pytest.raises(ValidationError, match=f"should be {re.escape(ReservedFileName.ALL.__repr__())}"):
            TestModel(all_file="$ALL")

    def test_all_file_whitespace_sensitive(self):
        """Test that all file is sensitive to whitespace."""
        with pytest.raises(ValidationError, match=f"should be {re.escape(ReservedFileName.ALL.__repr__())}"):
            TestModel(all_file=" $all")


class TestAllFileEquality:
    """Test equality and comparison of AllFile values."""

    def test_all_file_enum_value(self):
        """Test that all file works with the enum value."""
        model = TestModel(all_file=ReservedFileName.ALL)
        assert_that(model.all_file).is_equal_to(ReservedFileName.ALL)
        assert_that(model.all_file).is_equal_to("$all")

    def test_all_file_equality(self):
        """Test that all file values are equal to the expected string."""
        model = TestModel(all_file="$all")
        assert_that(model.all_file).is_equal_to("$all")
        assert_that(model.all_file).is_equal_to(ReservedFileName.ALL)
        assert_that(str(model.all_file)).is_equal_to(str(ReservedFileName.ALL))


class TestAllFileIntegration:
    """Test integration of AllFile in model contexts."""

    def test_all_file_in_model_context(self):
        """Test that all file works correctly within a model context."""
        class FileModel(BaseModel):
            """Model that can contain different file types."""
            file: AllFile
        
        model = FileModel(file="$all")
        assert_that(model.file).is_equal_to("$all")
        assert_that(model.file).is_instance_of(str)
