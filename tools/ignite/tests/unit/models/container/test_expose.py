import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.container import URL, Expose, Socket, URLScheme


class TestValidExpose:
    """Test cases for valid Expose configurations."""

    def test_expose_with_socket_only(self):
        """Test that Expose with only socket is accepted."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        expose = Expose(socket=socket)
        assert_that(expose.socket).is_equal_to(socket)
        assert_that(expose.address).is_none()

    def test_expose_with_address_only(self):
        """Test that Expose with only address is accepted."""
        address = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        expose = Expose(address=address)
        assert_that(expose.address).is_equal_to(address)
        assert_that(expose.socket).is_none()

    def test_expose_with_socket_and_no_address(self):
        """Test that Expose with socket and None address is accepted."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        expose = Expose(socket=socket, address=None)
        assert_that(expose.socket).is_equal_to(socket)
        assert_that(expose.address).is_none()

    def test_expose_with_address_and_no_socket(self):
        """Test that Expose with address and None socket is accepted."""
        address = URL(scheme=URLScheme.TCP, host="example.com", port=8080)
        expose = Expose(socket=None, address=address)
        assert_that(expose.address).is_equal_to(address)
        assert_that(expose.socket).is_none()


class TestExposeValidation:
    """Test cases for Expose validation rules."""

    def test_expose_with_both_socket_and_address(self):
        """Test that Expose with both socket and address is rejected."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        address = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        with pytest.raises(
            ValidationError, match="Exactly one of 'socket' or 'address' must be set"
        ):
            Expose(socket=socket, address=address)

    def test_expose_with_neither_socket_nor_address(self):
        """Test that Expose with neither socket nor address is rejected."""
        with pytest.raises(
            ValidationError, match="Exactly one of 'socket' or 'address' must be set"
        ):
            Expose(socket=None, address=None)

    def test_expose_with_empty_socket_and_address(self):
        """Test that Expose with empty socket and address is rejected."""
        with pytest.raises(
            ValidationError, match="Exactly one of 'socket' or 'address' must be set"
        ):
            Expose()


class TestExposeCompose:
    """Test cases for Expose compose method."""

    def test_expose_compose_with_socket(self):
        """Test that Expose compose method works correctly with socket."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        expose = Expose(socket=socket)
        result = expose.compose()

        expected = {
            "mounts": ["source=/tmp/docker.sock,target=/var/run/docker.sock,type=bind"]
        }
        assert_that(result).is_equal_to(expected)

    def test_expose_compose_with_address(self):
        """Test that Expose compose method works correctly with address."""
        address = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        expose = Expose(address=address)
        result = expose.compose()

        expected = {"remoteEnv": {"CONTAINER_HOST": "ssh://localhost:22"}}
        assert_that(result).is_equal_to(expected)

    def test_expose_compose_with_address_without_port(self):
        """Test that Expose compose method works correctly with address without port."""
        address = URL(scheme=URLScheme.TCP, host="example.com")
        expose = Expose(address=address)
        result = expose.compose()

        expected = {"remoteEnv": {"CONTAINER_HOST": "tcp://example.com"}}
        assert_that(result).is_equal_to(expected)


class TestExposeFeatureInheritance:
    """Test cases for Expose feature inheritance."""

    def test_expose_inherits_from_feature(self):
        """Test that Expose inherits from Feature base class."""
        expose = Expose(
            socket=Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        )
        assert_that(expose).is_instance_of(Expose)
        assert_that(hasattr(expose, "compose")).is_true()

    def test_expose_feature_name(self):
        """Test that Expose has correct feature name."""
        Expose(socket=Socket(host="/tmp/docker.sock", container="/var/run/docker.sock"))
        assert_that(Expose.feature_name()).is_equal_to("expose")


class TestExposeEdgeCases:
    """Test cases for Expose edge cases."""

    def test_expose_with_different_socket_paths(self):
        """Test that Expose works with different socket paths."""
        socket = Socket(host="/var/run/docker.sock", container="/tmp/docker.sock")
        expose = Expose(socket=socket)
        assert_that(expose.socket).is_equal_to(socket)
        assert_that(expose.address).is_none()

    def test_expose_with_different_address_schemes(self):
        """Test that Expose works with different address schemes."""
        address = URL(scheme=URLScheme.TCP, host="api.example.com", port=3000)
        expose = Expose(address=address)
        assert_that(expose.address).is_equal_to(address)
        assert_that(expose.socket).is_none()

    def test_expose_with_minimum_valid_port(self):
        """Test that Expose works with minimum valid port."""
        address = URL(scheme=URLScheme.SSH, host="localhost", port=1)
        expose = Expose(address=address)
        assert_that(expose.address).is_equal_to(address)
        assert_that(expose.socket).is_none()

    def test_expose_with_maximum_valid_port(self):
        """Test that Expose works with maximum valid port."""
        address = URL(scheme=URLScheme.TCP, host="localhost", port=65535)
        expose = Expose(address=address)
        assert_that(expose.address).is_equal_to(address)
        assert_that(expose.socket).is_none()


class TestExposeModelBehavior:
    """Test cases for Expose model behavior."""

    def test_expose_model_construction_with_socket(self):
        """Test that Expose models can be constructed correctly with socket."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        expose = Expose(socket=socket)
        assert_that(expose.socket).is_equal_to(socket)
        assert_that(expose.address).is_none()

    def test_expose_model_construction_with_address(self):
        """Test that Expose models can be constructed correctly with address."""
        address = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        expose = Expose(address=address)
        assert_that(expose.address).is_equal_to(address)
        assert_that(expose.socket).is_none()

    def test_expose_model_equality_with_socket(self):
        """Test that Expose models with same socket are equal."""
        socket1 = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        socket2 = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        expose1 = Expose(socket=socket1)
        expose2 = Expose(socket=socket2)
        assert_that(expose1).is_equal_to(expose2)

    def test_expose_model_equality_with_address(self):
        """Test that Expose models with same address are equal."""
        address1 = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        address2 = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        expose1 = Expose(address=address1)
        expose2 = Expose(address=address2)
        assert_that(expose1).is_equal_to(expose2)

    def test_expose_model_inequality(self):
        """Test that Expose models with different configurations are not equal."""
        socket = Socket(host="/tmp/docker.sock", container="/var/run/docker.sock")
        address = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        expose1 = Expose(socket=socket)
        expose2 = Expose(address=address)
        assert_that(expose1).is_not_equal_to(expose2)
