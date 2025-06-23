import pytest
from pydantic import ValidationError
from assertpy import assert_that

from ignite.models.container import Mount, MountType
from ignite.models.common import Identifier
from ignite.models.fs import AbsolutePath


class TestValidMountBind:
    """Test cases for valid bind mount configurations."""

    @pytest.mark.parametrize("source,target", [
        ("/home/user/data", "/workspace/data"),
        ("/var/lib/data", "/app/data"),
        ("/tmp/cache", "/cache"),
        ("/etc/config", "/config"),
        ("/usr/local/bin", "/bin"),
    ])
    def test_valid_bind_mounts(self, source, target):
        """Test that valid bind mounts with absolute paths are accepted."""
        mount = Mount(
            source=source,
            target=target,
            type=MountType.BIND
        )
        assert_that(mount.source).is_equal_to(source)
        assert_that(mount.target).is_equal_to(target)
        assert_that(mount.type).is_equal_to(MountType.BIND)
        assert_that(mount.options).is_none()

    def test_bind_mount_with_options(self):
        """Test that bind mounts with options are accepted."""
        mount = Mount(
            source="/home/user/data",
            target="/workspace/data",
            type=MountType.BIND,
            options=["ro", "noexec"]
        )
        assert_that(mount.source).is_equal_to("/home/user/data")
        assert_that(mount.target).is_equal_to("/workspace/data")
        assert_that(mount.type).is_equal_to(MountType.BIND)
        assert_that(mount.options).is_equal_to(["ro", "noexec"])

    def test_bind_mount_with_single_option(self):
        """Test that bind mounts with a single option are accepted."""
        mount = Mount(
            source="/home/user/data",
            target="/workspace/data",
            type=MountType.BIND,
            options=["ro"]
        )
        assert_that(mount.options).is_equal_to(["ro"])


class TestValidMountVolume:
    """Test cases for valid volume mount configurations."""

    @pytest.mark.parametrize("source,target", [
        ("data-volume", "/workspace/data"),
        ("cache-volume", "/cache"),
        ("config-volume", "/config"),
        ("logs-volume", "/var/logs"),
        ("temp-volume", "/tmp"),
    ])
    def test_valid_volume_mounts(self, source, target):
        """Test that valid volume mounts with identifier names are accepted."""
        mount = Mount(
            source=source,
            target=target,
            type=MountType.VOLUME
        )
        assert_that(mount.source).is_equal_to(source)
        assert_that(mount.target).is_equal_to(target)
        assert_that(mount.type).is_equal_to(MountType.VOLUME)
        assert_that(mount.options).is_none()

    def test_volume_mount_with_options(self):
        """Test that volume mounts with options are accepted."""
        mount = Mount(
            source="data-volume",
            target="/workspace/data",
            type=MountType.VOLUME,
            options=["ro", "noexec"]
        )
        assert_that(mount.source).is_equal_to("data-volume")
        assert_that(mount.target).is_equal_to("/workspace/data")
        assert_that(mount.type).is_equal_to(MountType.VOLUME)
        assert_that(mount.options).is_equal_to(["ro", "noexec"])


class TestMountValidation:
    """Test cases for mount validation rules."""

    def test_volume_mount_with_absolute_path_source(self):
        """Test that volume mounts with absolute path sources are rejected."""
        with pytest.raises(ValidationError, match="Source must be a volume name"):
            Mount(
                source="/home/user/data",
                target="/workspace/data",
                type=MountType.VOLUME
            )

    def test_bind_mount_with_identifier_source(self):
        """Test that bind mounts with identifier sources are rejected."""
        with pytest.raises(ValidationError, match="Source must be an absolute path"):
            Mount(
                source="data-volume",
                target="/workspace/data",
                type=MountType.BIND
            )

    def test_mount_with_invalid_target_path(self):
        """Test that mounts with invalid target paths are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Mount(
                source="/home/user/data",
                target="relative/path",
                type=MountType.BIND
            )

    def test_mount_with_empty_target(self):
        """Test that mounts with empty target paths are rejected."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            Mount(
                source="/home/user/data",
                target="",
                type=MountType.BIND
            )

    def test_mount_with_invalid_source_path_for_bind(self):
        """Test that bind mounts with invalid source paths are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Mount(
                source="relative/path",
                target="/workspace/data",
                type=MountType.BIND
            )

    def test_mount_with_invalid_volume_name(self):
        """Test that volume mounts with invalid volume names are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Mount(
                source="invalid-volume-name@",
                target="/workspace/data",
                type=MountType.VOLUME
            )


class TestMountOptions:
    """Test cases for mount options validation."""

    def test_mount_with_empty_options_list(self):
        """Test that mounts with empty options list are accepted."""
        mount = Mount(
            source="/home/user/data",
            target="/workspace/data",
            type=MountType.BIND,
            options=[]
        )
        assert_that(mount.options).is_equal_to([])

    def test_mount_with_single_empty_option(self):
        """Test that mounts with single empty option are rejected."""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            Mount(
                source="/home/user/data",
                target="/workspace/data",
                type=MountType.BIND,
                options=[""]
            )

    def test_mount_with_long_option(self):
        """Test that mounts with options longer than 256 characters are rejected."""
        long_option = "a" * 257
        with pytest.raises(ValidationError, match="String should have at most 256 characters"):
            Mount(
                source="/home/user/data",
                target="/workspace/data",
                type=MountType.BIND,
                options=[long_option]
            )

    @pytest.mark.parametrize("options", [
        ["ro"],
        ["noexec"],
        ["nosuid"],
        ["ro", "noexec"],
        ["ro", "noexec", "nosuid"],
        ["bind"],
        ["rbind"],
    ])
    def test_valid_mount_options(self, options):
        """Test that valid mount options are accepted."""
        mount = Mount(
            source="/home/user/data",
            target="/workspace/data",
            type=MountType.BIND,
            options=options
        )
        assert_that(mount.options).is_equal_to(options)


class TestMountStringRepresentation:
    """Test cases for mount string representation."""

    def test_bind_mount_string_representation(self):
        """Test string representation of bind mount without options."""
        mount = Mount(
            source="/home/user/data",
            target="/workspace/data",
            type=MountType.BIND
        )
        expected = "source=/home/user/data,target=/workspace/data,type=bind"
        assert_that(str(mount)).is_equal_to(expected)

    def test_volume_mount_string_representation(self):
        """Test string representation of volume mount without options."""
        mount = Mount(
            source="data-volume",
            target="/workspace/data",
            type=MountType.VOLUME
        )
        expected = "source=data-volume,target=/workspace/data,type=volume"
        assert_that(str(mount)).is_equal_to(expected)

    def test_mount_string_representation_with_single_option(self):
        """Test string representation of mount with single option."""
        mount = Mount(
            source="/home/user/data",
            target="/workspace/data",
            type=MountType.BIND,
            options=["ro"]
        )
        expected = "source=/home/user/data,target=/workspace/data,type=bind,options=ro"
        assert_that(str(mount)).is_equal_to(expected)

    def test_mount_string_representation_with_multiple_options(self):
        """Test string representation of mount with multiple options."""
        mount = Mount(
            source="/home/user/data",
            target="/workspace/data",
            type=MountType.BIND,
            options=["ro", "noexec"]
        )
        expected = "source=/home/user/data,target=/workspace/data,type=bind,options=ro,noexec"
        assert_that(str(mount)).is_equal_to(expected)

    def test_volume_mount_string_representation_with_options(self):
        """Test string representation of volume mount with options."""
        mount = Mount(
            source="data-volume",
            target="/workspace/data",
            type=MountType.VOLUME,
            options=["ro", "noexec", "nosuid"]
        )
        expected = "source=data-volume,target=/workspace/data,type=volume,options=ro,noexec,nosuid"
        assert_that(str(mount)).is_equal_to(expected)


class TestMountEdgeCases:
    """Test cases for mount edge cases and boundary conditions."""

    def test_mount_with_minimal_valid_paths(self):
        """Test mount with minimal valid absolute paths."""
        mount = Mount(
            source="/a",
            target="/b",
            type=MountType.BIND
        )
        assert_that(mount.source).is_equal_to("/a")
        assert_that(mount.target).is_equal_to("/b")

    def test_mount_with_long_valid_paths(self):
        """Test mount with long but valid absolute paths."""
        long_path = "/" + "a" * 255  # 256 characters total
        mount = Mount(
            source=long_path,
            target="/workspace/data",
            type=MountType.BIND
        )
        assert_that(mount.source).is_equal_to(long_path)

    def test_mount_with_minimal_valid_volume_name(self):
        """Test mount with minimal valid volume name."""
        mount = Mount(
            source="abc",
            target="/workspace/data",
            type=MountType.VOLUME
        )
        assert_that(mount.source).is_equal_to("abc")

    def test_mount_with_long_valid_volume_name(self):
        """Test mount with long but valid volume name."""
        long_volume = "a" * 256
        mount = Mount(
            source=long_volume,
            target="/workspace/data",
            type=MountType.VOLUME
        )
        assert_that(mount.source).is_equal_to(long_volume)

    def test_mount_with_special_characters_in_volume_name(self):
        """Test mount with valid special characters in volume name."""
        mount = Mount(
            source="volume-name_123",
            target="/workspace/data",
            type=MountType.VOLUME
        )
        assert_that(mount.source).is_equal_to("volume-name_123")

    def test_mount_with_special_characters_in_path(self):
        """Test mount with valid special characters in absolute path."""
        mount = Mount(
            source="/home/user/data-folder_123",
            target="/workspace/data-folder_123",
            type=MountType.BIND
        )
        assert_that(mount.source).is_equal_to("/home/user/data-folder_123")
        assert_that(mount.target).is_equal_to("/workspace/data-folder_123")


class TestMountCompose:
    """Test cases for Mount compose method."""

    def test_compose_bind_mount_without_options(self):
        """Test that bind mount without options composes correctly."""
        mount = Mount(
            source="/home/user/data",
            target="/workspace/data",
            type=MountType.BIND
        )
        result = mount.compose()
        expected = {
            "mounts": ["source=/home/user/data,target=/workspace/data,type=bind"]
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_bind_mount_with_single_option(self):
        """Test that bind mount with single option composes correctly."""
        mount = Mount(
            source="/home/user/data",
            target="/workspace/data",
            type=MountType.BIND,
            options=["ro"]
        )
        result = mount.compose()
        expected = {
            "mounts": ["source=/home/user/data,target=/workspace/data,type=bind,options=ro"]
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_bind_mount_with_multiple_options(self):
        """Test that bind mount with multiple options composes correctly."""
        mount = Mount(
            source="/home/user/data",
            target="/workspace/data",
            type=MountType.BIND,
            options=["ro", "noexec", "nosuid"]
        )
        result = mount.compose()
        expected = {
            "mounts": ["source=/home/user/data,target=/workspace/data,type=bind,options=ro,noexec,nosuid"]
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_volume_mount_without_options(self):
        """Test that volume mount without options composes correctly."""
        mount = Mount(
            source="data-volume",
            target="/workspace/data",
            type=MountType.VOLUME
        )
        result = mount.compose()
        expected = {
            "mounts": ["source=data-volume,target=/workspace/data,type=volume"]
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_volume_mount_with_options(self):
        """Test that volume mount with options composes correctly."""
        mount = Mount(
            source="cache-volume",
            target="/cache",
            type=MountType.VOLUME,
            options=["ro", "noexec"]
        )
        result = mount.compose()
        expected = {
            "mounts": ["source=cache-volume,target=/cache,type=volume,options=ro,noexec"]
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_mount_with_special_characters(self):
        """Test that mount with special characters in paths composes correctly."""
        mount = Mount(
            source="/home/user/data-folder_123",
            target="/workspace/data-folder_123",
            type=MountType.BIND,
            options=["ro"]
        )
        result = mount.compose()
        expected = {
            "mounts": ["source=/home/user/data-folder_123,target=/workspace/data-folder_123,type=bind,options=ro"]
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_mount_with_long_volume_name(self):
        """Test that mount with long volume name composes correctly."""
        long_volume = "a" * 256
        mount = Mount(
            source=long_volume,
            target="/workspace/data",
            type=MountType.VOLUME
        )
        result = mount.compose()
        expected = {
            "mounts": [f"source={long_volume},target=/workspace/data,type=volume"]
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_mount_with_long_path(self):
        """Test that mount with long path composes correctly."""
        long_path = "/" + "a" * 255  # 256 characters total
        mount = Mount(
            source=long_path,
            target="/workspace/data",
            type=MountType.BIND
        )
        result = mount.compose()
        expected = {
            "mounts": [f"source={long_path},target=/workspace/data,type=bind"]
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_mount_returns_dict(self):
        """Test that compose method always returns a dictionary."""
        mount = Mount(
            source="/test",
            target="/test",
            type=MountType.BIND
        )
        result = mount.compose()
        assert_that(result).is_instance_of(dict)

    def test_compose_mount_has_mounts_key(self):
        """Test that compose result always has 'mounts' key."""
        mount = Mount(
            source="/test",
            target="/test",
            type=MountType.BIND
        )
        result = mount.compose()
        assert_that(result).contains_key("mounts")

    def test_compose_mount_mounts_is_list(self):
        """Test that compose result 'mounts' value is always a list."""
        mount = Mount(
            source="/test",
            target="/test",
            type=MountType.BIND
        )
        result = mount.compose()
        assert_that(result["mounts"]).is_instance_of(list)

    def test_compose_mount_mounts_has_one_element(self):
        """Test that compose result 'mounts' list has exactly one element."""
        mount = Mount(
            source="/test",
            target="/test",
            type=MountType.BIND
        )
        result = mount.compose()
        assert_that(result["mounts"]).is_length(1)
