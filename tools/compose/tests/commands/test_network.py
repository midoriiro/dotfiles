from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from compose.main import App
from compose.models import ContainerNetworkFeature


def test_network_command_with_valid_name(app: App, runner: CliRunner, runner_args):
    """Test network command with a valid network name."""
    result = runner.invoke(app.typer, ["--dry-run", "network", "--name", "test_network"], **runner_args)
    assert result.exit_code == 0
    assert "network" in app.context.features
    assert isinstance(app.context.features["network"], ContainerNetworkFeature)
    assert app.context.features["network"].name == "test_network"


def test_network_command_with_invalid_name(app: App, runner: CliRunner, runner_args):
    """Test network command with an invalid network name."""
    result = runner.invoke(app.typer, ["--dry-run", "network", "--name", ""], **runner_args)
    assert result.exit_code == 2
    assert "Network name must be provided and cannot be empty" in result.output
    assert app.context.features.get("network") is None


def test_network_command_with_whitespace_name(app: App, runner: CliRunner, runner_args):
    """Test network command with a whitespace-only network name."""
    result = runner.invoke(app.typer, ["--dry-run", "network", "--name", "   "], **runner_args)
    assert result.exit_code == 2
    assert "Network name must be provided and cannot be empty" in result.output
    assert app.context.features.get("network") is None


def test_network_command_with_feature_creation_error(app: App, runner: CliRunner, runner_args, monkeypatch):
    """Test network command with feature creation error."""
    def mock_network_feature(*args, **kwargs):
        raise Exception("Simulated feature creation error")
    
    monkeypatch.setattr("compose.commands.network.ContainerNetworkFeature", mock_network_feature)
    
    result = runner.invoke(app.typer, ["--dry-run", "network", "--name", "test_network"], **runner_args)
    assert result.exit_code == 1
    assert "Error: Simulated feature creation error" in result.output
    assert app.context.features.get("network") is None 