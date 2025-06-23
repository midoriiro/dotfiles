import pytest
from pydantic import ValidationError
from assertpy import assert_that

from ignite.models.container import Extensions


class TestValidExtensionsList:
    """Test cases for valid extensions list configurations."""

    def test_single_extension(self):
        """Test that a single extension in the list is valid."""
        extensions = Extensions(vscode=["ms-python.python"])
        assert_that(extensions.vscode).is_length(1)
        assert_that(extensions.vscode[0]).is_equal_to("ms-python.python")

    def test_multiple_extensions(self):
        """Test that multiple extensions in the list are valid."""
        extensions = Extensions(vscode=[
            "ms-python.python",
            "ms-vscode.vscode-json",
            "esbenp.prettier-vscode"
        ])
        assert_that(extensions.vscode).is_length(3)
        assert_that(extensions.vscode).contains("ms-python.python")
        assert_that(extensions.vscode).contains("ms-vscode.vscode-json")
        assert_that(extensions.vscode).contains("esbenp.prettier-vscode")

    def test_maximum_extensions(self):
        """Test that the maximum number of extensions (100) is accepted."""
        vscode_list = [f"publisher{i}.extension{i}" for i in range(1, 101)]
        extensions = Extensions(vscode=vscode_list)
        assert_that(extensions.vscode).is_length(100)


class TestInvalidExtensionsList:
    """Test cases for invalid extensions list configurations."""

    def test_empty_list(self):
        """Test that an empty list is rejected."""
        with pytest.raises(ValidationError, match="List should have at least 1 item"):
            Extensions(vscode=[])

    def test_list_too_long(self):
        """Test that a list with more than 100 extensions is rejected."""
        vscode_list = [f"publisher{i}.extension{i}" for i in range(1, 102)]
        with pytest.raises(ValidationError, match="List should have at most 100 items"):
            Extensions(vscode=vscode_list)

    def test_none_value(self):
        """Test that None value is rejected."""
        with pytest.raises(ValidationError, match="Input should be a valid list"):
            Extensions(vscode=None)

    def test_invalid_list_type(self):
        """Test that non-list values are rejected."""
        with pytest.raises(ValidationError, match="Input should be a valid list"):
            Extensions(vscode="not-a-list")

        with pytest.raises(ValidationError, match="Input should be a valid list"):
            Extensions(vscode=123)

        with pytest.raises(ValidationError, match="Input should be a valid list"):
            Extensions(vscode={"key": "value"})


class TestExtensionsComposeMethod:
    """Test cases for the compose method of Extensions."""

    def test_compose_single_extension(self):
        """Test that compose method works correctly with a single extension."""
        extensions = Extensions(vscode=["ms-python.python"])
        result = extensions.compose()
        
        expected = {
            "customizations": {
                "vscode": {
                    "extensions": ["ms-python.python"]
                }
            }
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_multiple_extensions(self):
        """Test that compose method works correctly with multiple extensions."""
        extensions = Extensions(vscode=[
            "ms-python.python",
            "ms-vscode.vscode-json",
            "esbenp.prettier-vscode"
        ])
        result = extensions.compose()
        
        expected = {
            "customizations": {
                "vscode": {
                    "extensions": [
                        "ms-python.python",
                        "ms-vscode.vscode-json",
                        "esbenp.prettier-vscode"
                    ]
                }
            }
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_preserves_order(self):
        """Test that compose method preserves the order of extensions."""
        vscode_list = [
            "first.extension",
            "second.extension",
            "third.extension"
        ]
        extensions = Extensions(vscode=vscode_list)
        result = extensions.compose()
        
        assert_that(result["customizations"]["vscode"]["extensions"]).is_equal_to(vscode_list)

    def test_compose_structure(self):
        """Test that compose method returns the correct structure."""
        extensions = Extensions(vscode=["test.extension"])
        result = extensions.compose()
        
        # Check that the structure is correct
        assert_that(result).contains_key("customizations")
        assert_that(result["customizations"]).contains_key("vscode")
        assert_that(result["customizations"]["vscode"]).contains_key("extensions")
        assert_that(result["customizations"]["vscode"]["extensions"]).is_instance_of(list)


class TestExtensionsFeatureName:
    """Test cases for the feature_name method of Extensions."""

    def test_feature_name(self):
        """Test that feature_name returns the correct name."""
        assert_that(Extensions.feature_name()).is_equal_to("extensions")


class TestExtensionsEdgeCases:
    """Test cases for edge cases in Extensions validation."""

    def test_duplicate_extensions(self):
        """Test that duplicate extensions in the list are allowed."""
        extensions = Extensions(vscode=[
            "ms-python.python",
            "ms-python.python",  # Duplicate
            "ms-vscode.vscode-json"
        ])
        assert_that(extensions.vscode).is_length(3)
        assert_that(extensions.vscode).contains("ms-python.python")

    def test_minimal_valid_extensions(self):
        """Test that minimal valid extensions are accepted."""
        extensions = Extensions(vscode=["a.b"])
        assert_that(extensions.vscode).is_length(1)
        assert_that(extensions.vscode[0]).is_equal_to("a.b")

    def test_long_extension_names(self):
        """Test that long but valid extension names are accepted."""
        # Create extensions that are close to the 256 character limit
        long_publisher = "a" * 127
        long_name = "b" * 128
        long_extension = f"{long_publisher}.{long_name}"
        
        extensions = Extensions(vscode=[long_extension])
        assert_that(extensions.vscode).is_length(1)
        assert_that(extensions.vscode[0]).is_equal_to(long_extension)
