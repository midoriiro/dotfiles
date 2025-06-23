import re
import pytest
from pydantic import BaseModel, ValidationError
from assertpy import assert_that

from ignite.models.fs import RefFile, ReservedFileName


class TestModel(BaseModel):
    """Test model with RefFile field."""
    ref_file: RefFile


class TestRefFileValidation:
    """Test RefFile validation functionality."""

    def test_valid_ref_file_enum(self):
        """Test that valid ref file accepts the exact reserved value."""
        model = TestModel(ref_file=ReservedFileName.REF)
        assert_that(model.ref_file).is_equal_to(ReservedFileName.REF)
        assert_that(model.ref_file).is_equal_to("$ref")

    def test_valid_ref_file_string(self):
        """Test that valid ref file accepts the string value directly."""
        model = TestModel(ref_file="$ref")
        assert_that(model.ref_file).is_equal_to("$ref")

    @pytest.mark.parametrize("ref_file", [
        "ref",
        "REF",
        "$REF",
        "$Ref",
        "$refs",
        "ref$",
        " $ref",
        "$ref ",
        "\t$ref",
        "$ref\t",
        "\n$ref",
        "$ref\n",
        "",
        "test",
        ".test",
        "all",
        "$all",
    ])
    def test_invalid_ref_file_values(self, ref_file):
        """Test that ref file only accepts the exact '$ref' value."""
        with pytest.raises(ValidationError, match=f"should be {re.escape(ReservedFileName.REF.__repr__())}"):
            TestModel(ref_file=ref_file)

    def test_ref_file_case_sensitive(self):
        """Test that ref file is case sensitive."""
        with pytest.raises(ValidationError, match=f"should be {re.escape(ReservedFileName.REF.__repr__())}"):
            TestModel(ref_file="$REF")

    def test_ref_file_whitespace_sensitive(self):
        """Test that ref file is sensitive to whitespace."""
        with pytest.raises(ValidationError, match=f"should be {re.escape(ReservedFileName.REF.__repr__())}"):
            TestModel(ref_file=" $ref")


class TestRefFileBehavior:
    """Test RefFile behavior and properties."""

    def test_ref_file_enum_value(self):
        """Test that ref file works with the enum value."""
        model = TestModel(ref_file=ReservedFileName.REF)
        assert_that(model.ref_file).is_equal_to(ReservedFileName.REF)
        assert_that(model.ref_file).is_equal_to("$ref")

    def test_ref_file_equality(self):
        """Test that ref file values are equal to the expected string."""
        model = TestModel(ref_file="$ref")
        assert_that(model.ref_file).is_equal_to("$ref")
        assert_that(model.ref_file).is_equal_to(ReservedFileName.REF)
        assert_that(str(model.ref_file)).is_equal_to(str(ReservedFileName.REF))

    def test_ref_file_in_model_context(self):
        """Test that ref file works correctly within a model context."""
        class FileModel(BaseModel):
            """Model that can contain different file types."""
            file: RefFile
        
        model = FileModel(file="$ref")
        assert_that(model.file).is_equal_to("$ref")
        assert_that(model.file).is_instance_of(str)
