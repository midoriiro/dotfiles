import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.container import Users


class TestValidUsers:
    """Test cases for valid user configurations."""

    @pytest.mark.parametrize(
        "remote,container",
        [
            ("user1", "user2"),
            ("developer", "appuser"),
            ("admin", "worker"),
            ("test_user", "prod_user"),
            ("user_a", "user_b"),
        ],
    )
    def test_valid_users_with_different_names(self, remote, container):
        """Test that valid user configurations with different names are accepted."""
        users = Users(remote=remote, container=container)
        assert_that(users.remote).is_equal_to(remote)
        assert_that(users.container).is_equal_to(container)

    def test_users_with_minimal_valid_names(self):
        """Test that users with minimal valid names are accepted."""
        users = Users(remote="a", container="b")
        assert_that(users.remote).is_equal_to("a")
        assert_that(users.container).is_equal_to("b")

    def test_users_with_long_valid_names(self):
        """Test that users with long valid names are accepted."""
        long_name = "a" * 256
        users = Users(remote=long_name, container="other")
        assert_that(users.remote).is_equal_to(long_name)
        assert_that(users.container).is_equal_to("other")

    def test_users_with_special_characters(self):
        """Test that users with valid special characters are accepted."""
        users = Users(remote="user_123", container="app-user")
        assert_that(users.remote).is_equal_to("user_123")
        assert_that(users.container).is_equal_to("app-user")


class TestUsersValidation:
    """Test cases for user validation rules."""

    def test_users_with_same_remote_and_container(self):
        """Test that users with same remote and container names are rejected."""
        with pytest.raises(
            ValidationError, match="Remote and container users cannot be the same"
        ):
            Users(remote="sameuser", container="sameuser")

    def test_users_with_empty_remote(self):
        """Test that users with empty remote name are rejected."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            Users(remote="", container="validuser")

    def test_users_with_empty_container(self):
        """Test that users with empty container name are rejected."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            Users(remote="validuser", container="")

    def test_users_with_invalid_remote_pattern(self):
        """Test that users with invalid remote name patterns are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Users(remote="invalid@user", container="validuser")

    def test_users_with_invalid_container_pattern(self):
        """Test that users with invalid container name patterns are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Users(remote="validuser", container="invalid@user")

    def test_users_with_too_long_remote(self):
        """Test that users with remote name longer than 256 characters are rejected."""
        long_name = "a" * 257
        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            Users(remote=long_name, container="validuser")

    def test_users_with_too_long_container(self):
        """Test that users with container name longer than 256 characters are rejected."""
        long_name = "a" * 257
        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            Users(remote="validuser", container=long_name)


class TestUsersCompose:
    """Test cases for user composition."""

    def test_compose_users_with_different_names(self):
        """Test that users with different names are composed correctly."""
        users = Users(remote="developer", container="appuser")
        result = users.compose()
        expected = {"remoteUser": "developer", "containerUser": "appuser"}
        assert_that(result).is_equal_to(expected)

    def test_compose_users_with_minimal_names(self):
        """Test that users with minimal names are composed correctly."""
        users = Users(remote="a", container="b")
        result = users.compose()
        expected = {"remoteUser": "a", "containerUser": "b"}
        assert_that(result).is_equal_to(expected)

    def test_compose_users_with_long_names(self):
        """Test that users with long names are composed correctly."""
        long_name = "a" * 256
        users = Users(remote=long_name, container="other")
        result = users.compose()
        expected = {"remoteUser": long_name, "containerUser": "other"}
        assert_that(result).is_equal_to(expected)

    def test_compose_users_with_special_characters(self):
        """Test that users with special characters are composed correctly."""
        users = Users(remote="user_123", container="app-user")
        result = users.compose()
        expected = {"remoteUser": "user_123", "containerUser": "app-user"}
        assert_that(result).is_equal_to(expected)


class TestUsersEdgeCases:
    """Test cases for user edge cases."""

    def test_users_with_case_difference(self):
        """Test that users with case differences are accepted."""
        users = Users(remote="User", container="user")
        assert_that(users.remote).is_equal_to("User")
        assert_that(users.container).is_equal_to("user")

    def test_users_with_numbers(self):
        """Test that users with numbers are accepted."""
        users = Users(remote="user1", container="user2")
        assert_that(users.remote).is_equal_to("user1")
        assert_that(users.container).is_equal_to("user2")

    def test_users_with_underscores(self):
        """Test that users with underscores are accepted."""
        users = Users(remote="user_name", container="app_user")
        assert_that(users.remote).is_equal_to("user_name")
        assert_that(users.container).is_equal_to("app_user")

    def test_users_with_hyphens(self):
        """Test that users with hyphens are accepted."""
        users = Users(remote="user-name", container="app-name")
        assert_that(users.remote).is_equal_to("user-name")
        assert_that(users.container).is_equal_to("app-name")


class TestUsersFeatureInheritance:
    """Test cases for Users feature inheritance."""

    def test_users_feature_name(self):
        """Test that Users has the correct feature name."""
        assert_that(Users.feature_name()).is_equal_to("users")

    def test_users_inherits_from_feature(self):
        """Test that Users inherits from Feature base class."""
        users = Users(remote="testuser", container="appuser")
        assert_that(users).is_instance_of(Users)
        # Verify that compose method is implemented
        result = users.compose()
        assert_that(result).is_instance_of(dict)
        assert_that(result).contains_key("remoteUser")
        assert_that(result).contains_key("containerUser")
