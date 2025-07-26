import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest
import yaml
from assertpy import assert_that
from click.testing import Result
from typer.testing import CliRunner

from ignite.cli import REPOSITORY_CONTEXT_ENV_VAR
from ignite.logging import BaseMessage
from ignite.main import cli, logger
from ignite.models.config import Configuration
from ignite.models.container import Container, Image
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
from ignite.models.workspace import Workspace as WorkspaceModel
from ignite.resolvers import PathResolver

# pylint: disable=redefined-outer-name

Runner = Callable[[List[str]], Result]
Dumper = Callable[[Configuration, Path], None]
AssertLogs = Callable[[List[BaseMessage]], None]
AssertFile = Callable[[Path, Dict[str, Any]], None]


@pytest.fixture(autouse=True)
def set_logger_level(caplog):
    # Configure the root logger level for tests
    logger.setLevel(logging.INFO)
    caplog.at_level(logging.INFO)


@pytest.fixture(scope="session", autouse=True)
def repository_context():
    os.environ[REPOSITORY_CONTEXT_ENV_VAR] = str(Path("files"))


@pytest.fixture()
def user_context(tmp_path) -> Path:
    path = Path(tmp_path, "user-context")
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture()
def path_resolver(user_context) -> PathResolver:
    return PathResolver(repository_context=Path("files"), user_context=user_context)


@pytest.fixture
def app():
    cli.rich_markup_mode = None
    return cli


@pytest.fixture
def runner_args():
    return {
        "catch_exceptions": False,
    }


@pytest.fixture
def runner(app, runner_args) -> Runner:
    runner = CliRunner()

    def _runner(*args) -> Result:
        return runner.invoke(app, [*args], **runner_args)

    return _runner


@pytest.fixture
def minimal_container_configuration():
    return Container(
        workspace=ContainerWorkspace.model_construct(
            name="test-workspace",
            folder="/workspace",
            volume_name="test-workspace-volume",
        ),
        image=Image.model_construct(
            name="test-image",
        ),
    )


@pytest.fixture
def minimal_workspace_configuration():
    return WorkspaceModel(
        policies=Policies(
            {
                "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
                "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
            }
        ),
        projects=Projects(
            {
                "test-project-1": UserProject(
                    path="tools",
                ),
            }
        ),
    )


@pytest.fixture
def minimal_configuration(
    minimal_container_configuration, minimal_workspace_configuration
):
    return Configuration(
        container=minimal_container_configuration,
        workspace=minimal_workspace_configuration,
    )


@pytest.fixture
def configuration_file(tmp_path):
    """Create temporary JSON source files for testing."""
    file = tmp_path / "configuration.yml"
    return file


@pytest.fixture
def configuration_dumper() -> Dumper:
    """Configuration dumper"""

    def _dumper(configuration: Configuration, file: Path):
        data = configuration.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
        )
        data_yaml = yaml.dump(data)
        file.write_text(data_yaml)

    return _dumper


@pytest.fixture
def assert_logs(caplog: pytest.LogCaptureFixture) -> AssertLogs:
    """Assert that the filesystem logs are printed."""

    def _assert_logs(expected_messages: List[BaseMessage]):
        assert_that(caplog.records).is_length(len(expected_messages))
        for record in caplog.records:
            if not hasattr(record, "type"):
                raise AssertionError(
                    f"Record '{record.message}' does not have a 'type' attribute"
                )
            message = BaseMessage.from_record(record)
            assert_that(expected_messages).contains(message)

    return _assert_logs


@pytest.fixture
def assert_file(user_context: Path) -> AssertFile:
    """Assert that a file exists."""

    def _assert_file_content(content: Dict[str, Any], expected_content: Dict[str, Any]):
        assert_that(content).is_equal_to(expected_content)

    def _assert_file(path: Path, expected_content: Dict[str, Any]):
        path = Path(user_context, path)
        content: Dict[str, Any] = {}
        try:
            content = json.loads(path.read_text())
            _assert_file_content(content, expected_content)
            return
        except json.JSONDecodeError:
            pass
        try:
            content = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
            _assert_file_content(content, expected_content)
        except yaml.YAMLError:
            pass
        raise AssertionError(f"File '{path}' does not match expected content")

    return _assert_file
