from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from devcc.main import App
from devcc.models import ContainerImageFeature


def test_image_command_with_valid_name(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "image", "--name", "test_image"], **runner_args)
    assert result.exit_code == 0
    assert "image" in app.context.features
    assert isinstance(app.context.features["image"], ContainerImageFeature)
    assert app.context.features["image"].name == "test_image"


def test_image_command_with_invalid_name(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "image", "--name", ""], **runner_args)
    assert result.exit_code == 2
    assert "Image name must be provided and cannot be empty" in result.output
    assert app.context.features.get("image") is None


def test_image_command_with_valid_tag(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "image", "--name", "test_image:latest"], **runner_args)
    assert result.exit_code == 0
    assert app.context.features["image"].name == "test_image:latest"


def test_image_command_with_valid_repository(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "image", "--name", "myrepo/test_image"], **runner_args)
    assert result.exit_code == 0
    assert app.context.features["image"].name == "myrepo/test_image"


def test_image_command_with_valid_repository_and_tag(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "image", "--name", "myrepo/test_image:latest"], **runner_args)
    assert result.exit_code == 0
    assert app.context.features["image"].name == "myrepo/test_image:latest"


def test_image_command_with_invalid_format(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "image", "--name", "test:image:latest"], **runner_args)
    assert result.exit_code == 2
    assert "Image name format is invalid. Expected format: [repository/]name[:tag]" in result.output
    assert app.context.features.get("image") is None


def test_image_command_with_empty_repository(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "image", "--name", "/test_image"], **runner_args)
    assert result.exit_code == 2
    assert "Repository name must be non-empty" in result.output
    assert app.context.features.get("image") is None


def test_image_command_with_empty_image_name(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "image", "--name", "myrepo/"], **runner_args)
    assert result.exit_code == 2
    assert "Image name must be non-empty" in result.output
    assert app.context.features.get("image") is None


def test_image_command_with_invalid_repository_format(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "image", "--name", "repo1/repo2/test_image"], **runner_args)
    assert result.exit_code == 2
    assert "Image name format is invalid. Expected format: [repository/]name[:tag]" in result.output
    assert app.context.features.get("image") is None


def test_image_command_with_feature_creation_error(app: App, runner: CliRunner, runner_args, monkeypatch):
    def mock_expose_feature(*args, **kwargs):
        raise Exception("Simulated feature creation error")
    
    monkeypatch.setattr("devcc.commands.image.ContainerImageFeature", mock_expose_feature)
    
    result = runner.invoke(app.typer, ["--dry-run", "image", "--name", "repo2/test_image"], **runner_args)
    assert result.exit_code == 1
    assert "Error: Simulated feature creation error" in result.output
    assert app.context.features.get("image") is None 
