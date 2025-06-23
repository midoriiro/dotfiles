import logging
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml
from ignite.models.config import Configuration
from ignite.models.container import Container, Mount, MountType, Workspace as ContainerWorkspace
from ignite.logging import BaseMessage, FilesystemMessage, JsonSchemaValidationErrorMessage
from tests.conftest import AssertFile, AssertLogs, Dumper, Runner


def test_valid(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    assert_file: AssertFile,
):
    minimal_configuration.container.workspace = ContainerWorkspace.model_construct(
        name="test-workspace",
        folder="/workspace",
        volume_name="test-workspace-volume",
    )
    configuration_dumper(minimal_configuration, configuration_file)
    result = runner(
        "--configuration", str(configuration_file),
        str(user_context),
    )
    assert result.exit_code == 0
    assert_logs([
        FilesystemMessage.create_folder(Path(user_context, ".devcontainer")),
        FilesystemMessage.save_file(Path(user_context, ".devcontainer", "devcontainer.json")),
        FilesystemMessage.save_file(Path(user_context, "workspace.code-workspace")),
    ])
    assert_file(
        Path(".devcontainer/devcontainer.json"),
        {
            "name": f"{minimal_configuration.container.workspace.name}",
            "workspaceFolder": f"{minimal_configuration.container.workspace.folder}",
            "workspaceMount": f"{str(Mount(
                source=minimal_configuration.container.workspace.volume_name,
                target=minimal_configuration.container.workspace.folder,
                type=MountType.VOLUME
            ))}",
            "image": f"{minimal_configuration.container.image.name}",
        }
    )

def _test_invalid(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    arguments: Dict[str, Any],
    expected_message: List[BaseMessage],
):
    configuration = {
        **minimal_configuration.container.workspace.model_dump(),
        **arguments,
    }
    minimal_configuration.container.workspace = ContainerWorkspace.model_construct(**configuration)
    configuration_dumper(minimal_configuration, configuration_file)
    result = runner(
        "--configuration", str(configuration_file),
        str(user_context),
    )
    assert result.exit_code == 1
    assert_logs(expected_message)

def test_empty_name(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    assert_file: AssertFile,
):
    _test_invalid(
        runner,
        configuration_file,
        minimal_configuration,
        user_context,
        configuration_dumper,
        assert_logs,
        {
            "name": "",
        },
        [
            JsonSchemaValidationErrorMessage.model_construct(
                json_path="$.container.workspace.name",
                error_message="'' is too short",
            ),
        ],
    )

def test_short_name(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    assert_file: AssertFile,
):
    _test_invalid(
        runner,
        configuration_file,
        minimal_configuration,
        user_context,
        configuration_dumper,
        assert_logs,
        {
            "name": "a",
        },
        [
            JsonSchemaValidationErrorMessage.model_construct(
                json_path="$.container.workspace.name",
                error_message="'a' is too short",
            ),
        ],
    )

def test_long_name(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    assert_file: AssertFile,
): 
    _test_invalid(
        runner,
        configuration_file,
        minimal_configuration,
        user_context,
        configuration_dumper,
        assert_logs,
        {
            "name": f"{"a"*100}",
        },
        [
            JsonSchemaValidationErrorMessage.model_construct(
                json_path="$.container.workspace.name",
                error_message=f"'{"a"*100}' is too long",
            ),
        ],
    )


def test_empty_folder(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    assert_file: AssertFile,
):
    _test_invalid(
        runner,
        configuration_file,
        minimal_configuration,
        user_context,
        configuration_dumper,
        assert_logs,
        {
            "folder": "",
        },
        [
            JsonSchemaValidationErrorMessage.model_construct(
                json_path="$.container.workspace.folder",
                error_message="'' is too short",
            ),
        ],
    )


def test_short_folder(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    assert_file: AssertFile,
):
    _test_invalid(
        runner,
        configuration_file,
        minimal_configuration,
        user_context,
        configuration_dumper,
        assert_logs,
        {
            "folder": "a",
        },
        [
            JsonSchemaValidationErrorMessage.model_construct(
                json_path="$.container.workspace.folder",
                error_message="'a' is too short",
            ),
        ],
    )


def test_long_folder(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    assert_file: AssertFile,
):
    _test_invalid(
        runner,
        configuration_file,
        minimal_configuration,
        user_context,
        configuration_dumper,
        assert_logs,
        {
            "folder": f"/{"a"*300}",
        },
        [
            JsonSchemaValidationErrorMessage.model_construct(
                json_path="$.container.workspace.folder",
                error_message=f"'/{"a"*300}' is too long",
            ),
        ],
    )

def test_empty_volume_name(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    assert_file: AssertFile,
):
    _test_invalid(
        runner,
        configuration_file,
        minimal_configuration,
        user_context,
        configuration_dumper,
        assert_logs,
        {
            "volume_name": "",
        },
        [
            JsonSchemaValidationErrorMessage.model_construct(
                json_path="$.container.workspace.volume-name",
                error_message="'' is too short",
            ),
        ],
    )


def test_short_volume_name(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    assert_file: AssertFile,
):
    _test_invalid(
        runner,
        configuration_file,
        minimal_configuration,
        user_context,
        configuration_dumper,
        assert_logs,
        {
            "volume_name": "a",
        },
        [
            JsonSchemaValidationErrorMessage.model_construct(
                json_path="$.container.workspace.volume-name",
                error_message="'a' is too short",
            ),
        ],
    )


def test_long_volume_name(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    assert_file: AssertFile,
):
    _test_invalid(
        runner,
        configuration_file,
        minimal_configuration,
        user_context,
        configuration_dumper,
        assert_logs,
        {
            "volume_name": f"{"a"*100}",
        },
        [
            JsonSchemaValidationErrorMessage.model_construct(
                json_path="$.container.workspace.volume-name",
                error_message=f"'{"a"*100}' is too long",
            ),
        ],
    )