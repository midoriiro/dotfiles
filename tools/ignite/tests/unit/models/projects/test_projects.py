import pytest
from pydantic import ValidationError
from assertpy import assert_that
from pathlib import Path

from ignite.models.projects import (
    Projects, UserProject, RepositoryProject, ReservedProjectKey
)
from ignite.models.fs import Folder, File
from ignite.models.settings import VSCodeFolder


class TestValidProjects:
    """Test cases for valid Projects configurations."""

    def test_minimal_projects_with_user_project(self):
        """Test that a minimal projects with user project is accepted."""
        projects = Projects({
            "test-project": UserProject(path="/workspace/test-project")
        })
        assert_that(projects.root).contains_key("test-project")
        assert_that(projects.root["test-project"]).is_instance_of(UserProject)
        assert_that(projects.root["test-project"].path).is_equal_to("/workspace/test-project")

    def test_projects_with_repository_project(self):
        """Test that projects with repository project is accepted."""
        projects = Projects({
            "root": RepositoryProject()
        })
        assert_that(projects.root).contains_key("root")
        assert_that(projects.root["root"]).is_instance_of(RepositoryProject)

    def test_projects_with_mixed_project_types(self):
        """Test that projects with mixed project types is accepted."""
        projects = Projects({
            "root": RepositoryProject(),
            "ref": RepositoryProject(),
            "user-project": UserProject(path="/workspace/user-project")
        })
        assert_that(projects.root).contains_key("root")
        assert_that(projects.root).contains_key("ref")
        assert_that(projects.root).contains_key("user-project")
        assert_that(projects.root["root"]).is_instance_of(RepositoryProject)
        assert_that(projects.root["ref"]).is_instance_of(RepositoryProject)
        assert_that(projects.root["user-project"]).is_instance_of(UserProject)

    def test_projects_with_user_project_with_alias(self):
        """Test that projects with user project with alias is accepted."""
        projects = Projects({
            "project-key": UserProject(
                path="/workspace/project",
                alias="my-alias"
            )
        })
        assert_that(projects.root).contains_key("project-key")
        user_project = projects.root["project-key"]
        assert_that(user_project).is_instance_of(UserProject)
        assert_that(user_project.alias).is_equal_to("my-alias")

    def test_projects_with_user_project_with_vscode(self):
        """Test that projects with user project with VSCode configuration is accepted."""
        vscode_config = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})]
        )
        projects = Projects({
            "test-project": UserProject(
                path="/workspace/test-project",
                vscode=vscode_config
            )
        })
        assert_that(projects.root).contains_key("test-project")
        user_project = projects.root["test-project"]
        assert_that(user_project.vscode).is_instance_of(VSCodeFolder)

    def test_projects_with_repository_project_with_vscode(self):
        """Test that projects with repository project with VSCode configuration is accepted."""
        vscode_config = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})],
            tasks=[Folder({"poetry": [File("build")]})]
        )
        projects = Projects({
            "root": RepositoryProject(vscode=vscode_config)
        })
        assert_that(projects.root).contains_key("root")
        repo_project = projects.root["root"]
        assert_that(repo_project.vscode).is_instance_of(VSCodeFolder)


class TestProjectsValidation:
    """Test cases for Projects validation."""

    def test_empty_projects_raises_error(self):
        """Test that empty projects raises validation error."""
        with pytest.raises(ValueError, match="At least one project must be specified"):
            Projects({})

    def test_root_project_with_wrong_type_raises_error(self):
        """Test that root project with wrong type raises validation error."""
        with pytest.raises(ValueError, match="The value for key 'root' must be a RepositoryProject instance"):
            Projects({
                "root": UserProject(path="/workspace/test")
            })

    def test_ref_project_with_wrong_type_raises_error(self):
        """Test that ref project with wrong type raises validation error."""
        with pytest.raises(ValueError, match="The value for key 'ref' must be a RepositoryProject instance"):
            Projects({
                "ref": UserProject(path="/workspace/test")
            })

    def test_valid_mixed_projects_with_reserved_keys(self):
        """Test that valid mixed projects with reserved keys is accepted."""
        projects = Projects({
            "root": RepositoryProject(),
            "ref": RepositoryProject(),
            "user-project": UserProject(path="/workspace/user-project")
        })
        assert_that(projects.root).contains_key("root")
        assert_that(projects.root).contains_key("ref")
        assert_that(projects.root).contains_key("user-project")


class TestProjectsResolveProjectFolders:
    """Test cases for the resolve_project_folders method of Projects."""

    def test_resolve_project_folders_with_user_project_no_vscode(self):
        """Test that resolve_project_folders works with user project without VSCode."""
        projects = Projects({
            "test-project": UserProject(path="/workspace/test-project")
        })
        result = projects.resolve_project_folders()
        
        assert_that(result).contains_key("test-project")
        assert_that(result["test-project"]).is_empty()

    def test_resolve_project_folders_with_user_project_with_vscode(self):
        """Test that resolve_project_folders works with user project with VSCode."""
        vscode_config = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})]
        )
        projects = Projects({
            "test-project": UserProject(
                path="/workspace/test-project",
                vscode=vscode_config
            )
        })
        result = projects.resolve_project_folders()
        
        assert_that(result).contains_key("test-project")
        assert_that(result["test-project"]).is_length(1)
        resolved_folder = result["test-project"][0]
        assert_that(resolved_folder.destination).is_equal_to("/workspace/test-project/test-project/.vscode/settings.json")

    def test_resolve_project_folders_with_user_project_with_alias(self):
        """Test that resolve_project_folders uses alias when available."""
        vscode_config = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})]
        )
        projects = Projects({
            "project-key": UserProject(
                path="/workspace/project",
                alias="my-alias",
                vscode=vscode_config
            )
        })
        result = projects.resolve_project_folders()
        
        assert_that(result).contains_key("my-alias")
        assert_that(result["my-alias"]).is_length(1)
        resolved_folder = result["my-alias"][0]
        assert_that(resolved_folder.destination).is_equal_to("/workspace/project/project-key/.vscode/settings.json")

    def test_resolve_project_folders_with_repository_project_no_vscode(self):
        """Test that resolve_project_folders works with repository project without VSCode."""
        projects = Projects({
            "root": RepositoryProject()
        })
        result = projects.resolve_project_folders()
        
        assert_that(result).contains_key("root")
        assert_that(result["root"]).is_empty()

    def test_resolve_project_folders_with_repository_project_with_vscode(self):
        """Test that resolve_project_folders works with repository project with VSCode."""
        vscode_config = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})],
            tasks=[Folder({"poetry": [File("build")]})]
        )
        projects = Projects({
            "root": RepositoryProject(vscode=vscode_config)
        })
        result = projects.resolve_project_folders()
        
        assert_that(result).contains_key("root")
        assert_that(result["root"]).is_length(2)
        destinations = [folder.destination for folder in result["root"]]
        assert_that(destinations).contains(".vscode/settings.json")
        assert_that(destinations).contains(".vscode/tasks.json")

    def test_resolve_project_folders_with_mixed_projects(self):
        """Test that resolve_project_folders works with mixed project types."""
        vscode_config = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})]
        )
        projects = Projects({
            "root": RepositoryProject(vscode=vscode_config),
            "user-project": UserProject(
                path="/workspace/user-project",
                vscode=vscode_config
            )
        })
        result = projects.resolve_project_folders()
        
        assert_that(result).contains_key("root")
        assert_that(result).contains_key("user-project")
        assert_that(result["root"]).is_length(1)
        assert_that(result["user-project"]).is_length(1)

    def test_resolve_project_folders_with_multiple_user_projects(self):
        """Test that resolve_project_folders works with multiple user projects."""
        vscode_config = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})]
        )
        projects = Projects({
            "project1": UserProject(
                path="/workspace/project1",
                vscode=vscode_config
            ),
            "project2": UserProject(
                path="/workspace/project2",
                alias="my-project",
                vscode=vscode_config
            )
        })
        result = projects.resolve_project_folders()
        
        assert_that(result).contains_key("project1")
        assert_that(result).contains_key("my-project")
        assert_that(result["project1"]).is_length(1)
        assert_that(result["my-project"]).is_length(1)


class TestProjectsEdgeCases:
    """Test cases for edge cases in Projects."""

    def test_projects_with_user_project_no_alias(self):
        """Test that user project without alias uses key as identifier."""
        vscode_config = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})]
        )
        projects = Projects({
            "project-key": UserProject(
                path="/workspace/project",
                vscode=vscode_config
            )
        })
        result = projects.resolve_project_folders()
        
        assert_that(result).contains_key("project-key")
        assert_that(result["project-key"]).is_length(1)

    def test_projects_with_user_project_empty_alias(self):
        """Test that user project with empty alias raises validation error."""
        vscode_config = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})]
        )
        
        with pytest.raises(ValidationError):
            Projects({
                "project-key": UserProject(
                    path="/workspace/project",
                    alias="",
                    vscode=vscode_config
                )
            })
    
    def test_projects_with_complex_vscode_configuration(self):
        """Test that projects with complex VSCode configuration works correctly."""
        vscode_config = VSCodeFolder(
            settings=[
                Folder({"python": [File("base"), File("black")]}),
                Folder({"typescript": [File("base")]})
            ],
            tasks=[
                Folder({"poetry": [File("build"), File("test")]}),
                Folder({"npm": [File("install")]})
            ]
        )
        projects = Projects({
            "root": RepositoryProject(vscode=vscode_config)
        })
        result = projects.resolve_project_folders()
        
        assert_that(result).contains_key("root")
        assert_that(result["root"]).is_length(2)
        
        # Check that all expected files are present
        all_sources = []
        for folder in result["root"]:
            all_sources.extend(folder.sources)
        
        expected_sources = [
            "vscode/settings/python/base",
            "vscode/settings/python/black",
            "vscode/settings/typescript/base",
            "vscode/tasks/poetry/build",
            "vscode/tasks/poetry/test",
            "vscode/tasks/npm/install"
        ]
        
        for expected_source in expected_sources:
            assert_that(all_sources).contains(expected_source)


class TestProjectsInheritance:
    """Test cases for Projects inheritance and type checking."""

    def test_projects_inherits_from_root_model(self):
        """Test that Projects inherits from RootModel."""
        projects = Projects({
            "test-project": UserProject(path="/workspace/test-project")
        })
        assert_that(projects).is_instance_of(Projects)
        assert_that(hasattr(projects, 'root')).is_true()

    def test_projects_root_attribute_type(self):
        """Test that Projects root attribute has correct type."""
        projects = Projects({
            "test-project": UserProject(path="/workspace/test-project")
        })
        assert_that(projects.root).is_instance_of(dict)
        assert_that(projects.root["test-project"]).is_instance_of(UserProject)

    def test_projects_with_repository_project_type(self):
        """Test that Projects can contain RepositoryProject instances."""
        projects = Projects({
            "root": RepositoryProject()
        })
        assert_that(projects.root["root"]).is_instance_of(RepositoryProject)


class TestProjectsReservedKeys:
    """Test cases for Projects with reserved keys."""

    def test_reserved_project_keys_enum_values(self):
        """Test that ReservedProjectKey enum has correct values."""
        assert_that(ReservedProjectKey.ROOT).is_equal_to("root")
        assert_that(ReservedProjectKey.REF).is_equal_to("ref")

    def test_projects_with_root_key(self):
        """Test that Projects accepts root key."""
        projects = Projects({
            ReservedProjectKey.ROOT: RepositoryProject()
        })
        assert_that(projects.root).contains_key(ReservedProjectKey.ROOT)

    def test_projects_with_ref_key(self):
        """Test that Projects accepts ref key."""
        projects = Projects({
            ReservedProjectKey.REF: RepositoryProject()
        })
        assert_that(projects.root).contains_key(ReservedProjectKey.REF)

    def test_projects_with_both_reserved_keys(self):
        """Test that Projects accepts both reserved keys."""
        projects = Projects({
            ReservedProjectKey.ROOT: RepositoryProject(),
            ReservedProjectKey.REF: RepositoryProject()
        })
        assert_that(projects.root).contains_key(ReservedProjectKey.ROOT)
        assert_that(projects.root).contains_key(ReservedProjectKey.REF)
