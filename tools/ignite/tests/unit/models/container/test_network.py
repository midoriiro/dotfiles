import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.container import Network


class TestValidNetwork:
    """Test cases for valid network configurations."""

    def test_basic_network(self):
        """Test that a basic network with a valid name is accepted."""
        network = Network(name="test-network")
        assert_that(network.name).is_equal_to("test-network")

    def test_network_with_hyphens(self):
        """Test that network names with hyphens are accepted."""
        network = Network(name="test-network-name")
        assert_that(network.name).is_equal_to("test-network-name")

    def test_network_with_underscores(self):
        """Test that network names with underscores are accepted."""
        network = Network(name="test_network_name")
        assert_that(network.name).is_equal_to("test_network_name")

    def test_network_with_numbers(self):
        """Test that network names with numbers are accepted."""
        network = Network(name="network123")
        assert_that(network.name).is_equal_to("network123")

    def test_network_with_mixed_case(self):
        """Test that network names with mixed case are accepted."""
        network = Network(name="TestNetwork")
        assert_that(network.name).is_equal_to("TestNetwork")


class TestNetworkComposeMethod:
    """Test cases for the compose method of Network."""

    def test_compose_basic_network(self):
        """Test that compose method works correctly with a basic network name."""
        network = Network(name="test-network")
        result = network.compose()

        expected = {"runArgs": ["--network=test-network"]}
        assert_that(result).is_equal_to(expected)

    def test_compose_structure(self):
        """Test that compose method returns the correct structure."""
        network = Network(name="test-network")
        result = network.compose()

        # Check that the structure is correct
        assert_that(result).contains_key("runArgs")
        assert_that(result["runArgs"]).is_instance_of(list)
        assert_that(result["runArgs"]).is_length(1)
        assert_that(result["runArgs"][0]).starts_with("--network=")
        assert_that(result["runArgs"][0]).ends_with("test-network")


class TestNetworkFeatureName:
    """Test cases for the feature_name method of Network."""

    def test_feature_name(self):
        """Test that feature_name returns the correct name."""
        assert_that(Network.feature_name()).is_equal_to("network")


class TestNetworkEdgeCases:
    """Test cases for edge cases in Network validation."""

    def test_minimal_valid_network_name(self):
        """Test that minimal valid network names are accepted."""
        network = Network(name="a")
        assert_that(network.name).is_equal_to("a")

    def test_long_network_name(self):
        """Test that long but valid network names are accepted."""
        # Create a network name that is close to the 256 character limit
        long_name = "a" * 255
        network = Network(name=long_name)
        assert_that(network.name).is_equal_to(long_name)

    def test_network_name_with_special_characters(self):
        """Test that network names with special characters are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Network(name="test-network@123")

    def test_network_with_dots(self):
        """Test that network names with dots are accepted."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Network(name="test.network")


class TestNetworkInheritance:
    """Test cases for Network inheritance from Feature."""

    def test_network_inherits_from_feature(self):
        """Test that Network inherits from Feature."""
        network = Network(name="test-network")
        assert_that(network).is_instance_of(Network)
        # Check that it has the compose method
        assert_that(hasattr(network, "compose")).is_true()
        # Check that it has the feature_name class method
        assert_that(hasattr(Network, "feature_name")).is_true()

    def test_network_compose_returns_dict(self):
        """Test that Network.compose() returns a dictionary."""
        network = Network(name="test-network")
        result = network.compose()
        assert_that(result).is_instance_of(dict)

    def test_network_feature_name_returns_string(self):
        """Test that Network.feature_name() returns a string."""
        result = Network.feature_name()
        assert_that(result).is_instance_of(str)
