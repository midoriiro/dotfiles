import pytest
from typer.testing import CliRunner

from devcc.main import App
from devcc.models import MountType


def test_workspace_command_with_name(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["workspace", "--name", "testworkspace"])
    assert result.exit_code == 0
    assert app.context.features["workspace"].name == "testworkspace"
    assert app.context.features["workspace"].workspaceMount is None

def test_workspace_command_with_volume(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["workspace", "--volume-name", "testvolume"])
    assert result.exit_code == 0
    assert app.context.features["workspace"].name is None
    assert app.context.features["workspace"].workspaceMount.source == "testvolume"
    assert app.context.features["workspace"].workspaceMount.target == "/workspace"
    assert app.context.features["workspace"].workspaceMount.type == MountType.VOLUME
    assert app.context.features["workspace"].workspaceMount.options == "consistency=cached"

def test_workspace_command_with_both(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["workspace", "--name", "testworkspace", "--volume-name", "testvolume"])
    assert result.exit_code == 0
    assert app.context.features["workspace"].name == "testworkspace"
    assert app.context.features["workspace"].workspaceMount.source == "testvolume"
    assert app.context.features["workspace"].workspaceMount.target == "/workspace"
    assert app.context.features["workspace"].workspaceMount.type == MountType.VOLUME
    assert app.context.features["workspace"].workspaceMount.options == "consistency=cached"

# Tests pour les validations de nom
def test_workspace_command_with_empty_name(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["workspace", "--name", ""])
    assert result.exit_code == 2
    assert "Name cannot be empty" in result.output
    assert app.context.features.get("workspace") is None

def test_workspace_command_with_short_name(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["workspace", "--name", "te"])
    assert result.exit_code == 2
    assert "Name must be at least 3 characters long" in result.output
    assert app.context.features.get("workspace") is None

def test_workspace_command_with_non_alphanumeric_name(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["workspace", "--name", "test-workspace"])
    assert result.exit_code == 2
    assert "Name must be alphanumeric" in result.output
    assert app.context.features.get("workspace") is None

# Tests pour les validations de nom de volume
def test_workspace_command_with_empty_volume_name(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["workspace", "--volume-name", ""])
    assert result.exit_code == 2
    assert "Volume name cannot be empty" in result.output
    assert app.context.features.get("workspace") is None

def test_workspace_command_with_short_volume_name(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["workspace", "--volume-name", "vo"])
    assert result.exit_code == 2
    assert "Volume name must be at least 3 characters long" in result.output
    assert app.context.features.get("workspace") is None

def test_workspace_command_with_non_alphanumeric_volume_name(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["workspace", "--volume-name", "test-volume"])
    assert result.exit_code == 2
    assert "Volume name must be alphanumeric" in result.output
    assert app.context.features.get("workspace") is None

def test_workspace_command_with_feature_creation_error(app: App, runner: CliRunner, monkeypatch):
    def mock_workspace_feature(*args, **kwargs):
        raise Exception("Simulated feature creation error")
    
    monkeypatch.setattr("devcc.commands.workspace.WorkspaceFeature", mock_workspace_feature)
    
    result = runner.invoke(app.typer, ["workspace", "--name", "testworkspace"])
    assert result.exit_code == 1
    assert "Error: Simulated feature creation error" in result.output
    assert app.context.features.get("workspace") is None