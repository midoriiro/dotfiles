import pytest

from compose.models import ContainerImageFeature


def test_container_image_feature_creation():
    """Test the creation of a ContainerImageFeature instance with all fields."""
    feature = ContainerImageFeature(name="python:3.9")
    assert feature.name == "python:3.9"
    assert feature.has_valid_fields() is True


def test_container_image_feature_minimal():
    """Test the creation of a ContainerImageFeature instance with minimal fields."""
    feature = ContainerImageFeature(name="python:3.9")
    assert feature.name == "python:3.9"
    assert feature.has_valid_fields() is True


def test_container_image_feature_compose():
    """Test the compose method of ContainerImageFeature."""
    feature = ContainerImageFeature(name="python:3.9")
    composed = feature.compose()
    assert composed == {"image": "python:3.9"}


def test_container_image_feature_has_valid_fields():
    """Test the has_valid_fields method of ContainerImageFeature."""
    feature = ContainerImageFeature(name="python:3.9")
    assert feature.has_valid_fields() is True
