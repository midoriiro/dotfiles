import pytest

from devcc.models import ContainerBuildFeature


def test_container_build_feature_creation():
    """Test the creation of a ContainerBuildFeature instance with all fields."""
    feature = ContainerBuildFeature(
        container_file="Dockerfile",
        context=".",
        target="dev"
    )
    assert feature.container_file == "Dockerfile"
    assert feature.context == "."
    assert feature.target == "dev"
    assert feature.has_valid_fields() is True

def test_container_build_feature_minimal():
    """Test the creation of a ContainerBuildFeature instance with minimal fields."""
    feature = ContainerBuildFeature(container_file="Dockerfile")
    assert feature.container_file == "Dockerfile"
    assert feature.context is None
    assert feature.target is None
    assert feature.has_valid_fields() is True

def test_container_build_feature_compose_full():
    """Test the compose method with all fields set."""
    feature = ContainerBuildFeature(
        container_file="Dockerfile",
        context=".",
        target="dev"
    )
    composed = feature.compose()
    assert composed == {
        "build": {
            "dockerFile": "Dockerfile",
            "context": ".",
            "target": "dev"
        }
    }

def test_container_build_feature_compose_partial():
    """Test the compose method with only some fields set."""
    feature = ContainerBuildFeature(
        container_file="Dockerfile",
        context="."
    )
    composed = feature.compose()
    assert composed == {
        "build": {
            "dockerFile": "Dockerfile",
            "context": "."
        }
    }

def test_container_build_feature_has_valid_fields():
    """Test the has_valid_fields method with different combinations."""
    # Test with all fields
    feature1 = ContainerBuildFeature(
        container_file="Dockerfile",
        context=".",
        target="dev"
    )
    assert feature1.has_valid_fields() is True

    # Test with only container_file
    feature2 = ContainerBuildFeature(container_file="Dockerfile")
    assert feature2.has_valid_fields() is True

    # Test with only context
    feature3 = ContainerBuildFeature(context=".")
    assert feature3.has_valid_fields() is True

    # Test with only target
    feature4 = ContainerBuildFeature(target="dev")
    assert feature4.has_valid_fields() is True

    # Test with no fields
    feature5 = ContainerBuildFeature()
    assert feature5.has_valid_fields() is False 