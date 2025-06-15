import pytest
from typer.testing import CliRunner

from devcc.main import App
from devcc.models import Env, MountPoint, MountType, RuntimeFeature


def test_runtime_command_with_remote_user(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "runtime", "--user", "remote:testuser"], **runner_args)
    assert result.exit_code == 0
    assert app.context.features["runtime"].remoteUser == "testuser"
    assert app.context.features["runtime"].containerUser is None

def test_runtime_command_with_container_user(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "runtime", "--user", "container:testuser"], **runner_args)
    assert result.exit_code == 0
    assert app.context.features["runtime"].containerUser == "testuser"
    assert app.context.features["runtime"].remoteUser is None

def test_runtime_command_with_container_env(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "runtime", "--env", "container:TEST_KEY=test_value"], **runner_args)
    assert result.exit_code == 0
    assert len(app.context.features["runtime"].containerEnv) == 1
    assert app.context.features["runtime"].containerEnv[0].key == "TEST_KEY"
    assert app.context.features["runtime"].containerEnv[0].value == "test_value"

def test_runtime_command_with_remote_env(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "runtime", "--env", "remote:TEST_KEY=test_value"], **runner_args)
    assert result.exit_code == 0
    assert len(app.context.features["runtime"].remoteEnv) == 1
    assert app.context.features["runtime"].remoteEnv[0].key == "TEST_KEY"
    assert app.context.features["runtime"].remoteEnv[0].value == "test_value"

def test_runtime_command_with_mount(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "runtime", "--mounts", "/host/path:/container/path:bind"], **runner_args)
    assert result.exit_code == 0
    assert len(app.context.features["runtime"].mounts) == 1
    assert app.context.features["runtime"].mounts[0].source == "/host/path"
    assert app.context.features["runtime"].mounts[0].target == "/container/path"
    assert app.context.features["runtime"].mounts[0].type == MountType.BIND

def test_runtime_command_with_mount_options(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["--dry-run", "runtime", "--mounts", "/host/path:/container/path:bind:ro"])
    assert result.exit_code == 0
    assert len(app.context.features["runtime"].mounts) == 1
    assert app.context.features["runtime"].mounts[0].options == "ro"

def test_runtime_command_with_volume_mount(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["--dry-run", "runtime", "--mounts", "volume_name:/container/path:volume"], **runner_args)
    assert result.exit_code == 0
    assert len(app.context.features["runtime"].mounts) == 1
    assert app.context.features["runtime"].mounts[0].source == "volume_name"
    assert app.context.features["runtime"].mounts[0].type == MountType.VOLUME

def test_runtime_command_with_invalid_user_format(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["runtime", "--user", "invalid_format"], **runner_args)
    assert result.exit_code == 2
    assert "User must be in format 'container:user' or 'remote:user'" in result.output

def test_runtime_command_with_invalid_user_type(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["runtime", "--user", "invalid:testuser"], **runner_args)
    assert result.exit_code == 2
    assert "User must be in format 'container:user' or 'remote:user'" in result.output

def test_runtime_command_with_empty_user(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["runtime", "--user", "remote:"], **runner_args)
    assert result.exit_code == 2
    assert "User cannot be empty" in result.output

def test_runtime_command_with_short_user(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["runtime", "--user", "remote:ab"], **runner_args)
    assert result.exit_code == 2
    assert "User must be at least 3 characters long" in result.output

def test_runtime_command_with_root_user(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["runtime", "--user", "remote:root"])
    assert result.exit_code == 2
    assert "User cannot be 'root'" in result.output

def test_runtime_command_with_digit_start_user(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["runtime", "--user", "remote:1user"])
    assert result.exit_code == 2
    assert "User cannot start with a digit" in result.output

def test_runtime_command_with_non_alphanumeric_user(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["runtime", "--user", "remote:user-name"], **runner_args)
    assert result.exit_code == 2
    assert "User must be alphanumeric" in result.output

def test_runtime_command_with_invalid_env_format(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["runtime", "--env", "invalid_format"], **runner_args)
    assert result.exit_code == 2
    assert "must be in 'container:key=value' or 'remote:key=value' format" in result.output

def test_runtime_command_with_invalid_env_type(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["runtime", "--env", "invalid:key=value"], **runner_args)
    assert result.exit_code == 2
    assert "must be in 'container:key=value' or 'remote:key=value' format" in result.output

def test_runtime_command_with_empty_env(app: App, runner: CliRunner, runner_args):
    result = runner.invoke(app.typer, ["runtime", "--env", " "], **runner_args)
    assert result.exit_code == 2
    assert "Environment variable string cannot be empty" in result.output

def test_runtime_command_with_env_no_equals(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["runtime", "--env", "container:keyvalue"])
    assert result.exit_code == 2
    assert "must be in key=value format" in result.output

def test_runtime_command_with_empty_env_key(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["runtime", "--env", "container:=value"])
    assert result.exit_code == 2
    assert "Environment variable key cannot be empty" in result.output

def test_runtime_command_with_empty_env_value(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["runtime", "--env", "container:key="])
    assert result.exit_code == 2
    assert "Environment variable value cannot be empty" in result.output

def test_runtime_command_with_invalid_mount_format(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["runtime", "--mounts", "invalid_format"])
    assert result.exit_code == 2
    assert "must be in source:target:type[:options] format" in result.output

def test_runtime_command_with_invalid_mount_type(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["runtime", "--mounts", "/host/path:/container/path:invalid"])
    assert result.exit_code == 2
    assert f"Mount type must be one of: {MountType.BIND.value}, {MountType.VOLUME.value}" in result.output

def test_runtime_command_with_empty_mount(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["runtime", "--mounts", " "])
    assert result.exit_code == 2
    assert "Mount point string cannot be empty" in result.output

def test_runtime_command_with_empty_mount_source(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["runtime", "--mounts", ":/container/path:bind"])
    assert result.exit_code == 2
    assert "Source, target, and type cannot be empty" in result.output

def test_runtime_command_with_empty_mount_target(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["runtime", "--mounts", "/host/path::bind"])
    assert result.exit_code == 2
    assert "Source, target, and type cannot be empty" in result.output

def test_runtime_command_with_empty_mount_type(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["runtime", "--mounts", "/host/path:/container/path:"])
    assert result.exit_code == 2
    assert "Source, target, and type cannot be empty" in result.output

def test_runtime_command_with_empty_mount_options(app: App, runner: CliRunner):
    result = runner.invoke(app.typer, ["runtime", "--mounts", "/host/path:/container/path:bind:"])
    assert result.exit_code == 2
    assert "Options cannot be empty if provided" in result.output

def test_runtime_command_with_feature_creation_error(app: App, runner: CliRunner, runner_args, monkeypatch):
    def mock_runtime_feature(*args, **kwargs):
        raise Exception("Simulated feature creation error")
    
    monkeypatch.setattr("devcc.commands.runtime.RuntimeFeature", mock_runtime_feature)
    
    result = runner.invoke(app.typer, ["runtime", "--user", "remote:testuser"], **runner_args)
    assert result.exit_code == 1
    assert "Error: Simulated feature creation error" in result.output
    assert app.context.features.get("runtime") is None