import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml
from assertpy import assert_that
from typer.testing import CliRunner

from ignite.cli import REPOSITORY_CONTEXT_ENV_VAR
from ignite.logging import (
    ComposerMessage,
    ConfigurationFileErrorMessage,
    FilesystemMessage,
    JsonSchemaValidationErrorMessage,
    PydanticValidationErrorMessage,
    PydanticValidationErrorMessageList,
)
from ignite.main import cli
from ignite.models.config import Configuration
from ignite.models.container import Container, Image, Mount, MountType, Runtime
from ignite.models.container import Workspace as ContainerWorkspace
from ignite.models.policies import (
    ContainerBackendPolicy,
    ContainerPolicy,
    FilePolicy,
    FileWritePolicy,
    FolderCreatePolicy,
    FolderPolicy,
    Policies,
)
from ignite.models.projects import Projects, UserProject
from ignite.models.settings import VSCodeFolder
from ignite.models.workspace import Workspace as WorkspaceModel
from tests.conftest import AssertFile, AssertLogs, Dumper, Runner


def test_complete_workflow_with_complex_configuration(
    runner: Runner,
    configuration_file: Path,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    assert_file: AssertFile,
):
    """Test complete workflow with a complex configuration including multiple projects and custom settings."""
    # Create complex configuration
    complex_config = Configuration(
        container=Container(
            workspace=ContainerWorkspace(
                name="complex-workspace",
                folder="/workspace",
                volume_name="complex-workspace-volume",
            ),
            image=Image(
                name="python",
                tag="3.11-slim",
            ),
            runtime=Runtime(
                mounts=[
                    Mount(source="host-data", target="/data", type=MountType.VOLUME)
                ]
            ),
        ),
        workspace=WorkspaceModel(
            policies=Policies(
                {
                    "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
                    "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                    "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
                }
            ),
            projects=Projects(
                {
                    "frontend": UserProject(
                        path="tools",
                        vscode=VSCodeFolder(
                            settings=[
                                "on-save",
                                "coverage-gutters",
                            ]
                        ),
                    ),
                    "backend": UserProject(path="tools"),
                    "shared": UserProject(path="tools"),
                }
            ),
        ),
    )

    configuration_dumper(complex_config, configuration_file)
    result = runner("--configuration", str(configuration_file), str(user_context))

    assert_that(result.exit_code).is_equal_to(0)
    assert_logs(
        [
            FilesystemMessage.create_folder(Path(user_context, ".devcontainer")),
            FilesystemMessage.save_file(
                Path(user_context, ".devcontainer", "devcontainer.json")
            ),
            FilesystemMessage.save_file(Path(user_context, "workspace.code-workspace")),
            FilesystemMessage.create_folder(
                Path(user_context, "tools", "frontend", ".vscode")
            ),
            FilesystemMessage.save_file(
                Path(user_context, "tools", "frontend", ".vscode", "settings.json")
            ),
        ]
    )

    assert_file(
        Path(".devcontainer/devcontainer.json"),
        {
            "name": "complex-workspace",
            "workspaceFolder": "/workspace",
            "workspaceMount": "source=complex-workspace-volume,target=/workspace,type=volume",
            "image": "python:3.11-slim",
            "mounts": ["source=host-data,target=/data,type=volume"],
        },
    )

    # Verify generated workspace file
    assert_file(
        Path("workspace.code-workspace"),
        {
            "folders": [
                {"path": f"{str(Path('tools', 'backend'))}", "name": "backend"},
                {"path": f"{str(Path('tools', 'frontend'))}", "name": "frontend"},
                {"path": f"{str(Path('tools', 'shared'))}", "name": "shared"},
            ],
            "settings": {},
        },
    )


def test_cli_with_invalid_yaml_configuration(
    runner: Runner,
    configuration_file: Path,
    user_context: Path,
    assert_logs: AssertLogs,
):
    """Test CLI behavior with invalid YAML configuration file."""
    configuration_file.write_text("invalid: yaml: content: [")
    result = runner("--configuration", str(configuration_file), str(user_context))
    assert_that(result.exit_code).is_equal_to(1)
    assert_that(result.output).contains("Configuration file is invalid")
    assert_logs(
        [
            ConfigurationFileErrorMessage.model_construct(
                line=0,
                column=13,
                problem="mapping values are not allowed here",
            )
        ]
    )


def test_cli_with_missing_required_fields(
    runner: Runner,
    configuration_file: Path,
    user_context: Path,
    assert_logs: AssertLogs,
):
    """Test CLI behavior with configuration missing required fields."""
    invalid_config = {
        "container": {
            "workspace": {
                "name": "test"
                # Missing required fields
            }
        },
        "workspace": {
            "policies": {"container": {"backend": "docker"}},
            "projects": {"frontend": {"path": "/workspace/frontend"}},
        },
    }
    configuration_file.write_text(yaml.dump(invalid_config))
    result = runner("--configuration", str(configuration_file), str(user_context))
    assert_that(result.exit_code).is_equal_to(1)
    assert_that(result.output).contains("Configuration file is invalid")
    assert_logs(
        [
            JsonSchemaValidationErrorMessage.model_construct(
                json_path="$.container.workspace",
                error_message="'folder' is a required property",
            )
        ]
    )


def test_cli_with_validation_error(
    runner: Runner,
    configuration_file: Path,
    user_context: Path,
    assert_logs: AssertLogs,
):
    """Test CLI behavior with configuration validation error."""
    invalid_config = {
        "container": {
            "workspace": {
                "name": "test",
                "folder": "/workspace",
                "volume-name": "test-volume",
            },
            "runtime": {"user": {"remote": "non-root", "container": "non-root"}},
        },
        "workspace": {
            "policies": {
                "container": {"backend": "docker"},
                "folder": {"create": "ask"},
                "file": {"write": "ask"},
            },
            "projects": {"frontend": {"path": "/workspace/frontend"}},
        },
    }
    configuration_file.write_text(yaml.dump(invalid_config))
    result = runner("--configuration", str(configuration_file), str(user_context))
    assert_that(result.exit_code).is_equal_to(1)
    assert_that(result.output).contains("Configuration file is invalid")
    assert_logs(
        [
            PydanticValidationErrorMessageList.model_construct(
                errors=[
                    PydanticValidationErrorMessage.model_construct(
                        location="container.runtime.user.constrained-str",
                        error_type="string_type",
                        error_message="Input should be a valid string",
                        input={"container": "non-root", "remote": "non-root"},
                    ),
                    PydanticValidationErrorMessage.model_construct(
                        location="container.runtime.user.function-after[check_users(), Users]",
                        error_type="value_error",
                        error_message="Value error, Remote and container users cannot be the same.",
                        input={"container": "non-root", "remote": "non-root"},
                    ),
                ]
            )
        ]
    )


def test_cli_with_composer_error(
    runner: Runner,
    configuration_file: Path,
    user_context: Path,
    assert_logs: AssertLogs,
):
    """Test CLI behavior with composer error."""
    valid_config = {
        "container": {
            "workspace": {
                "name": "test",
                "folder": "/workspace",
                "volume-name": "test-volume",
            },
            "image": {"name": "python", "tag": "3.11-slim"},
        },
        "workspace": {
            "policies": {
                "container": {"backend": "docker"},
                "folder": {"create": "never"},
                "file": {"write": "never"},
            },
            "projects": {"frontend": {"path": "/workspace/frontend"}},
        },
    }
    configuration_file.write_text(yaml.dump(valid_config))
    workspace_file = Path(user_context, "workspace.code-workspace")
    workspace_file.touch()
    result = runner("--configuration", str(configuration_file), str(user_context))
    assert_that(result.exit_code).is_equal_to(1)
    assert_that(result.output).contains("Composer failed")
    assert_logs(
        [
            ComposerMessage.model_construct(
                composer_type="ContainerComposer",
                error_type="ValueError",
                error_message=f"Folder '{str(Path(user_context, '.devcontainer'))}' does not exist and policy is set to never.",
            ),
            ComposerMessage.model_construct(
                composer_type="WorkspaceComposer",
                error_type="ValueError",
                error_message=f"File '{str(Path(user_context, 'workspace.code-workspace'))}' already exists and policy is set to never.",
            ),
        ]
    )


def test_cli_with_missing_environment_variables(
    runner: Runner,
    configuration_file: Path,
    user_context: Path,
    minimal_configuration: Configuration,
    configuration_dumper: Dumper,
):
    """Test CLI behavior when REPOSITORY_CONTEXT environment variable is not set."""
    # Temporarily unset the environment variable
    original_value = os.environ.get(REPOSITORY_CONTEXT_ENV_VAR)
    if REPOSITORY_CONTEXT_ENV_VAR in os.environ:
        del os.environ[REPOSITORY_CONTEXT_ENV_VAR]

    try:
        configuration_dumper(minimal_configuration, configuration_file)
        result = runner("--configuration", str(configuration_file), str(user_context))
        assert_that(result.exit_code).is_equal_to(0)
    finally:
        # Restore the environment variable
        if original_value is not None:
            os.environ[REPOSITORY_CONTEXT_ENV_VAR] = original_value


def test_cli_with_nonexistent_configuration_file(
    runner: Runner,
    user_context: Path,
):
    """Test CLI behavior with non-existent configuration file."""
    nonexistent_file = Path("nonexistent", "workspace.yml")
    result = runner("--configuration", str(nonexistent_file), str(user_context))
    assert_that(result.exit_code).is_equal_to(2)
    assert_that(result.output).contains(f"Error: Invalid value for '--configuration'")


def test_cli_with_nonexistent_context_directory(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    configuration_dumper: Dumper,
):
    """Test CLI behavior with non-existent context directory."""
    configuration_dumper(minimal_configuration, configuration_file)
    nonexistent_context = Path("nonexistent", "context")
    result = runner(
        "--configuration", str(configuration_file), str(nonexistent_context)
    )
    assert_that(result.exit_code).is_equal_to(2)
    assert_that(result.output).contains(f"Error: Invalid value for '[CONTEXT]'")


def test_cli_help_output(runner: Runner):
    """Test CLI help output."""
    result = runner("--help")
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains(
        "Development workspace environment management CLI tool"
    )
    assert_that(result.output).contains("--configuration")
    assert_that(result.output).contains("Path to the configuration file")


def test_cli_no_args_help(runner: Runner):
    """Test CLI behavior when no arguments are provided."""
    result = runner()
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains(
        "Development workspace environment management CLI tool"
    )
    assert_that(result.output).contains("--configuration")
    assert_that(result.output).contains("Path to the configuration file")
