import pytest

from devcc.models import (ContainerBuildFeature, ContainerFeature,
                          ContainerImageFeature)


def test_container_feature_with_image():
    """Test ContainerFeature with an image configuration."""
    image_feature = ContainerImageFeature(name="python:3.9")
    feature = ContainerFeature(image=image_feature)
    composed = feature.compose()
    assert composed == {"image": "python:3.9"}

def test_container_feature_with_build():
    """Test ContainerFeature with a build configuration."""
    build_feature = ContainerBuildFeature(
        container_file="Dockerfile",
        context=".",
        target="dev"
    )
    feature = ContainerFeature(build=build_feature)
    composed = feature.compose()
    assert composed == {
        "build": {
            "dockerFile": "Dockerfile",
            "context": ".",
            "target": "dev"
        }
    }

def test_container_feature_with_both_image_and_build():
    """Test ContainerFeature with both image and build configurations (should raise error)."""
    image_feature = ContainerImageFeature(name="python:3.9")
    build_feature = ContainerBuildFeature(container_file="Dockerfile")
    with pytest.raises(ValueError, match="Either 'image' or 'build' must be set, but not both or neither."):
        ContainerFeature(image=image_feature, build=build_feature).compose()

def test_container_feature_with_neither_image_nor_build():
    """Test ContainerFeature with neither image nor build configurations (should raise error)."""
    with pytest.raises(ValueError, match="Either 'image' or 'build' must be set, but not both or neither."):
        ContainerFeature().compose()

def test_container_feature_with_minimal_build():
    """Test ContainerFeature with minimal build configuration."""
    build_feature = ContainerBuildFeature(container_file="Dockerfile")
    feature = ContainerFeature(build=build_feature)
    composed = feature.compose()
    assert composed == {
        "build": {
            "dockerFile": "Dockerfile"
        }
    }

def test_container_feature_with_minimal_image():
    """Test ContainerFeature with minimal image configuration."""
    image_feature = ContainerImageFeature(name="python:3.9")
    feature = ContainerFeature(image=image_feature)
    composed = feature.compose()
    assert composed == {"image": "python:3.9"} 