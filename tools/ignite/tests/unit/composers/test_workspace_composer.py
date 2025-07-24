import json
import pathlib
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from assertpy import assert_that

from ignite.composers import WorkspaceComposer
from ignite.models.fs import (
    File,
    Folder,
    ResolvedFile,
)
from ignite.models.policies import (
    ContainerBackendPolicy,
    ContainerPolicy,
    FilePolicy,
    FileWritePolicy,
    FolderCreatePolicy,
    FolderPolicy,
    Policies,
    ReservedPolicyKeys,
)
from ignite.models.projects import (
    Projects,
    RepositoryProject,
    ReservedProjectKey,
    UserProject,
)
from ignite.models.settings import VSCodeFolder
from ignite.models.variables import StringVariable, Variables
from ignite.models.workspace import Workspace as WorkspaceModel
from ignite.resolvers import PathResolver


class TestWorkspaceComposerInitialization:
    """Test WorkspaceComposer initialization and basic properties."""

    def test_workspace_composer_initialization(self, minimal_workspace_configuration):
        """Test that WorkspaceComposer initializes correctly with a workspace and path resolver."""
        path_resolver = Mock(spec=PathResolver)
        composer = WorkspaceComposer(minimal_workspace_configuration, path_resolver)

        assert_that(composer).is_not_none()
        assert_that(composer._WorkspaceComposer__workspace).is_equal_to(
            minimal_workspace_configuration
        )
        assert_that(composer._WorkspaceComposer__path_resolver).is_equal_to(
            path_resolver
        )
        assert_that(composer._WorkspaceComposer__resolved_files).is_none()

    def test_inherits_from_composer(self, minimal_workspace_configuration):
        """Test that WorkspaceComposer inherits from Composer base class."""
        path_resolver = Mock(spec=PathResolver)
        composer = WorkspaceComposer(minimal_workspace_configuration, path_resolver)

        assert_that(composer).is_instance_of(WorkspaceComposer)
        assert_that(hasattr(composer, "logger")).is_true()
        assert_that(hasattr(composer, "compose")).is_true()
        assert_that(hasattr(composer, "save")).is_true()


class TestWorkspaceComposerCompose:
    """Test WorkspaceComposer compose functionality."""

    def test_compose_with_minimal_workspace(self, minimal_workspace_configuration):
        """Test composing a minimal workspace configuration."""
        path_resolver = Mock(spec=PathResolver)
        path_resolver.user_context = Path(".")
        path_resolver.resolve.return_value = []

        composer = WorkspaceComposer(minimal_workspace_configuration, path_resolver)
        composer.compose()

        assert_that(composer._WorkspaceComposer__resolved_files).is_not_none()
        assert_that(composer._WorkspaceComposer__resolved_files).is_length(1)

        # Check that the first file is the workspace specification
        workspace_file = composer._WorkspaceComposer__resolved_files[0]
        assert_that(workspace_file.path).is_equal_to("workspace.code-workspace")
        assert_that(workspace_file.content).is_not_empty()

    def test_compose_with_projects(self):
        """Test composing a workspace with projects."""
        workspace = WorkspaceModel(
            policies=Policies(
                {
                    "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
                    "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                    "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
                }
            ),
            projects=Projects(
                {
                    "test-project-1": UserProject(path="tools"),
                    "test-project-2": UserProject(path="tools"),
                }
            ),
        )

        path_resolver = Mock(spec=PathResolver)
        path_resolver.resolve.return_value = []

        composer = WorkspaceComposer(workspace, path_resolver)
        composer.compose()

        resolved_files = composer._WorkspaceComposer__resolved_files
        assert_that(resolved_files).is_not_none()
        assert_that(resolved_files).is_length(
            1
        )  # Only workspace file, no project files

        # Verify workspace file content contains project folders
        workspace_file = resolved_files[0]
        workspace_content = json.loads(workspace_file.content)
        assert_that(workspace_content).contains_key("folders")
        assert_that(workspace_content["folders"]).is_length(2)

    def test_compose_with_repository_project(self):
        """Test composing a workspace with a repository project."""
        workspace = WorkspaceModel(
            policies=Policies(
                {
                    "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
                    "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                    "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
                }
            ),
            projects=Projects(
                {
                    ReservedProjectKey.ROOT: RepositoryProject(path="."),
                }
            ),
        )

        path_resolver = Mock(spec=PathResolver)
        path_resolver.resolve.return_value = []

        composer = WorkspaceComposer(workspace, path_resolver)
        composer.compose()

        resolved_files = composer._WorkspaceComposer__resolved_files
        assert_that(resolved_files).is_not_none()
        assert_that(resolved_files).is_length(1)

        # Verify workspace file content contains root folder
        workspace_file = resolved_files[0]
        workspace_content = json.loads(workspace_file.content)
        assert_that(workspace_content).contains_key("folders")
        assert_that(workspace_content["folders"]).is_length(1)
        assert_that(workspace_content["folders"][0]["path"]).is_equal_to(".")


class TestWorkspaceComposerResolveFileSpecification:
    """Test WorkspaceComposer _resolve_file_specification method."""

    def test_resolve_file_specification_creates_workspace_file(
        self, minimal_workspace_configuration
    ):
        """Test that _resolve_file_specification creates a workspace file."""
        path_resolver = Mock(spec=PathResolver)
        composer = WorkspaceComposer(minimal_workspace_configuration, path_resolver)

        resolved_file = composer._resolve_file_specification()

        assert_that(resolved_file).is_instance_of(ResolvedFile)
        assert_that(resolved_file.path).is_equal_to("workspace.code-workspace")
        assert_that(resolved_file.content).is_not_empty()

        # Verify content is valid JSON
        content = json.loads(resolved_file.content)
        assert_that(content).contains_key("folders")
        assert_that(content).contains_key("settings")

    def test_resolve_file_specification_includes_project_folders(self):
        """Test that _resolve_file_specification includes project folders."""
        workspace = WorkspaceModel(
            policies=Policies(
                {
                    "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
                    "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                    "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
                }
            ),
            projects=Projects(
                {
                    "project1": UserProject(path="tools", alias="ProjectOne"),
                    "project2": UserProject(path="tools"),
                }
            ),
        )

        path_resolver = Mock(spec=PathResolver)
        composer = WorkspaceComposer(workspace, path_resolver)

        resolved_file = composer._resolve_file_specification()
        content = json.loads(resolved_file.content)

        assert_that(content["folders"]).is_length(2)

        # Check first project
        folder1 = content["folders"][0]
        assert_that(folder1["path"]).is_equal_to(str(pathlib.Path("tools", "project1")))
        assert_that(folder1["name"]).is_equal_to("ProjectOne")

        # Check second project
        folder2 = content["folders"][1]
        assert_that(folder2["path"]).is_equal_to(str(pathlib.Path("tools", "project2")))
        assert_that(folder2["name"]).is_equal_to("project2")

    def test_resolve_file_specification_with_repository_root(self):
        """Test that _resolve_file_specification handles repository root project."""
        workspace = WorkspaceModel(
            policies=Policies(
                {
                    "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
                    "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                    "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
                }
            ),
            projects=Projects(
                {
                    ReservedProjectKey.ROOT: RepositoryProject(path="."),
                }
            ),
        )

        path_resolver = Mock(spec=PathResolver)
        composer = WorkspaceComposer(workspace, path_resolver)

        resolved_file = composer._resolve_file_specification()
        content = json.loads(resolved_file.content)

        assert_that(content["folders"]).is_length(1)
        folder = content["folders"][0]
        assert_that(folder["path"]).is_equal_to(".")
        assert_that(folder).does_not_contain_key("name")


class TestWorkspaceComposerResolveProjectFiles:
    """Test WorkspaceComposer _resolve_project_files method."""

    def test_resolve_project_files_with_no_projects(
        self, minimal_workspace_configuration
    ):
        """Test _resolve_project_files with no projects."""
        path_resolver = Mock(spec=PathResolver)
        path_resolver.resolve.return_value = []

        composer = WorkspaceComposer(minimal_workspace_configuration, path_resolver)

        resolved_files = composer._resolve_project_files()

        assert_that(resolved_files).is_empty()

    def test_resolve_project_files_with_projects(self, path_resolver):
        """Test _resolve_project_files with projects."""
        workspace = WorkspaceModel(
            policies=Policies(
                {
                    "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
                    "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                    "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
                }
            ),
            projects=Projects(
                {
                    "test-project": UserProject(
                        path="tools",
                        vscode=VSCodeFolder(
                            settings=[Folder({"python": [File("base")]})]
                        ),
                    ),
                }
            ),
        )

        composer = WorkspaceComposer(workspace, path_resolver)
        resolved_files = composer._resolve_project_files()

        assert_that(resolved_files).is_length(1)
        assert_that(resolved_files[0].path).is_equal_to(
            str(pathlib.Path("tools", "test-project", ".vscode", "settings.json"))
        )
        assert_that(resolved_files[0].content).is_not_empty()

    def test_resolve_project_files_with_multiple_projects(self, path_resolver):
        """Test _resolve_project_files with multiple projects."""
        workspace = WorkspaceModel(
            policies=Policies(
                {
                    "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
                    "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                    "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
                }
            ),
            projects=Projects(
                {
                    "project1": UserProject(
                        path="tools",
                        vscode=VSCodeFolder(
                            settings=[Folder({"python": [File("base")]})]
                        ),
                    ),
                    "project2": UserProject(
                        path="tools",
                        vscode=VSCodeFolder(
                            settings=[Folder({"python": [File("base")]})]
                        ),
                    ),
                }
            ),
        )

        composer = WorkspaceComposer(workspace, path_resolver)
        resolved_files = composer._resolve_project_files()

        assert_that(resolved_files).is_length(2)
        assert_that(resolved_files[0].path).is_equal_to(
            str(pathlib.Path("tools", "project1", ".vscode", "settings.json"))
        )
        assert_that(resolved_files[0].content).is_not_empty()
        assert_that(resolved_files[1].path).is_equal_to(
            str(pathlib.Path("tools", "project2", ".vscode", "settings.json"))
        )
        assert_that(resolved_files[1].content).is_not_empty()

    def test_resolve_project_files_with_project_variables(self, path_resolver):
        """Test _resolve_project_files with project variables."""
        workspace = WorkspaceModel(
            policies=Policies(
                {
                    "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
                    "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                    "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
                }
            ),
            projects=Projects(
                {
                    "test-project": UserProject(
                        path="tools",
                        variables=Variables(
                            {
                                "pytest-capture": StringVariable("no"),
                            }
                        ),
                        vscode=VSCodeFolder(
                            settings=[
                                Folder(
                                    {"python": [Folder({"pytest": [File("capture")]})]}
                                )
                            ]
                        ),
                    ),
                }
            ),
        )

        composer = WorkspaceComposer(workspace, path_resolver)
        resolved_files = composer._resolve_project_files()

        assert_that(resolved_files).is_length(1)
        assert_that(resolved_files[0].path).is_equal_to(
            str(pathlib.Path("tools", "test-project", ".vscode", "settings.json"))
        )
        assert_that(resolved_files[0].content).is_not_empty()
        assert_that(resolved_files[0].content).contains('"--capture=no"')

    def test_resolve_project_files_with_ref_project_variables(self, path_resolver):
        """Test _resolve_project_files with ref project variables."""
        workspace = WorkspaceModel(
            policies=Policies(
                {
                    "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
                    "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                    "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
                }
            ),
            projects=Projects(
                {
                    "ref": RepositoryProject(
                        variables=Variables(
                            {
                                "pytest-capture": StringVariable("no"),
                            }
                        ),
                        vscode=VSCodeFolder(
                            settings=[
                                Folder(
                                    {"python": [Folder({"pytest": [File("capture")]})]}
                                )
                            ]
                        ),
                    ),
                    "test-project": UserProject(
                        path="tools",
                        variables=Variables(
                            {
                                "pytest-show-capture": StringVariable("no"),
                            }
                        ),
                        vscode=VSCodeFolder(
                            settings=[
                                Folder(
                                    {
                                        "python": [
                                            Folder(
                                                {
                                                    "pytest": [
                                                        File("$ref"),
                                                        File("show-capture"),
                                                    ]
                                                }
                                            )
                                        ]
                                    }
                                )
                            ]
                        ),
                    ),
                }
            ),
        )

        composer = WorkspaceComposer(workspace, path_resolver)
        resolved_files = composer._resolve_project_files()

        assert_that(resolved_files).is_length(1)
        assert_that(resolved_files[0].path).is_equal_to(
            str(pathlib.Path("tools", "test-project", ".vscode", "settings.json"))
        )
        assert_that(resolved_files[0].content).is_not_empty()
        assert_that(resolved_files[0].content).contains('"--capture=no"')
        assert_that(resolved_files[0].content).contains('"--show-capture=no"')


class TestWorkspaceComposerSave:
    """Test WorkspaceComposer save functionality."""

    def test_save_without_compose_raises_error(
        self, minimal_workspace_configuration, tmp_path
    ):
        """Test that save raises an error if compose hasn't been called."""
        path_resolver = Mock(spec=PathResolver)
        composer = WorkspaceComposer(minimal_workspace_configuration, path_resolver)
        policies = Policies.model_construct(
            root={
                ReservedPolicyKeys.FOLDER: FolderPolicy(
                    create=FolderCreatePolicy.ALWAYS
                ),
                ReservedPolicyKeys.FILE: FilePolicy(write=FileWritePolicy.OVERWRITE),
            }
        )
        with pytest.raises(ValueError, match="Files are not resolved yet."):
            composer.save(tmp_path, policies)

    def test_save_creates_files(self, minimal_workspace_configuration, tmp_path):
        """Test that save creates the workspace file."""
        path_resolver = Mock(spec=PathResolver)
        path_resolver.user_context = Path(".")
        path_resolver.resolve.return_value = []
        policies = Policies.model_construct(
            root={
                ReservedPolicyKeys.FOLDER: FolderPolicy(
                    create=FolderCreatePolicy.ALWAYS
                ),
                ReservedPolicyKeys.FILE: FilePolicy(write=FileWritePolicy.OVERWRITE),
            }
        )

        composer = WorkspaceComposer(minimal_workspace_configuration, path_resolver)
        composer.compose()
        composer.save(tmp_path, policies)

        workspace_file = tmp_path / "workspace.code-workspace"
        assert_that(workspace_file.exists()).is_true()
        assert_that(workspace_file.read_text()).is_not_empty()

    def test_save_writes_valid_json(self, minimal_workspace_configuration, tmp_path):
        """Test that save writes valid JSON content."""
        path_resolver = Mock(spec=PathResolver)
        path_resolver.resolve.return_value = []
        policies = Policies.model_construct(
            root={
                ReservedPolicyKeys.FOLDER: FolderPolicy(
                    create=FolderCreatePolicy.ALWAYS
                ),
                ReservedPolicyKeys.FILE: FilePolicy(write=FileWritePolicy.OVERWRITE),
            }
        )

        composer = WorkspaceComposer(minimal_workspace_configuration, path_resolver)
        composer.compose()
        composer.save(tmp_path, policies)

        workspace_file = tmp_path / "workspace.code-workspace"
        content = workspace_file.read_text()

        # Verify it's valid JSON
        json_content = json.loads(content)
        assert_that(json_content).contains_key("folders")
        assert_that(json_content).contains_key("settings")

    def test_save_with_project_files(self, user_context, path_resolver):
        """Test that save creates both workspace and project files."""
        workspace = WorkspaceModel(
            policies=Policies(
                {
                    "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
                    "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                    "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
                }
            ),
            projects=Projects(
                {
                    "test-project": UserProject(
                        path="tools",
                        vscode=VSCodeFolder(
                            settings=[Folder({"python": [File("base")]})]
                        ),
                    ),
                }
            ),
        )
        policies = Policies.model_construct(
            root={
                ReservedPolicyKeys.FOLDER: FolderPolicy(
                    create=FolderCreatePolicy.ALWAYS
                ),
                ReservedPolicyKeys.FILE: FilePolicy(write=FileWritePolicy.OVERWRITE),
            }
        )
        composer = WorkspaceComposer(workspace, path_resolver)
        composer.compose()
        composer.save(user_context, policies)

        # Check workspace file
        workspace_file = user_context / "workspace.code-workspace"
        assert_that(str(workspace_file)).exists()

        # Check project file
        project_file = (
            user_context / "tools" / "test-project" / ".vscode" / "settings.json"
        )
        assert_that(str(project_file)).exists()
        assert_that(project_file.read_text()).is_not_empty()

    def test_save_uses_workspace_policies(
        self, minimal_workspace_configuration, tmp_path, caplog
    ):
        """Test that save uses the workspace policies for file operations."""
        path_resolver = Mock(spec=PathResolver)
        path_resolver.resolve.return_value = []
        policies = Policies.model_construct(
            root={
                ReservedPolicyKeys.FOLDER: FolderPolicy(
                    create=FolderCreatePolicy.ALWAYS
                ),
                ReservedPolicyKeys.FILE: FilePolicy(write=FileWritePolicy.OVERWRITE),
            }
        )
        composer = WorkspaceComposer(minimal_workspace_configuration, path_resolver)
        composer.compose()

        # Mock the _save_file method to verify it's called with correct policies
        with patch.object(composer, "_save_file") as mock_save_file:
            composer.save(tmp_path, policies)

            # Verify _save_file was called with workspace policies
            mock_save_file.assert_called_once()
            call_args = mock_save_file.call_args
            assert_that(call_args[1]["folder_policy"]).is_equal_to(
                FolderCreatePolicy.ALWAYS
            )
            assert_that(call_args[1]["file_policy"]).is_equal_to(
                FileWritePolicy.OVERWRITE
            )

    def test_save_creates_directories_as_needed(
        self, minimal_workspace_configuration, tmp_path
    ):
        """Test that save creates directories when needed."""
        path_resolver = Mock(spec=PathResolver)
        path_resolver.resolve.return_value = []
        policies = Policies.model_construct(
            root={
                ReservedPolicyKeys.FOLDER: FolderPolicy(
                    create=FolderCreatePolicy.ALWAYS
                ),
                ReservedPolicyKeys.FILE: FilePolicy(write=FileWritePolicy.OVERWRITE),
            }
        )
        composer = WorkspaceComposer(minimal_workspace_configuration, path_resolver)
        composer.compose()

        # Create a nested path that doesn't exist
        nested_path = tmp_path / "nested" / "deep" / "path"
        composer.save(nested_path, policies)

        workspace_file = nested_path / "workspace.code-workspace"
        assert_that(workspace_file.exists()).is_true()
