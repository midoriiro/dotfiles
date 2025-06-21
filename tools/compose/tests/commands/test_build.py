from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from compose.main import App
from compose.models import ContainerBuildFeature


def test_build_command_with_all_parameters(app: App, runner: CliRunner, runner_args, tmp_path_factory):
    """Test build command with all parameters provided."""
    container_file = tmp_path_factory.mktemp("container_file")
    context_file = tmp_path_factory.mktemp("context_file")
    
    result = runner.invoke(
        app.typer,
        ["--dry-run", "build", "--container-file", str(container_file), "--context", str(context_file), "--target", "build-stage"],
        **runner_args
    )
    assert result.exit_code == 0
    assert "build" in app.context.features
    assert isinstance(app.context.features["build"], ContainerBuildFeature)
    assert app.context.features["build"].container_file == str(container_file)
    assert app.context.features["build"].context == str(context_file)
    assert app.context.features["build"].target == "build-stage"


def test_build_command_with_no_parameters(app: App, runner: CliRunner, runner_args):
    """Test build command with no parameters provided."""
    result = runner.invoke(app.typer, ["--dry-run", "build"], **runner_args)
    assert result.exit_code == 2
    assert "Container file path must be provided" in result.output
    assert app.context.features.get("container") is None


def test_build_command_with_partial_parameters(app: App, runner: CliRunner, runner_args, tmp_path_factory):
    """Test build command with only some parameters provided."""
    container_file = tmp_path_factory.mktemp("container_file")
    
    result = runner.invoke(
        app.typer,
        ["--dry-run", "build", "--container-file", str(container_file)],
        **runner_args
    )
    assert result.exit_code == 0
    assert "build" in app.context.features
    assert isinstance(app.context.features["build"], ContainerBuildFeature)
    assert app.context.features["build"].container_file == str(container_file)
    assert app.context.features["build"].context is None
    assert app.context.features["build"].target is None


def test_build_command_with_empty_container_file(app: App, runner: CliRunner, runner_args):
    """Test build command with empty container file path."""
    result = runner.invoke(
        app.typer,
        ["--dry-run", "build", "--container-file", ""],
        **runner_args
    )
    assert result.exit_code == 2
    assert "Container file path must be provided" in result.output
    assert app.context.features.get("container") is None


def test_build_command_with_nonexistent_container_file(app: App, runner: CliRunner, runner_args):
    """Test build command with nonexistent container file path."""
    with patch('pathlib.Path.exists', return_value=False):
        result = runner.invoke(
            app.typer,
            ["--dry-run", "build", "--container-file", "/nonexistent/path"],
            **runner_args
        )
        assert result.exit_code == 2
        assert "Container file does not exist" in result.output
        assert app.context.features.get("container") is None


def test_build_command_with_empty_context(app: App, runner: CliRunner, runner_args, tmp_path_factory):
    """Test build command with empty context path."""
    container_file = tmp_path_factory.mktemp("container_file")
    
    result = runner.invoke(
        app.typer,
        ["--dry-run", "build", "--container-file", str(container_file), "--context", " "],
        **runner_args
    )
    assert result.exit_code == 2
    assert "Build context path must be provided" in result.output
    assert app.context.features.get("container") is None


def test_build_command_with_nonexistent_context(app: App, runner: CliRunner, runner_args):
    """Test build command with nonexistent context path."""
    with patch('pathlib.Path.exists', return_value=False):
        result = runner.invoke(
            app.typer,
            ["--dry-run", "build", "--context", "/nonexistent/path"],
            **runner_args
        )
        assert result.exit_code == 2
        assert "Build context does not exist" in result.output
        assert app.context.features.get("container") is None


def test_build_command_with_empty_target(app: App, runner: CliRunner, runner_args, tmp_path_factory):
    """Test build command with empty target build stage."""
    container_file = tmp_path_factory.mktemp("container_file")
    
    result = runner.invoke(
        app.typer,
        ["--dry-run", "build", "--container-file", str(container_file), "--target", " "],
        **runner_args
    )
    assert result.exit_code == 2
    assert "Target build stage cannot be empty" in result.output
    assert app.context.features.get("container") is None


def test_build_command_with_feature_creation_error(app: App, runner: CliRunner, runner_args, monkeypatch, tmp_path_factory):
    """Test build command with feature creation error."""
    def mock_build_feature(*args, **kwargs):
        raise Exception("Simulated feature creation error")
    
    monkeypatch.setattr("compose.commands.build.ContainerBuildFeature", mock_build_feature)

    container_file = tmp_path_factory.mktemp("container_file")
    
    result = runner.invoke(
        app.typer,
        ["--dry-run", "build", "--container-file", str(container_file)],
        **runner_args
    )
    assert result.exit_code == 1
    assert "Error: Simulated feature creation error" in result.output
    assert app.context.features.get("container") is None 