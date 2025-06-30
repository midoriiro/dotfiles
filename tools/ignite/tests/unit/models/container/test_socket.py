import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.container import Mount, MountType, Socket
from ignite.models.fs import AbsolutePath


class TestValidSocket:
    """Test cases for valid socket configurations."""

    @pytest.mark.parametrize(
        "host_path,container_path",
        [
            ("/tmp/docker.sock", "/var/run/docker.sock"),
            ("/var/run/docker.sock", "/var/run/docker.sock"),
            ("/tmp/mysql.sock", "/var/run/mysqld/mysqld.sock"),
            ("/tmp/postgres.sock", "/var/run/postgresql/.s.PGSQL.5432"),
            ("/tmp/redis.sock", "/tmp/redis.sock"),
        ],
    )
    def test_valid_socket_paths(self, host_path, container_path):
        """Test that valid socket paths are accepted."""
        socket = Socket(host=host_path, container=container_path)
        assert_that(socket.host).is_equal_to(host_path)
        assert_that(socket.container).is_equal_to(container_path)

    def test_socket_with_same_paths(self):
        """Test that socket with same host and container paths is accepted."""
        socket = Socket(host="/tmp/docker.sock", container="/tmp/docker.sock")
        assert_that(socket.host).is_equal_to("/tmp/docker.sock")
        assert_that(socket.container).is_equal_to("/tmp/docker.sock")


class TestSocketValidation:
    """Test cases for socket validation rules."""

    def test_socket_with_relative_host_path(self):
        """Test that socket with relative host path is rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Socket(host="tmp/docker.sock", container="/var/run/docker.sock")

    def test_socket_with_relative_container_path(self):
        """Test that socket with relative container path is rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Socket(host="/tmp/docker.sock", container="var/run/docker.sock")

    def test_socket_with_empty_host_path(self):
        """Test that socket with empty host path is rejected."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            Socket(host="", container="/var/run/docker.sock")

    def test_socket_with_empty_container_path(self):
        """Test that socket with empty container path is rejected."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            Socket(host="/tmp/docker.sock", container="")

    def test_socket_with_too_long_host_path(self):
        """Test that socket with host path longer than 256 characters is rejected."""
        long_path = "/" + "a" * 256
        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            Socket(host=long_path, container="/var/run/docker.sock")

    def test_socket_with_too_long_container_path(self):
        """Test that socket with container path longer than 256 characters is rejected."""
        long_path = "/" + "a" * 256
        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            Socket(host="/tmp/docker.sock", container=long_path)

    def test_socket_with_invalid_host_path_characters(self):
        """Test that socket with invalid characters in host path is rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Socket(host="/tmp/docker@.sock", container="/var/run/docker.sock")

    def test_socket_with_invalid_container_path_characters(self):
        """Test that socket with invalid characters in container path is rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Socket(host="/tmp/docker.sock", container="/var/run/docker#.sock")

    def test_socket_with_host_path_ending_without_slash(self):
        """Test that socket with host path ending without slash is accepted."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        assert_that(socket.host).is_equal_to("/tmp/docker.sock")

    def test_socket_with_host_path_ending_with_slash(self):
        """Test that socket with host path ending with slash is accepted."""
        socket = Socket(host="/tmp/", container="/var/run/docker.sock")
        assert_that(socket.host).is_equal_to("/tmp/")

    def test_socket_with_container_path_ending_without_slash(self):
        """Test that socket with container path ending without slash is accepted."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        assert_that(socket.container).is_equal_to("/var/run/docker.sock")

    def test_socket_with_container_path_ending_with_slash(self):
        """Test that socket with container path ending with slash is accepted."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/")
        assert_that(socket.container).is_equal_to("/var/run/")


class TestSocketStringRepresentation:
    """Test cases for socket string representation."""

    def test_socket_string_representation(self):
        """Test that socket string representation creates correct mount string."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        result = str(socket)
        expected = "source=/tmp/docker.sock,target=/var/run/docker.sock,type=bind"
        assert_that(result).is_equal_to(expected)

    def test_socket_string_representation_with_different_paths(self):
        """Test that socket string representation works with different paths."""
        socket = Socket(host="/var/run/docker.sock", container="/tmp/docker.sock")
        result = str(socket)
        expected = "source=/var/run/docker.sock,target=/tmp/docker.sock,type=bind"
        assert_that(result).is_equal_to(expected)

    def test_socket_string_representation_with_same_paths(self):
        """Test that socket string representation works with same paths."""
        socket = Socket(host="/tmp/docker.sock", container="/tmp/docker.sock")
        result = str(socket)
        expected = "source=/tmp/docker.sock,target=/tmp/docker.sock,type=bind"
        assert_that(result).is_equal_to(expected)

    def test_socket_string_representation_with_nested_paths(self):
        """Test that socket string representation works with nested paths."""
        socket = Socket(
            host="/var/run/docker/docker.sock", container="/var/run/docker/docker.sock"
        )
        result = str(socket)
        expected = "source=/var/run/docker/docker.sock,target=/var/run/docker/docker.sock,type=bind"
        assert_that(result).is_equal_to(expected)


class TestSocketEdgeCases:
    """Test cases for socket edge cases."""

    def test_socket_with_minimal_valid_host_path(self):
        """Test that socket with minimal valid host path is accepted."""
        socket = Socket(host="/a", container="/var/run/docker.sock")
        assert_that(socket.host).is_equal_to("/a")
        assert_that(socket.container).is_equal_to("/var/run/docker.sock")

    def test_socket_with_minimal_valid_container_path(self):
        """Test that socket with minimal valid container path is accepted."""
        socket = Socket(host="/tmp/docker.sock", container="/a")
        assert_that(socket.host).is_equal_to("/tmp/docker.sock")
        assert_that(socket.container).is_equal_to("/a")

    def test_socket_with_long_valid_host_path(self):
        """Test that socket with long valid host path is accepted."""
        long_path = "/" + "a" * 255
        socket = Socket(host=long_path, container="/var/run/docker.sock")
        assert_that(socket.host).is_equal_to(long_path)
        assert_that(socket.container).is_equal_to("/var/run/docker.sock")

    def test_socket_with_long_valid_container_path(self):
        """Test that socket with long valid container path is accepted."""
        long_path = "/" + "a" * 255
        socket = Socket(host="/tmp/docker.sock", container=long_path)
        assert_that(socket.host).is_equal_to("/tmp/docker.sock")
        assert_that(socket.container).is_equal_to(long_path)

    def test_socket_with_special_characters_in_paths(self):
        """Test that socket with valid special characters in paths is accepted."""
        socket = Socket(host="/tmp/docker-sock", container="/var/run/docker_sock")
        assert_that(socket.host).is_equal_to("/tmp/docker-sock")
        assert_that(socket.container).is_equal_to("/var/run/docker_sock")

    def test_socket_with_numbers_in_paths(self):
        """Test that socket with numbers in paths is accepted."""
        socket = Socket(host="/tmp/docker123.sock", container="/var/run/docker456.sock")
        assert_that(socket.host).is_equal_to("/tmp/docker123.sock")
        assert_that(socket.container).is_equal_to("/var/run/docker456.sock")

    def test_socket_with_dots_in_paths(self):
        """Test that socket with dots in paths is accepted."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        assert_that(socket.host).is_equal_to("/tmp/docker.sock")
        assert_that(socket.container).is_equal_to("/var/run/docker.sock")


class TestSocketIntegration:
    """Test cases for socket integration with other components."""

    def test_socket_creates_valid_mount(self):
        """Test that socket creates a valid mount object when converted to string."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        mount_string = str(socket)

        # Verify the mount string can be parsed back into a mount object
        mount = Mount(
            source="/tmp/docker.sock",
            target="/var/run/docker.sock",
            type=MountType.BIND,
        )
        expected_mount_string = str(mount)
        assert_that(mount_string).is_equal_to(expected_mount_string)

    def test_socket_with_mount_type_bind(self):
        """Test that socket always creates bind mount type."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        mount_string = str(socket)
        assert_that(mount_string).contains("type=bind")

    def test_socket_paths_are_absolute_paths(self):
        """Test that socket paths are properly typed as AbsolutePath."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        assert_that(socket.host).is_instance_of(str)
        assert_that(socket.container).is_instance_of(str)
        # Verify they are valid absolute paths
        assert_that(socket.host).starts_with("/")
        assert_that(socket.container).starts_with("/")
