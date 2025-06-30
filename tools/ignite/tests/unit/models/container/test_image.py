import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.container import Image


class TestValidImage:
    """Test cases for valid image configurations."""

    def test_basic_image_with_name_only(self):
        """Test that a basic image with only name is accepted."""
        image = Image(name="test-image")
        assert_that(image.name).is_equal_to("test-image")
        assert_that(image.repository).is_none()
        assert_that(image.tag).is_none()

    def test_image_with_repository_and_name(self):
        """Test that an image with repository and name is accepted."""
        image = Image(repository="docker.io", name="test-image")
        assert_that(image.repository).is_equal_to("docker.io")
        assert_that(image.name).is_equal_to("test-image")
        assert_that(image.tag).is_none()

    def test_image_with_name_and_tag(self):
        """Test that an image with name and tag is accepted."""
        image = Image(name="test-image", tag="latest")
        assert_that(image.name).is_equal_to("test-image")
        assert_that(image.tag).is_equal_to("latest")
        assert_that(image.repository).is_none()

    def test_image_with_all_fields(self):
        """Test that an image with all fields is accepted."""
        image = Image(repository="docker.io", name="test-image", tag="v1.0.0")
        assert_that(image.repository).is_equal_to("docker.io")
        assert_that(image.name).is_equal_to("test-image")
        assert_that(image.tag).is_equal_to("v1.0.0")


class TestImageComposeMethod:
    """Test cases for the compose method of Image."""

    def test_compose_name_only(self):
        """Test that compose method works correctly with name only."""
        image = Image(name="test-image")
        result = image.compose()

        expected = {"image": "test-image"}
        assert_that(result).is_equal_to(expected)

    def test_compose_with_repository(self):
        """Test that compose method works correctly with repository and name."""
        image = Image(repository="docker.io", name="test-image")
        result = image.compose()

        expected = {"image": "docker.io/test-image"}
        assert_that(result).is_equal_to(expected)

    def test_compose_with_tag(self):
        """Test that compose method works correctly with name and tag."""
        image = Image(name="test-image", tag="latest")
        result = image.compose()

        expected = {"image": "test-image:latest"}
        assert_that(result).is_equal_to(expected)

    def test_compose_with_repository_and_tag(self):
        """Test that compose method works correctly with repository, name and tag."""
        image = Image(repository="docker.io", name="test-image", tag="v1.0.0")
        result = image.compose()

        expected = {"image": "docker.io/test-image:v1.0.0"}
        assert_that(result).is_equal_to(expected)

    def test_compose_structure(self):
        """Test that compose method returns the correct structure."""
        image = Image(name="test-image")
        result = image.compose()

        # Check that the structure is correct
        assert_that(result).contains_key("image")
        assert_that(result["image"]).is_instance_of(str)


class TestImageFeatureName:
    """Test cases for the feature_name method of Image."""

    def test_feature_name(self):
        """Test that feature_name returns the correct name."""
        assert_that(Image.feature_name()).is_equal_to("image")


class TestImageValidation:
    """Test cases for Image field validation."""

    def test_empty_name_raises_error(self):
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            Image(name="")

    def test_name_with_special_characters_raises_error(self):
        """Test that name with special characters raises validation error."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Image(name="test@image")

    def test_name_with_dots_raises_error(self):
        """Test that name with dots raises validation error."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Image(name="test.image")

    def test_name_starting_with_hyphen_raises_error(self):
        """Test that name starting with hyphen raises validation error."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Image(name="-test-image")

    def test_name_ending_with_hyphen_raises_error(self):
        """Test that name ending with hyphen raises validation error."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Image(name="test-image-")

    def test_name_too_long_raises_error(self):
        """Test that name too long raises validation error."""
        long_name = "a" * 257  # Exceeds 256 character limit
        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            Image(name=long_name)

    def test_repository_with_special_characters_raises_error(self):
        """Test that repository with special characters raises validation error."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Image(repository="docker@io", name="test-image")

    def test_tag_with_special_characters_raises_error(self):
        """Test that tag with special characters raises validation error."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Image(name="test-image", tag="latest@1")


class TestImageModelValidator:
    """Test cases for the model validator in Image."""

    def test_repository_without_name_raises_error(self):
        """Test that repository without name raises validation error."""
        with pytest.raises(ValueError, match="Field required"):
            Image(repository="docker.io")

    def test_tag_without_name_raises_error(self):
        """Test that tag without name raises validation error."""
        with pytest.raises(ValueError, match="Field required"):
            Image(tag="latest")

    def test_repository_and_tag_without_name_raises_error(self):
        """Test that repository and tag without name raises validation error."""
        with pytest.raises(ValueError, match="Field required"):
            Image(repository="docker.io", tag="latest")


class TestImageEdgeCases:
    """Test cases for edge cases in Image validation."""

    def test_minimal_valid_name(self):
        """Test that minimal valid name is accepted."""
        image = Image(name="a")
        assert_that(image.name).is_equal_to("a")

    def test_long_valid_name(self):
        """Test that long but valid name is accepted."""
        # Create a name that is close to the 256 character limit
        long_name = "a" * 256
        image = Image(name=long_name)
        assert_that(image.name).is_equal_to(long_name)

    def test_name_with_single_character(self):
        """Test that single character name is accepted."""
        image = Image(name="a")
        assert_that(image.name).is_equal_to("a")

    def test_name_with_maximum_length(self):
        """Test that maximum length name is accepted."""
        max_name = "a" * 256
        image = Image(name=max_name)
        assert_that(image.name).is_equal_to(max_name)


class TestImageInheritance:
    """Test cases for Image inheritance from Feature."""

    def test_image_inherits_from_feature(self):
        """Test that Image inherits from Feature."""
        image = Image(name="test-image")
        assert_that(image).is_instance_of(Image)
        # Check that it has the compose method
        assert_that(hasattr(image, "compose")).is_true()
        # Check that it has the feature_name class method
        assert_that(hasattr(Image, "feature_name")).is_true()

    def test_image_compose_returns_dict(self):
        """Test that Image.compose() returns a dictionary."""
        image = Image(name="test-image")
        result = image.compose()
        assert_that(result).is_instance_of(dict)

    def test_image_feature_name_returns_string(self):
        """Test that Image.feature_name() returns a string."""
        result = Image.feature_name()
        assert_that(result).is_instance_of(str)
