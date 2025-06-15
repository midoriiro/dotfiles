import pytest

from devcc.models import ConnectionURL, ExposeFeature, MountPoint, MountType


def test_expose_feature_compose_socket():
    """Test that ExposeFeature correctly composes socket property."""
    feature = ExposeFeature(
        socket=MountPoint(
            source="/host/socket",
            target="/container/socket",
            type=MountType.BIND
        )
    )
    result = feature.compose()
    assert result == {
        "mounts": ["source=/host/socket,target=/container/socket,type=bind"]
    }

def test_expose_feature_compose_address():
    """Test that ExposeFeature correctly composes address property."""
    feature = ExposeFeature(
        address=ConnectionURL.from_string("tcp://localhost:2375")
    )
    result = feature.compose()
    assert result == {
        "containerEnv": ["tcp://localhost:2375"]
    }

def test_expose_feature_compose_all_properties():
    """Test that ExposeFeature correctly composes all properties together."""
    feature = ExposeFeature(
        socket=MountPoint(
            source="/host/socket",
            target="/container/socket",
            type=MountType.BIND
        ),
        address=ConnectionURL.from_string("tcp://localhost:2375")
    )
    result = feature.compose()
    assert result == {
        "mounts": ["source=/host/socket,target=/container/socket,type=bind"],
        "containerEnv": ["tcp://localhost:2375"]
    }

def test_expose_feature_compose_empty():
    """Test that ExposeFeature returns empty dict when no properties are set."""
    feature = ExposeFeature()
    result = feature.compose()
    assert result == {} 