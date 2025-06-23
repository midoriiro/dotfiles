import logging
from pathlib import Path

import pytest
import yaml
from ignite.models.config import Configuration
from ignite.models.container import Container, Mount, MountType, Workspace as ContainerWorkspace
from tests.conftest import AssertFile, AssertLogs, Dumper, Runner


def test_minimal_configuration(
    runner: Runner,
    configuration_file: Path,
    minimal_configuration: Configuration,
    user_context: Path,
    configuration_dumper: Dumper,
    assert_logs: AssertLogs,
    assert_file: AssertFile,
):
    configuration_dumper(minimal_configuration, configuration_file)
    result = runner(
        "--configuration", str(configuration_file),
        str(user_context),
    )
    assert result.exit_code == 0
    assert_logs({
        f"Folder '{user_context}/.devcontainer' created.": logging.INFO,
        f"File '{user_context}/.devcontainer/devcontainer.json' saved.": logging.INFO,
        f"File '{user_context}/workspace.code-workspace' saved.": logging.INFO,
    })
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