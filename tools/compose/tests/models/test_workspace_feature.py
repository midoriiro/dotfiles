import pytest

from compose.models import MountPoint, MountType, WorkspaceFeature


def test_workspace_feature_compose_name():
    """Test that WorkspaceFeature correctly composes name property."""
    feature = WorkspaceFeature(name="test-workspace")
    result = feature.compose()
    assert result == {"name": "test-workspace"}

def test_workspace_feature_compose_workspace_mount():
    """Test that WorkspaceFeature correctly composes workspaceMount property."""
    feature = WorkspaceFeature(
        workspaceMount=MountPoint(
            source="/host/workspace",
            target="/workspace",
            type=MountType.BIND,
            options="rw"
        )
    )
    result = feature.compose()
    assert result == {
        "workspaceMount": "source=/host/workspace,target=/workspace,type=bind,options=rw"
    }

def test_workspace_feature_compose_all_properties():
    """Test that WorkspaceFeature correctly composes all properties together."""
    feature = WorkspaceFeature(
        name="test-workspace",
        workspaceMount=MountPoint(
            source="/host/workspace",
            target="/workspace",
            type=MountType.BIND,
            options="rw"
        )
    )
    result = feature.compose()
    assert result == {
        "name": "test-workspace",
        "workspaceMount": "source=/host/workspace,target=/workspace,type=bind,options=rw"
    }

def test_workspace_feature_compose_empty():
    """Test that WorkspaceFeature returns empty dict when no properties are set."""
    feature = WorkspaceFeature()
    result = feature.compose()
    assert result == {} 