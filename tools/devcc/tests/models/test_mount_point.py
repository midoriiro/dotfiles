import pytest

from devcc.models import MountPoint, MountType


def test_mount_point_str_bind():
    """Test that MountPoint correctly formats a bind mount."""
    mount = MountPoint(
        source="/host/path",
        target="/container/path",
        type=MountType.BIND
    )
    assert str(mount) == "source=/host/path,target=/container/path,type=bind"

def test_mount_point_str_volume():
    """Test that MountPoint correctly formats a volume mount."""
    mount = MountPoint(
        source="volume_name",
        target="/container/volume",
        type=MountType.VOLUME,
        options="rw"
    )
    assert str(mount) == "source=volume_name,target=/container/volume,type=volume,options=rw"

def test_mount_point_str_without_options():
    """Test that MountPoint correctly formats a mount without options."""
    mount = MountPoint(
        source="/host/path",
        target="/container/path",
        type=MountType.BIND,
        options=None
    )
    assert str(mount) == "source=/host/path,target=/container/path,type=bind" 