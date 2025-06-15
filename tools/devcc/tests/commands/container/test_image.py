from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from devcc.main import App
from devcc.models import ContainerFeature, ContainerImageFeature


def test_image_command_with_valid_name(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "container", "image", "--name", "test_image"], **runner_args)
    assert result.exit_code == 0
    assert "container" in app.context.features
    assert isinstance(app.context.features["container"], ContainerFeature)
    assert isinstance(app.context.features["container"].image, ContainerImageFeature)
    assert app.context.features["container"].image.name == "test_image"


def test_image_command_with_invalid_name(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "container", "image", "--name", ""], **runner_args)
    assert result.exit_code == 2
    assert "Image name must be provided and cannot be empty" in result.output
    assert app.context.features.get("container") is None


def test_image_command_with_valid_tag(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "container", "image", "--name", "test_image:latest"], **runner_args)
    assert result.exit_code == 0
    assert app.context.features["container"].image.name == "test_image:latest"


def test_image_command_with_valid_repository(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "container", "image", "--name", "myrepo/test_image"], **runner_args)
    assert result.exit_code == 0
    assert app.context.features["container"].image.name == "myrepo/test_image"


def test_image_command_with_valid_repository_and_tag(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "container", "image", "--name", "myrepo/test_image:latest"], **runner_args)
    assert result.exit_code == 0
    assert app.context.features["container"].image.name == "myrepo/test_image:latest"


def test_image_command_with_invalid_format(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "container", "image", "--name", "test:image:latest"], **runner_args)
    assert result.exit_code == 2
    assert "Image name format is invalid. Expected format: [repository/]name[:tag]" in result.output
    assert app.context.features.get("container") is None


def test_image_command_with_empty_repository(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "container", "image", "--name", "/test_image"], **runner_args)
    assert result.exit_code == 2
    assert "Repository name must be non-empty" in result.output
    assert app.context.features.get("container") is None


def test_image_command_with_empty_image_name(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "container", "image", "--name", "myrepo/"], **runner_args)
    assert result.exit_code == 2
    assert "Image name must be non-empty" in result.output
    assert app.context.features.get("container") is None


def test_image_command_with_invalid_repository_format(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "container", "image", "--name", "repo1/repo2/test_image"], **runner_args)
    assert result.exit_code == 2
    assert "Image name format is invalid. Expected format: [repository/]name[:tag]" in result.output
    assert app.context.features.get("container") is None


def test_image_command_with_feature_creation_error(app: App, runner: CliRunner, runner_args, monkeypatch):
    def mock_expose_feature(*args, **kwargs):
        raise Exception("Simulated feature creation error")
    
    monkeypatch.setattr("devcc.commands.container.image.ContainerImageFeature", mock_expose_feature)
    
    result = runner.invoke(app.typer, ["--dry-run", "container", "image", "--name", "repo2/test_image"], **runner_args)
    assert result.exit_code == 1
    assert "Error: Simulated feature creation error" in result.output
    assert app.context.features.get("expose") is None 
