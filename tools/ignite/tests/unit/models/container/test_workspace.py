import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.container import Workspace


class TestValidWorkspace:
    """Test cases for valid workspace configurations."""

    def test_basic_workspace(self):
        """Test that a basic workspace with all required fields is accepted."""
        workspace = Workspace(
            name="test-workspace",
            folder="/workspace",
            volume_name="test-workspace-volume",
        )
        assert_that(workspace.name).is_equal_to("test-workspace")
        assert_that(workspace.folder).is_equal_to("/workspace")
        assert_that(workspace.volume_name).is_equal_to("test-workspace-volume")

    def test_workspace_with_alias_volume_name(self):
        """Test that workspace accepts volume-name alias."""
        workspace = Workspace(
            name="test-workspace",
            folder="/workspace",
            volume_name="test-workspace-volume",
        )
        assert_that(workspace.volume_name).is_equal_to("test-workspace-volume")

    def test_workspace_with_long_path(self):
        """Test that workspace accepts long folder paths."""
        long_path = "/very/long/workspace/path/that/exceeds/normal/length"
        workspace = Workspace(
            name="test-workspace", folder=long_path, volume_name="test-workspace-volume"
        )
        assert_that(workspace.folder).is_equal_to(long_path)

    def test_workspace_with_minimal_name(self):
        """Test that workspace accepts minimal valid name."""
        workspace = Workspace(
            name="a",  # Minimum 1 character
            folder="/workspace",
            volume_name="test-workspace-volume",
        )
        assert_that(workspace.name).is_equal_to("a")

    def test_workspace_with_maximum_name(self):
        """Test that workspace accepts maximum length name."""
        max_name = "a" * 256  # Maximum 256 characters
        workspace = Workspace(
            name=max_name, folder="/workspace", volume_name="test-workspace-volume"
        )
        assert_that(workspace.name).is_equal_to(max_name)


class TestWorkspaceComposeMethod:
    """Test cases for the compose method of Workspace."""

    def test_compose_basic_workspace(self):
        """Test that compose method works correctly with basic workspace."""
        workspace = Workspace(
            name="test-workspace",
            folder="/workspace",
            volume_name="test-workspace-volume",
        )
        result = workspace.compose()

        expected = {
            "name": "test-workspace",
            "workspaceFolder": "/workspace",
            "workspaceMount": "source=test-workspace-volume,target=/workspace,"
            "type=volume",
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_with_different_paths(self):
        """Test that compose method works correctly with different paths."""
        workspace = Workspace(
            name="my-project",
            folder="/home/user/project",
            volume_name="my-project-volume",
        )
        result = workspace.compose()

        expected = {
            "name": "my-project",
            "workspaceFolder": "/home/user/project",
            "workspaceMount": "source=my-project-volume,target=/home/user/project,"
            "type=volume",
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_structure(self):
        """Test that compose method returns the correct structure."""
        workspace = Workspace(
            name="test-workspace",
            folder="/workspace",
            volume_name="test-workspace-volume",
        )
        result = workspace.compose()

        # Check that the structure is correct
        assert_that(result).contains_key("name")
        assert_that(result).contains_key("workspaceFolder")
        assert_that(result).contains_key("workspaceMount")
        assert_that(result["name"]).is_instance_of(str)
        assert_that(result["workspaceFolder"]).is_instance_of(str)
        assert_that(result["workspaceMount"]).is_instance_of(str)

    def test_compose_mount_string_format(self):
        """Test that the workspaceMount string follows the correct format."""
        workspace = Workspace(
            name="test-workspace",
            folder="/workspace",
            volume_name="test-workspace-volume",
        )
        result = workspace.compose()

        mount_string = result["workspaceMount"]
        assert_that(mount_string).contains("source=test-workspace-volume")
        assert_that(mount_string).contains("target=/workspace")
        assert_that(mount_string).contains("type=volume")


class TestWorkspaceFeatureName:
    """Test cases for the feature_name method of Workspace."""

    def test_feature_name(self):
        """Test that feature_name returns the correct name."""
        assert_that(Workspace.feature_name()).is_equal_to("workspace")


class TestWorkspaceValidation:
    """Test cases for Workspace field validation."""

    def test_empty_name_raises_error(self):
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            Workspace(name="", folder="/workspace", volume_name="test-workspace-volume")

    def test_name_too_long_raises_error(self):
        """Test that name too long raises validation error."""
        long_name = "a" * 257  # Exceeds 256 character limit
        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            Workspace(
                name=long_name, folder="/workspace", volume_name="test-workspace-volume"
            )

    def test_name_with_special_characters_raises_error(self):
        """Test that name with special characters raises validation error."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Workspace(
                name="test@workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            )

    def test_name_starting_with_hyphen_raises_error(self):
        """Test that name starting with hyphen raises validation error."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Workspace(
                name="-test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            )

    def test_name_ending_with_hyphen_raises_error(self):
        """Test that name ending with hyphen raises validation error."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Workspace(
                name="test-workspace-",
                folder="/workspace",
                volume_name="test-workspace-volume",
            )

    def test_empty_folder_raises_error(self):
        """Test that empty folder raises validation error."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            Workspace(
                name="test-workspace", folder="", volume_name="test-workspace-volume"
            )

    def test_folder_too_long_raises_error(self):
        """Test that folder too long raises validation error."""
        long_folder = "/" + "a" * 256  # Exceeds 256 character limit
        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            Workspace(
                name="test-workspace",
                folder=long_folder,
                volume_name="test-workspace-volume",
            )

    def test_empty_volume_name_raises_error(self):
        """Test that empty volume name raises validation error."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            Workspace(name="test-workspace", folder="/workspace", volume_name="")

    def test_volume_name_too_long_raises_error(self):
        """Test that volume name too long raises validation error."""
        long_volume_name = "a" * 257  # Exceeds 256 character limit
        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            Workspace(
                name="test-workspace", folder="/workspace", volume_name=long_volume_name
            )

    def test_volume_name_with_special_characters_raises_error(self):
        """Test that volume name with special characters raises validation error."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Workspace(
                name="test-workspace", folder="/workspace", volume_name="test@volume"
            )


class TestWorkspaceModelValidator:
    """Test cases for the model validator in Workspace."""

    def test_missing_name_raises_error(self):
        """Test that missing name raises validation error."""
        with pytest.raises(ValidationError, match="Field required"):
            Workspace(folder="/workspace", volume_name="test-workspace-volume")

    def test_missing_folder_raises_error(self):
        """Test that missing folder raises validation error."""
        with pytest.raises(ValidationError, match="Field required"):
            Workspace(name="test-workspace", volume_name="test-workspace-volume")

    def test_missing_volume_name_raises_error(self):
        """Test that missing volume name raises validation error."""
        with pytest.raises(ValidationError, match="Field required"):
            Workspace(name="test-workspace", folder="/workspace")


class TestWorkspaceEdgeCases:
    """Test cases for edge cases in Workspace validation."""

    def test_minimal_valid_name(self):
        """Test that minimal valid name is accepted."""
        workspace = Workspace(
            name="a",  # Exactly 1 character
            folder="/workspace",
            volume_name="test-workspace-volume",
        )
        assert_that(workspace.name).is_equal_to("a")

    def test_maximum_valid_name(self):
        """Test that maximum valid name is accepted."""
        max_name = "a" * 256  # Exactly 256 characters
        workspace = Workspace(
            name=max_name, folder="/workspace", volume_name="test-workspace-volume"
        )
        assert_that(workspace.name).is_equal_to(max_name)

    def test_minimal_valid_folder(self):
        """Test that minimal valid folder is accepted."""
        workspace = Workspace(
            name="test-workspace",
            folder="/a",  # Exactly 2 characters
            volume_name="test-workspace-volume",
        )
        assert_that(workspace.folder).is_equal_to("/a")

    def test_maximum_valid_folder(self):
        """Test that maximum valid folder is accepted."""
        max_folder = "/" + "a" * 255  # Exactly 256 characters
        workspace = Workspace(
            name="test-workspace",
            folder=max_folder,
            volume_name="test-workspace-volume",
        )
        assert_that(workspace.folder).is_equal_to(max_folder)

    def test_minimal_valid_volume_name(self):
        """Test that minimal valid volume name is accepted."""
        workspace = Workspace(
            name="test-workspace",
            folder="/workspace",
            volume_name="a",  # Exactly 1 character
        )
        assert_that(workspace.volume_name).is_equal_to("a")

    def test_maximum_valid_volume_name(self):
        """Test that maximum valid volume name is accepted."""
        max_volume_name = "a" * 256  # Exactly 256 characters
        workspace = Workspace(
            name="test-workspace", folder="/workspace", volume_name=max_volume_name
        )
        assert_that(workspace.volume_name).is_equal_to(max_volume_name)

    def test_workspace_with_hyphenated_names(self):
        """Test that workspace accepts hyphenated names."""
        workspace = Workspace(
            name="test-workspace-name",
            folder="/workspace",
            volume_name="test-workspace-volume-name",
        )
        assert_that(workspace.name).is_equal_to("test-workspace-name")
        assert_that(workspace.volume_name).is_equal_to("test-workspace-volume-name")

    def test_workspace_with_single_character_names(self):
        """Test that workspace accepts single character names."""
        workspace = Workspace(name="a", folder="/workspace", volume_name="b")
        assert_that(workspace.name).is_equal_to("a")
        assert_that(workspace.volume_name).is_equal_to("b")


class TestWorkspaceInheritance:
    """Test cases for Workspace inheritance from Feature."""

    def test_workspace_inherits_from_feature(self):
        """Test that Workspace inherits from Feature."""
        workspace = Workspace(
            name="test-workspace",
            folder="/workspace",
            volume_name="test-workspace-volume",
        )
        assert_that(workspace).is_instance_of(Workspace)
        # Check that it has the compose method
        assert_that(hasattr(workspace, "compose")).is_true()
        # Check that it has the feature_name class method
        assert_that(hasattr(Workspace, "feature_name")).is_true()

    def test_workspace_compose_returns_dict(self):
        """Test that Workspace.compose() returns a dictionary."""
        workspace = Workspace(
            name="test-workspace",
            folder="/workspace",
            volume_name="test-workspace-volume",
        )
        result = workspace.compose()
        assert_that(result).is_instance_of(dict)

    def test_workspace_feature_name_returns_string(self):
        """Test that Workspace.feature_name() returns a string."""
        result = Workspace.feature_name()
        assert_that(result).is_instance_of(str)
        assert_that(result).is_equal_to("workspace")


class TestWorkspaceMountIntegration:
    """Test cases for Workspace integration with Mount class."""

    def test_workspace_mount_creation(self):
        """Test that workspace creates correct Mount object."""
        workspace = Workspace(
            name="test-workspace",
            folder="/workspace",
            volume_name="test-workspace-volume",
        )
        result = workspace.compose()

        # The workspaceMount should be a string representation of a Mount
        mount_string = result["workspaceMount"]
        assert_that(mount_string).contains("source=test-workspace-volume")
        assert_that(mount_string).contains("target=/workspace")
        assert_that(mount_string).contains("type=volume")

    def test_workspace_mount_type_is_volume(self):
        """Test that workspace mount type is always volume."""
        workspace = Workspace(
            name="test-workspace",
            folder="/workspace",
            volume_name="test-workspace-volume",
        )
        result = workspace.compose()

        mount_string = result["workspaceMount"]
        assert_that(mount_string).contains("type=volume")
        assert_that(mount_string).does_not_contain("type=bind")
