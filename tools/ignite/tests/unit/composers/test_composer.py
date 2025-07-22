import logging
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
from assertpy import assert_that
from typer.testing import CliRunner

from ignite.composers import Composer
from ignite.logging import FilesystemMessage
from ignite.models.policies import FileWritePolicy, FolderCreatePolicy, Policies


class TestComposerInit:
    """Test class for Composer initialization and basic methods."""

    def test_init(self):
        """Test composer initialization."""
        composer = Composer()
        assert_that(composer.logger).is_not_none()
        assert_that(composer.logger.name).is_equal_to("Composer")
        assert_that(composer.logger.propagate).is_true()

    def test_compose_method(self):
        """Test the compose method returns None by default."""
        composer = Composer()
        result = composer.compose()
        assert_that(result).is_none()

    def test_save_method_raises_not_implemented(self):
        """Test that save method raises NotImplementedError."""
        composer = Composer()
        output_path = Path("/tmp/test")
        policies = Policies.model_construct(root={})

        assert_that(composer.save).raises(NotImplementedError).when_called_with(
            output_path, policies
        ).is_equal_to("Subclass must implement this method.")


class TestComposerUserInteraction:
    """Test class for Composer user interaction methods."""

    @patch("typer.confirm")
    def test_ask_create_folder_returns_user_choice(self, mock_confirm):
        """Test _ask_create_folder returns user choice."""
        composer = Composer()
        output_path = Path("/tmp/test")

        # Test when user confirms
        mock_confirm.return_value = True
        result = composer._ask_create_folder(output_path)
        assert_that(result).is_true()
        mock_confirm.assert_called_once_with(
            f"Folder '{output_path}' does not exist. Do you want to create it?"
        )

        # Test when user declines
        mock_confirm.return_value = False
        result = composer._ask_create_folder(output_path)
        assert_that(result).is_false()

    @patch("typer.confirm")
    def test_ask_overwrite_file_returns_user_choice(self, mock_confirm):
        """Test _ask_overwrite_file returns user choice."""
        composer = Composer()
        output_path = Path("/tmp/test")

        # Test when user confirms
        mock_confirm.return_value = True
        result = composer._ask_overwrite_file(output_path)
        assert_that(result).is_true()
        mock_confirm.assert_called_once_with(
            f"File '{output_path}' already exists. Do you want to overwrite it?"
        )

        # Test when user declines
        mock_confirm.return_value = False
        result = composer._ask_overwrite_file(output_path)
        assert_that(result).is_false()


class TestComposerSaveFile:
    """Test class for Composer _save_file method."""

    def test_save_file_raises_error_for_directory_path(self, tmp_path):
        """Test _save_file raises ValueError when output_path is a directory."""
        composer = Composer()
        dir_path = tmp_path / "test_dir"
        dir_path.mkdir()

        assert_that(composer._save_file).raises(ValueError).when_called_with(
            dir_path, "test content"
        ).is_equal_to(f"Path '{dir_path}' is a directory.")

    def test_save_file_saves_content_when_file_does_not_exist(self, tmp_path, caplog):
        """Test _save_file saves content when file does not exist."""
        composer = Composer()
        output_path = tmp_path / "test.txt"

        composer._save_file(output_path, "test content")

        # Check that file save message was logged
        assert_that(
            any(
                "File '{}' saved.".format(output_path) in record.message
                for record in caplog.records
            )
        ).is_true()

        # Verify content was saved
        assert_that(output_path.read_text()).is_equal_to("test content")

    def test_save_file_creates_parent_directories_when_they_dont_exist(
        self, tmp_path, caplog
    ):
        """Test _save_file creates parent directories when they don't exist."""
        composer = Composer()
        output_path = tmp_path / "parent" / "child" / "test.txt"

        composer._save_file(
            output_path, "test content", folder_policy=FolderCreatePolicy.ALWAYS
        )

        # Verify parent directories were created
        assert_that(output_path.parent.exists()).is_true()
        assert_that(output_path.parent.parent.exists()).is_true()

        # Verify content was saved
        assert_that(output_path.read_text()).is_equal_to("test content")

        # Check that folder creation message was logged
        assert_that(
            any(
                "Folder '{}' created.".format(output_path.parent) in record.message
                for record in caplog.records
            )
        ).is_true()


class TestComposerFolderPolicies:
    """Test class for Composer _save_file method with different folder policies."""

    @patch("typer.confirm")
    def test_ask_policy_when_user_confirms_folder_creation(
        self, mock_confirm, tmp_path, caplog
    ):
        """Test _save_file asks for folder creation when policy is ASK."""
        composer = Composer()
        output_path = tmp_path / "nonexistent" / "test.txt"

        # User confirms folder creation
        mock_confirm.return_value = True

        with patch("builtins.open", mock_open()) as mock_file:
            composer._save_file(output_path, "test content")

        mock_confirm.assert_called_once_with(
            "Folder '{}' does not exist. Do you want to create it?".format(
                output_path.parent
            )
        )
        mock_file.assert_called_once_with(output_path, "w")
        mock_file().write.assert_called_once_with("test content")

        # Check that folder creation message was logged
        assert_that(
            any(
                "Folder '{}' created.".format(output_path.parent) in record.message
                for record in caplog.records
            )
        ).is_true()

    @patch("typer.confirm")
    def test_ask_policy_when_user_declines_folder_creation(
        self, mock_confirm, tmp_path, caplog
    ):
        """Test _save_file skips folder creation when user declines."""
        composer = Composer()
        output_path = tmp_path / "nonexistent" / "test.txt"

        # User declines folder creation
        mock_confirm.return_value = False

        composer._save_file(output_path, "test content")

        mock_confirm.assert_called_once_with(
            "Folder '{}' does not exist. Do you want to create it?".format(
                output_path.parent
            )
        )

        # Check that folder skip message was logged
        assert_that(
            any(
                "Folder '{}' creation skipped.".format(output_path.parent)
                in record.message
                for record in caplog.records
            )
        ).is_true()

        # Verify file was not created
        assert_that(output_path.exists()).is_false()

    def test_always_policy_when_folder_does_not_exist(self, tmp_path, caplog):
        """Test _save_file always creates folder when policy is ALWAYS."""
        composer = Composer()
        output_path = tmp_path / "nonexistent" / "test.txt"

        with patch("builtins.open", mock_open()) as mock_file:
            composer._save_file(
                output_path, "test content", folder_policy=FolderCreatePolicy.ALWAYS
            )

        mock_file.assert_called_once_with(output_path, "w")
        mock_file().write.assert_called_once_with("test content")

        # Check that folder creation message was logged
        assert_that(
            any(
                "Folder '{}' created.".format(output_path.parent) in record.message
                for record in caplog.records
            )
        ).is_true()

    def test_never_policy_when_folder_does_not_exist(self, tmp_path):
        """Test _save_file raises error when policy is NEVER and folder doesn't exist."""
        composer = Composer()
        output_path = tmp_path / "nonexistent" / "test.txt"

        assert_that(composer._save_file).raises(ValueError).when_called_with(
            output_path, "test content", folder_policy=FolderCreatePolicy.NEVER
        ).is_equal_to(
            f"Folder '{output_path.parent}' does not exist and policy is set to never."
        )

    def test_unsupported_folder_policy(self, tmp_path):
        """Test _save_file raises error for unsupported folder policy."""
        composer = Composer()
        output_path = tmp_path / "folder" / "test.txt"

        assert_that(composer._save_file).raises(ValueError).when_called_with(
            output_path, "test content", folder_policy="invalid_policy"
        ).is_equal_to("Unsupported folder create policy: invalid_policy.")


class TestComposerFilePolicies:
    """Test class for Composer _save_file method with different file policies."""

    @patch("typer.confirm")
    def test_ask_policy_when_user_confirms_overwrite(
        self, mock_confirm, tmp_path, caplog
    ):
        """Test _save_file asks for overwrite when file exists and policy is ASK."""
        composer = Composer()
        output_path = tmp_path / "test.txt"
        output_path.write_text("existing content")

        # User confirms overwrite
        mock_confirm.return_value = True

        with patch("builtins.open", mock_open()) as mock_file:
            composer._save_file(output_path, "new content")

        mock_confirm.assert_called_once_with(
            "File '{}' already exists. Do you want to overwrite it?".format(output_path)
        )
        mock_file.assert_called_once_with(output_path, "w")
        mock_file().write.assert_called_once_with("new content")

    @patch("typer.confirm")
    def test_ask_policy_when_user_declines_overwrite(
        self, mock_confirm, tmp_path, caplog
    ):
        """Test _save_file skips file when user declines overwrite."""
        composer = Composer()
        output_path = tmp_path / "test.txt"
        output_path.write_text("existing content")

        # User declines overwrite
        mock_confirm.return_value = False

        composer._save_file(output_path, "new content")

        mock_confirm.assert_called_once_with(
            "File '{}' already exists. Do you want to overwrite it?".format(output_path)
        )

        # Check that file skip message was logged
        assert_that(
            any(
                "File '{}' skipped.".format(output_path) in record.message
                for record in caplog.records
            )
        ).is_true()

        # Verify original content is preserved
        assert_that(output_path.read_text()).is_equal_to("existing content")

    def test_skip_policy_when_file_exists(self, tmp_path, caplog):
        """Test _save_file skips file when policy is SKIP and file exists."""
        composer = Composer()
        output_path = tmp_path / "test.txt"
        output_path.write_text("existing content")

        composer._save_file(
            output_path, "new content", file_policy=FileWritePolicy.SKIP
        )

        # Check that file skip message was logged
        assert_that(
            any(
                "File '{}' skipped.".format(output_path) in record.message
                for record in caplog.records
            )
        ).is_true()

        # Verify original content is preserved
        assert_that(output_path.read_text()).is_equal_to("existing content")

    def test_overwrite_policy_when_file_exists(self, tmp_path, caplog):
        """Test _save_file overwrites file when policy is OVERWRITE and file exists."""
        composer = Composer()
        output_path = tmp_path / "test.txt"
        output_path.write_text("existing content")

        composer._save_file(
            output_path, "new content", file_policy=FileWritePolicy.OVERWRITE
        )

        # Check that file overwrite message was logged
        assert_that(
            any(
                "File '{}' will be overwritten.".format(output_path) in record.message
                for record in caplog.records
            )
        ).is_true()

        # Verify content was overwritten
        assert_that(output_path.read_text()).is_equal_to("new content")

    def test_never_policy_when_file_exists(self, tmp_path, caplog):
        """Test _save_file raises error when policy is NEVER and file exists."""
        composer = Composer()
        output_path = tmp_path / "test.txt"
        output_path.write_text("existing content")

        assert_that(composer._save_file).raises(ValueError).when_called_with(
            output_path, "new content", file_policy=FileWritePolicy.NEVER
        ).is_equal_to(
            f"File '{output_path}' already exists and policy is set to never."
        )

    def test_unsupported_file_policy(self, tmp_path):
        """Test _save_file raises error for unsupported file policy."""
        composer = Composer()
        output_path = tmp_path / "test.txt"
        output_path.write_text("existing content")

        assert_that(composer._save_file).raises(ValueError).when_called_with(
            output_path, "test content", file_policy="invalid_policy"
        ).is_equal_to("Unsupported file write policy: invalid_policy.")
