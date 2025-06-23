import pathlib
from unittest.mock import Mock, patch
from typing import Dict, List

import pytest
from assertpy import assert_that

from ignite.models.policies import Policies, ContainerPolicy, ContainerBackendPolicy, FolderPolicy, FolderCreatePolicy, FilePolicy, FileWritePolicy
from ignite.models.projects import Projects, UserProject, RepositoryProject, ReservedProjectKey
from ignite.models.settings import VSCodeFolder
from ignite.models.workspace import Workspace, WorkspaceFileSpecification, WorkspaceFolderSpecification
from ignite.models.fs import File, Folder, ResolvedFolder
from ignite.resolvers import PathResolver


class TestWorkspace:
    """Test cases for the Workspace model."""

    def test_workspace_creation_with_valid_data(self, minimal_workspace_configuration):
        """Test that a Workspace can be created with valid data."""
        workspace = minimal_workspace_configuration
        
        assert_that(workspace).is_not_none()
        assert_that(workspace.policies).is_instance_of(Policies)
        assert_that(workspace.projects).is_instance_of(Projects)

    def test_workspace_creation_with_custom_data(self):
        """Test that a Workspace can be created with custom data."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
            "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
        })
        
        projects = Projects({
            "test-project": UserProject(path="/workspace/test-project"),
            "another-project": UserProject(
                path="/workspace/another-project",
                alias="custom-alias"
            ),
        })
        
        workspace = Workspace(policies=policies, projects=projects)
        
        assert_that(workspace.policies).is_equal_to(policies)
        assert_that(workspace.projects).is_equal_to(projects)

    def test_workspace_with_repository_projects(self):
        """Test that a Workspace can be created with repository projects."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
            "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
        })
        
        projects = Projects({
            ReservedProjectKey.ROOT: RepositoryProject(),
            ReservedProjectKey.REF: RepositoryProject(),
        })
        
        workspace = Workspace(policies=policies, projects=projects)
        
        assert_that(workspace.projects.root).contains_key(ReservedProjectKey.ROOT)
        assert_that(workspace.projects.root).contains_key(ReservedProjectKey.REF)
        assert_that(workspace.projects.root[ReservedProjectKey.ROOT]).is_instance_of(RepositoryProject)
        assert_that(workspace.projects.root[ReservedProjectKey.REF]).is_instance_of(RepositoryProject)


class TestWorkspaceResolveProjectFolders:
    """Test cases for the resolve_project_folders method."""

    def test_resolve_project_folders_with_user_projects_only(self):
        """Test resolve_project_folders with only user projects."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
            "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
        })

        projects = Projects({
            "user-project": UserProject(
                path="/workspace/user-project",
                vscode=VSCodeFolder(settings=[Folder({"python": [File("$ref")]})])
            ),
        })

        workspace = Workspace(policies=policies, projects=projects)

        path_resolver = Mock(spec=PathResolver)
        path_resolver.resolve.return_value = ["/resolved/path"]
        
        result = workspace.resolve_project_folders(path_resolver)
        
        assert_that(result).contains_key("user-project")
        path_resolver.resolve.assert_called_once()

    def test_resolve_project_folders_with_ref_project(self):
        """Test resolve_project_folders when a ref project is present."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
            "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
        })
        
        projects = Projects({
            ReservedProjectKey.REF: RepositoryProject(
                vscode=VSCodeFolder(settings=[Folder({"python": [File("base")]})])
            ),
            "user-project": UserProject(
                path="/workspace/user-project",
                vscode=VSCodeFolder(settings=[Folder({"python": [File("$ref")]})])
            ),
        })
        
        workspace = Workspace(policies=policies, projects=projects)
        
        # Mock the projects.resolve_project_folders method
        path_resolver = Mock(spec=PathResolver)
        path_resolver.resolve.return_value = ["/resolved/path"]
        
        result = workspace.resolve_project_folders(path_resolver)
        
        # Verify ref project is removed from result
        assert_that(result).does_not_contain_key(ReservedProjectKey.REF)
        assert_that(result).contains_key("user-project")
        
        assert_that(path_resolver.resolve.call_count).is_equal_to(1)
        call_args = path_resolver.resolve.call_args
        assert_that(call_args[0][1]).is_not_none()


class TestWorkspaceResolveFileSpecification:
    """Test cases for the resolve_file_specification method."""

    def test_resolve_file_specification_with_user_projects(self):
        """Test resolve_file_specification with user projects."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
            "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
        })
        
        projects = Projects({
            "project1": UserProject(path="/workspace/project1"),
            "project2": UserProject(
                path="/workspace/project2",
                alias="custom-alias"
            ),
        })
        
        workspace = Workspace(policies=policies, projects=projects)
        
        result = workspace.resolve_file_specification()
        
        assert_that(result).is_instance_of(WorkspaceFileSpecification)
        assert_that(result.folders).is_length(2)
        assert_that(result.settings).is_empty()
        
        # Check first project
        folder1 = result.folders[0]
        assert_that(folder1.path).is_equal_to("/workspace/project1/project1")
        assert_that(folder1.name).is_equal_to("project1")
        
        # Check second project with alias
        folder2 = result.folders[1]
        assert_that(folder2.path).is_equal_to("/workspace/project2/project2")
        assert_that(folder2.name).is_equal_to("custom-alias")

    def test_resolve_file_specification_with_root_repository_project(self):
        """Test resolve_file_specification with root repository project."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
            "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
        })
        
        projects = Projects({
            ReservedProjectKey.ROOT: RepositoryProject(),
        })
        
        workspace = Workspace(policies=policies, projects=projects)
        
        result = workspace.resolve_file_specification()
        
        assert_that(result.folders).is_length(1)
        folder = result.folders[0]
        assert_that(folder.path).is_equal_to(".")
        assert_that(folder.name).is_none()

    def test_resolve_file_specification_with_mixed_projects(self):
        """Test resolve_file_specification with both user and repository projects."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
            "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
        })
        
        projects = Projects({
            ReservedProjectKey.ROOT: RepositoryProject(),
            "user-project": UserProject(path="/workspace/user-project"),
        })
        
        workspace = Workspace(policies=policies, projects=projects)
        
        result = workspace.resolve_file_specification()
        
        assert_that(result.folders).is_length(2)
        
        # Check root project
        root_folder = next(f for f in result.folders if f.path == ".")
        assert_that(root_folder.name).is_none()
        
        # Check user project
        user_folder = next(f for f in result.folders if f.path != ".")
        assert_that(user_folder.path).is_equal_to("/workspace/user-project/user-project")
        assert_that(user_folder.name).is_equal_to("user-project")

    def test_resolve_file_specification_with_ref_project_only(self):
        """Test resolve_file_specification with only ref project (should be ignored)."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
            "file": FilePolicy(write=FileWritePolicy.OVERWRITE),
        })
        
        projects = Projects({
            ReservedProjectKey.REF: RepositoryProject(),
        })
        
        workspace = Workspace(policies=policies, projects=projects)
        
        result = workspace.resolve_file_specification()
        
        assert_that(result.folders).is_empty()
        assert_that(result.settings).is_empty()


class TestWorkspaceFolderSpecification:
    """Test cases for the WorkspaceFolderSpecification model."""

    def test_workspace_folder_specification_creation(self):
        """Test that WorkspaceFolderSpecification can be created with valid data."""
        folder_spec = WorkspaceFolderSpecification(
            path="/workspace/project",
            name="test-project"
        )
        
        assert_that(folder_spec.path).is_equal_to("/workspace/project")
        assert_that(folder_spec.name).is_equal_to("test-project")

    def test_workspace_folder_specification_without_name(self):
        """Test that WorkspaceFolderSpecification can be created without a name."""
        folder_spec = WorkspaceFolderSpecification(path="/workspace/project")
        
        assert_that(folder_spec.path).is_equal_to("/workspace/project")
        assert_that(folder_spec.name).is_none()


class TestWorkspaceFileSpecification:
    """Test cases for the WorkspaceFileSpecification model."""

    def test_workspace_file_specification_creation(self):
        """Test that WorkspaceFileSpecification can be created with valid data."""
        folder_spec = WorkspaceFolderSpecification(path="/workspace/project")
        file_spec = WorkspaceFileSpecification(
            folders=[folder_spec],
            settings={"key": "value"}
        )
        
        assert_that(file_spec.folders).is_length(1)
        assert_that(file_spec.folders[0]).is_equal_to(folder_spec)
        assert_that(file_spec.settings).is_equal_to({"key": "value"})

    def test_workspace_file_specification_with_default_settings(self):
        """Test that WorkspaceFileSpecification uses default empty settings."""
        folder_spec = WorkspaceFolderSpecification(path="/workspace/project")
        file_spec = WorkspaceFileSpecification(folders=[folder_spec])
        
        assert_that(file_spec.settings).is_empty()

    def test_workspace_file_specification_empty_folders(self):
        """Test that WorkspaceFileSpecification can be created with empty folders."""
        file_spec = WorkspaceFileSpecification(folders=[])
        
        assert_that(file_spec.folders).is_empty()
        assert_that(file_spec.settings).is_empty()
