import pytest

from devcc.models import Env, MountPoint, MountType, RuntimeFeature


def test_runtime_feature_compose_remote_user():
    """Test that RuntimeFeature correctly composes remoteUser property."""
    feature = RuntimeFeature(remoteUser="testuser")
    result = feature.compose()
    assert result == {"remoteUser": "testuser"}

def test_runtime_feature_compose_container_user():
    """Test that RuntimeFeature correctly composes containerUser property."""
    feature = RuntimeFeature(containerUser="testuser")
    result = feature.compose()
    assert result == {"containerUser": "testuser"}

def test_runtime_feature_compose_container_env():
    """Test that RuntimeFeature correctly composes containerEnv property."""
    feature = RuntimeFeature(
        containerEnv=[
            Env(key="KEY1", value="value1"),
            Env(key="KEY2", value="value2")
        ]
    )
    result = feature.compose()
    assert result == {
        "containerEnv": {
            "KEY1": "value1",
            "KEY2": "value2"
        }
    }

def test_runtime_feature_compose_remote_env():
    """Test that RuntimeFeature correctly composes remoteEnv property."""
    feature = RuntimeFeature(
        remoteEnv=[
            Env(key="REMOTE_KEY1", value="remote_value1"),
            Env(key="REMOTE_KEY2", value="remote_value2")
        ]
    )
    result = feature.compose()
    assert result == {
        "remoteEnv": {
            "REMOTE_KEY1": "remote_value1",
            "REMOTE_KEY2": "remote_value2"
        }
    }

def test_runtime_feature_compose_mounts():
    """Test that RuntimeFeature correctly composes mounts property."""
    feature = RuntimeFeature(
        mounts=[
            MountPoint(
                source="/host/path",
                target="/container/path",
                type=MountType.BIND
            ),
            MountPoint(
                source="volume_name",
                target="/container/volume",
                type=MountType.VOLUME,
                options="rw"
            )
        ]
    )
    result = feature.compose()
    assert result == {
        "mounts": [
            "source=/host/path,target=/container/path,type=bind",
            "source=volume_name,target=/container/volume,type=volume,options=rw"
        ]
    }

def test_runtime_feature_compose_all_properties():
    """Test that RuntimeFeature correctly composes all properties together."""
    feature = RuntimeFeature(
        remoteUser="remoteuser",
        containerUser="testuser",
        containerEnv=[Env(key="KEY1", value="value1")],
        remoteEnv=[Env(key="REMOTE_KEY1", value="remote_value1")],
        mounts=[
            MountPoint(
                source="/host/path",
                target="/container/path",
                type=MountType.BIND
            )
        ]
    )
    result = feature.compose()
    assert result == {
        "remoteUser": "remoteuser",
        "containerUser": "testuser",
        "containerEnv": {"KEY1": "value1"},
        "remoteEnv": {"REMOTE_KEY1": "remote_value1"},
        "mounts": ["source=/host/path,target=/container/path,type=bind"]
    }

def test_runtime_feature_compose_empty():
    """Test that RuntimeFeature returns empty dict when no properties are set."""
    feature = RuntimeFeature()
    result = feature.compose()
    assert result == {} 