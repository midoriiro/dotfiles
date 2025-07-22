import pathlib

import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.fs import ResolvedFolder
from ignite.models.projects import RepositoryProject
from ignite.models.settings import File, Folder, VSCodeFolder


class TestValidRepositoryProject:
    """Test cases for valid RepositoryProject configurations."""

    def test_minimal_repository_project(self):
        """Test that a minimal repository project without vscode is accepted."""
        repository_project = RepositoryProject()

        assert_that(repository_project.vscode).is_none()

    def test_repository_project_with_vscode_settings(self):
        """Test that a repository project with VSCode settings is accepted."""
        vscode_folder = VSCodeFolder(settings=[Folder({"python": [File("base")]})])
        repository_project = RepositoryProject(vscode=vscode_folder)

        assert_that(repository_project.vscode).is_not_none()
        assert_that(repository_project.vscode.settings).is_not_none()
        assert_that(repository_project.vscode.tasks).is_none()

    def test_repository_project_with_vscode_tasks(self):
        """Test that a repository project with VSCode tasks is accepted."""
        vscode_folder = VSCodeFolder(tasks=[Folder({"poetry": [File("build")]})])
        repository_project = RepositoryProject(vscode=vscode_folder)

        assert_that(repository_project.vscode).is_not_none()
        assert_that(repository_project.vscode.settings).is_none()
        assert_that(repository_project.vscode.tasks).is_not_none()

    def test_repository_project_with_both_settings_and_tasks(self):
        """Test that a repository project with both settings and tasks is accepted."""
        vscode_folder = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})],
            tasks=[Folder({"poetry": [File("build")]})],
        )
        repository_project = RepositoryProject(vscode=vscode_folder)

        assert_that(repository_project.vscode).is_not_none()
        assert_that(repository_project.vscode.settings).is_not_none()
        assert_that(repository_project.vscode.tasks).is_not_none()


class TestRepositoryProjectValidation:
    """Test cases for RepositoryProject validation."""

    def test_repository_project_with_invalid_vscode_settings_raises_error(self):
        """Test that repository project with invalid VSCode settings raises validation error."""
        with pytest.raises(ValidationError):
            RepositoryProject(vscode="invalid-vscode")

    def test_repository_project_with_empty_vscode_settings_raises_error(self):
        """Test that repository project with empty VSCode settings raises validation error."""
        with pytest.raises(ValidationError):
            RepositoryProject(vscode=VSCodeFolder(settings=[]))

    def test_repository_project_with_empty_vscode_tasks_raises_error(self):
        """Test that repository project with empty VSCode tasks raises validation error."""
        with pytest.raises(ValidationError):
            RepositoryProject(vscode=VSCodeFolder(tasks=[]))


class TestRepositoryProjectResolveFoldersMethod:
    """Test cases for the resolve_folders method of RepositoryProject."""

    def test_resolve_folders_without_vscode(self):
        """Test that resolve_folders returns empty list when no vscode is configured."""
        repository_project = RepositoryProject()
        resolved_folders = repository_project.resolve_folders()

        assert_that(resolved_folders).is_empty()

    def test_resolve_folders_with_vscode_settings(self):
        """Test that resolve_folders works correctly with VSCode settings."""
        vscode_folder = VSCodeFolder(settings=[Folder({"python": [File("base")]})])
        repository_project = RepositoryProject(vscode=vscode_folder)

        resolved_folders = repository_project.resolve_folders()

        assert_that(resolved_folders).is_not_empty()
        assert_that(resolved_folders).is_length(1)

        resolved_folder = resolved_folders[0]
        assert_that(resolved_folder).is_instance_of(ResolvedFolder)
        assert_that(resolved_folder.destination).is_equal_to(
            str(pathlib.Path(".vscode", "settings.json"))
        )
        assert_that(resolved_folder.sources).contains(
            str(pathlib.Path("vscode", "settings", "python", "base"))
        )

    def test_resolve_folders_with_vscode_tasks(self):
        """Test that resolve_folders works correctly with VSCode tasks."""
        vscode_folder = VSCodeFolder(tasks=[Folder({"poetry": [File("build")]})])
        repository_project = RepositoryProject(vscode=vscode_folder)

        resolved_folders = repository_project.resolve_folders()

        assert_that(resolved_folders).is_not_empty()
        assert_that(resolved_folders).is_length(1)

        resolved_folder = resolved_folders[0]
        assert_that(resolved_folder).is_instance_of(ResolvedFolder)
        assert_that(resolved_folder.destination).is_equal_to(
            str(pathlib.Path(".vscode", "tasks.json"))
        )
        assert_that(resolved_folder.sources).contains(
            str(pathlib.Path("vscode", "tasks", "poetry", "build"))
        )

    def test_resolve_folders_with_both_settings_and_tasks(self):
        """Test that resolve_folders works correctly with both settings and tasks."""
        vscode_folder = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})],
            tasks=[Folder({"poetry": [File("build")]})],
        )
        repository_project = RepositoryProject(vscode=vscode_folder)

        resolved_folders = repository_project.resolve_folders()

        assert_that(resolved_folders).is_not_empty()
        assert_that(resolved_folders).is_length(2)

        # Check that we have both settings and tasks
        destinations = [folder.destination for folder in resolved_folders]
        assert_that(destinations).contains(
            str(pathlib.Path(".vscode", "settings.json"))
        )
        assert_that(destinations).contains(str(pathlib.Path(".vscode", "tasks.json")))

    def test_resolve_folders_with_multiple_settings_sources(self):
        """Test that resolve_folders works correctly with multiple settings sources."""
        vscode_folder = VSCodeFolder(
            settings=[
                Folder({"python": [File("base")]}),
                Folder({"python": [File("black")]}),
            ]
        )
        repository_project = RepositoryProject(vscode=vscode_folder)

        resolved_folders = repository_project.resolve_folders()

        assert_that(resolved_folders).is_not_empty()
        assert_that(resolved_folders).is_length(1)

        resolved_folder = resolved_folders[0]
        assert_that(resolved_folder).is_instance_of(ResolvedFolder)
        assert_that(resolved_folder.destination).is_equal_to(
            str(pathlib.Path(".vscode", "settings.json"))
        )
        assert_that(resolved_folder.sources).contains(
            str(pathlib.Path("vscode", "settings", "python", "base"))
        )
        assert_that(resolved_folder.sources).contains(
            str(pathlib.Path("vscode", "settings", "python", "black"))
        )

    def test_resolve_folders_with_multiple_tasks_sources(self):
        """Test that resolve_folders works correctly with multiple tasks sources."""
        vscode_folder = VSCodeFolder(
            tasks=[
                Folder({"poetry": [File("build")]}),
                Folder({"poetry": [File("test")]}),
            ]
        )
        repository_project = RepositoryProject(vscode=vscode_folder)

        resolved_folders = repository_project.resolve_folders()

        assert_that(resolved_folders).is_not_empty()
        assert_that(resolved_folders).is_length(1)

        resolved_folder = resolved_folders[0]
        assert_that(resolved_folder).is_instance_of(ResolvedFolder)
        assert_that(resolved_folder.destination).is_equal_to(
            str(pathlib.Path(".vscode", "tasks.json"))
        )
        assert_that(resolved_folder.sources).contains(
            str(pathlib.Path("vscode", "tasks", "poetry", "build"))
        )
        assert_that(resolved_folder.sources).contains(
            str(pathlib.Path("vscode", "tasks", "poetry", "test"))
        )


class TestRepositoryProjectEdgeCases:
    """Test cases for edge cases in RepositoryProject."""

    def test_repository_project_with_none_vscode(self):
        """Test that repository project with explicit None vscode is accepted."""
        repository_project = RepositoryProject(vscode=None)

        assert_that(repository_project.vscode).is_none()
        resolved_folders = repository_project.resolve_folders()
        assert_that(resolved_folders).is_empty()

    def test_repository_project_with_complex_vscode_configuration(self):
        """Test that repository project with complex VSCode configuration works correctly."""
        vscode_folder = VSCodeFolder(
            settings=[
                Folder({"python": [File("base"), File("black")]}),
                Folder({"editor": [File("format")]}),
            ],
            tasks=[
                Folder({"poetry": [File("build"), File("test")]}),
                Folder({"docker": [File("compose")]}),
            ],
        )
        repository_project = RepositoryProject(vscode=vscode_folder)

        resolved_folders = repository_project.resolve_folders()

        assert_that(resolved_folders).is_not_empty()
        assert_that(resolved_folders).is_length(2)

        # Check settings folder
        settings_folder = next(
            f
            for f in resolved_folders
            if f.destination == str(pathlib.Path(".vscode", "settings.json"))
        )
        assert_that(settings_folder.sources).contains(
            str(pathlib.Path("vscode", "settings", "python", "base"))
        )
        assert_that(settings_folder.sources).contains(
            str(pathlib.Path("vscode", "settings", "python", "black"))
        )
        assert_that(settings_folder.sources).contains(
            str(pathlib.Path("vscode", "settings", "editor", "format"))
        )

        # Check tasks folder
        tasks_folder = next(
            f
            for f in resolved_folders
            if f.destination == str(pathlib.Path(".vscode", "tasks.json"))
        )
        assert_that(tasks_folder.sources).contains(
            str(pathlib.Path("vscode", "tasks", "poetry", "build"))
        )
        assert_that(tasks_folder.sources).contains(
            str(pathlib.Path("vscode", "tasks", "poetry", "test"))
        )
        assert_that(tasks_folder.sources).contains(
            str(pathlib.Path("vscode", "tasks", "docker", "compose"))
        )

    def test_repository_project_with_direct_files(self):
        """Test that repository project with direct files in VSCode configuration works correctly."""
        vscode_folder = VSCodeFolder(settings=[File("base")], tasks=[File("build")])
        repository_project = RepositoryProject(vscode=vscode_folder)

        resolved_folders = repository_project.resolve_folders()

        assert_that(resolved_folders).is_not_empty()
        assert_that(resolved_folders).is_length(2)

        # Check settings folder
        settings_folder = next(
            f
            for f in resolved_folders
            if f.destination == str(pathlib.Path(".vscode", "settings.json"))
        )
        assert_that(settings_folder.sources).contains(
            str(pathlib.Path("vscode", "settings", "base"))
        )

        # Check tasks folder
        tasks_folder = next(
            f
            for f in resolved_folders
            if f.destination == str(pathlib.Path(".vscode", "tasks.json"))
        )
        assert_that(tasks_folder.sources).contains(
            str(pathlib.Path("vscode", "tasks", "build"))
        )


class TestRepositoryProjectInheritance:
    """Test cases for RepositoryProject inheritance and model behavior."""

    def test_repository_project_inherits_from_basemodel(self):
        """Test that RepositoryProject inherits from BaseModel."""
        repository_project = RepositoryProject()

        assert_that(repository_project).is_instance_of(RepositoryProject)
        # Check that it has BaseModel methods
        assert_that(hasattr(repository_project, "model_dump")).is_true()
        assert_that(hasattr(repository_project, "model_validate")).is_true()

    def test_repository_project_model_dump(self):
        """Test that RepositoryProject can be serialized correctly."""
        vscode_folder = VSCodeFolder(settings=[Folder({"python": [File("base")]})])
        repository_project = RepositoryProject(vscode=vscode_folder)

        dumped = repository_project.model_dump()

        assert_that(dumped).contains_key("vscode")
        assert_that(dumped["vscode"]).is_not_none()

    def test_repository_project_model_validate(self):
        """Test that RepositoryProject can be validated from dict."""
        data = {
            "vscode": {
                "settings": [{"python": ["base"]}],
                "tasks": [{"poetry": ["build"]}],
            }
        }

        repository_project = RepositoryProject.model_validate(data)

        assert_that(repository_project.vscode).is_not_none()
        assert_that(repository_project.vscode.settings).is_not_none()
        assert_that(repository_project.vscode.tasks).is_not_none()

    def test_repository_project_model_validate_empty(self):
        """Test that RepositoryProject can be validated from empty dict."""
        data = {}

        repository_project = RepositoryProject.model_validate(data)

        assert_that(repository_project.vscode).is_none()


class TestRepositoryProjectComparison:
    """Test cases for RepositoryProject comparison and equality."""

    def test_repository_project_equality_with_same_config(self):
        """Test that two RepositoryProject instances with same config are equal."""
        vscode_folder = VSCodeFolder(settings=[Folder({"python": [File("base")]})])
        project1 = RepositoryProject(vscode=vscode_folder)
        project2 = RepositoryProject(vscode=vscode_folder)

        assert_that(project1).is_equal_to(project2)

    def test_repository_project_equality_without_vscode(self):
        """Test that two RepositoryProject instances without vscode are equal."""
        project1 = RepositoryProject()
        project2 = RepositoryProject()

        assert_that(project1).is_equal_to(project2)

    def test_repository_project_inequality_with_different_config(self):
        """Test that two RepositoryProject instances with different config are not equal."""
        vscode1 = VSCodeFolder(settings=[Folder({"python": [File("base")]})])
        vscode2 = VSCodeFolder(tasks=[Folder({"poetry": [File("build")]})])

        project1 = RepositoryProject(vscode=vscode1)
        project2 = RepositoryProject(vscode=vscode2)

        assert_that(project1).is_not_equal_to(project2)
