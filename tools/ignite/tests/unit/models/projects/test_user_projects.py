import pytest
from pydantic import ValidationError
from assertpy import assert_that

from ignite.models.projects import UserProject
from ignite.models.fs import AbsolutePath, ResolvedFolder
from ignite.models.settings import VSCodeFolder, Folder, File


class TestValidUserProject:
    """Test cases for valid UserProject configurations."""

    def test_minimal_user_project(self):
        """Test that a minimal user project with only path is accepted."""
        user_project = UserProject(path="/workspace/test-project")
        
        assert_that(user_project.path).is_equal_to("/workspace/test-project")
        assert_that(user_project.alias).is_none()
        assert_that(user_project.vscode).is_none()

    def test_user_project_with_alias(self):
        """Test that a user project with alias is accepted."""
        user_project = UserProject(
            path="/workspace/test-project",
            alias="my-project"
        )
        
        assert_that(user_project.path).is_equal_to("/workspace/test-project")
        assert_that(user_project.alias).is_equal_to("my-project")
        assert_that(user_project.vscode).is_none()

    def test_user_project_with_vscode_settings(self):
        """Test that a user project with VSCode settings is accepted."""
        vscode_folder = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})]
        )
        user_project = UserProject(
            path="/workspace/test-project",
            vscode=vscode_folder
        )
        
        assert_that(user_project.path).is_equal_to("/workspace/test-project")
        assert_that(user_project.alias).is_none()
        assert_that(user_project.vscode).is_not_none()
        assert_that(user_project.vscode.settings).is_not_none()

    def test_user_project_with_vscode_tasks(self):
        """Test that a user project with VSCode tasks is accepted."""
        vscode_folder = VSCodeFolder(
            tasks=[Folder({"poetry": [File("build")]})]
        )
        user_project = UserProject(
            path="/workspace/test-project",
            vscode=vscode_folder
        )
        
        assert_that(user_project.path).is_equal_to("/workspace/test-project")
        assert_that(user_project.alias).is_none()
        assert_that(user_project.vscode).is_not_none()
        assert_that(user_project.vscode.tasks).is_not_none()

    def test_user_project_with_all_fields(self):
        """Test that a user project with all fields is accepted."""
        vscode_folder = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})],
            tasks=[Folder({"poetry": [File("build")]})]
        )
        user_project = UserProject(
            path="/workspace/test-project",
            alias="my-project",
            vscode=vscode_folder
        )
        
        assert_that(user_project.path).is_equal_to("/workspace/test-project")
        assert_that(user_project.alias).is_equal_to("my-project")
        assert_that(user_project.vscode).is_not_none()
        assert_that(user_project.vscode.settings).is_not_none()
        assert_that(user_project.vscode.tasks).is_not_none()


class TestUserProjectValidation:
    """Test cases for UserProject validation."""

    def test_user_project_without_path_raises_error(self):
        """Test that user project without path raises validation error."""
        with pytest.raises(ValidationError, match="Field required"):
            UserProject()

    def test_user_project_with_invalid_path_raises_error(self):
        """Test that user project with invalid path raises validation error."""
        with pytest.raises(ValidationError):
            UserProject(path="invalid-path")

    def test_user_project_with_empty_path_raises_error(self):
        """Test that user project with empty path raises validation error."""
        with pytest.raises(ValidationError):
            UserProject(path="")

    def test_user_project_with_invalid_alias_raises_error(self):
        """Test that user project with invalid alias raises validation error."""
        with pytest.raises(ValidationError):
            UserProject(
                path="/workspace/test-project",
                alias="invalid-alias-with-special-chars!"
            )

    def test_user_project_with_empty_alias_raises_error(self):
        """Test that user project with empty alias raises validation error."""
        with pytest.raises(ValidationError):
            UserProject(
                path="/workspace/test-project",
                alias=""
            )

    def test_user_project_with_absolute_path_validation(self):
        """Test that user project accepts valid absolute paths."""
        valid_paths = [
            "/workspace/test-project",
            "/home/user/project",
            "/var/www/html",
            "/tmp/test",
            "/usr/local/bin"
        ]
        
        for path in valid_paths:
            user_project = UserProject(path=path)
            assert_that(user_project.path).is_equal_to(path)

    @pytest.mark.parametrize("relative_path", [
        "workspace/test-project",
        "home/user/project", 
        "var/www/html",
        "tmp/test",
        "usr/local/bin"
    ])
    def test_user_project_with_relative_path_validation(self, relative_path):
        """Test that user project with relative path raises validation error."""
        with pytest.raises(ValidationError):
            UserProject(path=relative_path)

    def test_user_project_with_long_path_raises_error(self):
        """Test that user project with long path raises validation error."""
        long_path = "/" + "/".join(["very", "long", "path", "with", "many", "segments"] * 10)
        
        with pytest.raises(ValidationError):
            UserProject(path=long_path)


class TestUserProjectResolveFoldersMethod:
    """Test cases for the resolve_folders method of UserProject."""

    def test_resolve_folders_without_vscode(self):
        """Test that resolve_folders returns empty list when no vscode is configured."""
        user_project = UserProject(path="/workspace/test-project")
        resolved_folders = user_project.resolve_folders()
        
        assert_that(resolved_folders).is_empty()

    def test_resolve_folders_with_vscode_settings(self):
        """Test that resolve_folders works correctly with VSCode settings."""
        vscode_folder = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})]
        )
        user_project = UserProject(
            path="/workspace/test-project",
            vscode=vscode_folder
        )
        
        resolved_folders = user_project.resolve_folders()
        
        assert_that(resolved_folders).is_not_empty()
        assert_that(resolved_folders).is_length(1)
        
        resolved_folder = resolved_folders[0]
        assert_that(resolved_folder).is_instance_of(ResolvedFolder)
        assert_that(resolved_folder.destination).is_equal_to(".vscode/settings.json")
        assert_that(resolved_folder.sources).contains("vscode/settings/python/base")

    def test_resolve_folders_with_vscode_tasks(self):
        """Test that resolve_folders works correctly with VSCode tasks."""
        vscode_folder = VSCodeFolder(
            tasks=[Folder({"poetry": [File("build")]})]
        )
        user_project = UserProject(
            path="/workspace/test-project",
            vscode=vscode_folder
        )
        
        resolved_folders = user_project.resolve_folders()
        
        assert_that(resolved_folders).is_not_empty()
        assert_that(resolved_folders).is_length(1)
        
        resolved_folder = resolved_folders[0]
        assert_that(resolved_folder).is_instance_of(ResolvedFolder)
        assert_that(resolved_folder.destination).is_equal_to(".vscode/tasks.json")
        assert_that(resolved_folder.sources).contains("vscode/tasks/poetry/build")

    def test_resolve_folders_with_both_settings_and_tasks(self):
        """Test that resolve_folders works correctly with both settings and tasks."""
        vscode_folder = VSCodeFolder(
            settings=[Folder({"python": [File("base")]})],
            tasks=[Folder({"poetry": [File("build")]})]
        )
        user_project = UserProject(
            path="/workspace/test-project",
            vscode=vscode_folder
        )
        
        resolved_folders = user_project.resolve_folders()
        
        assert_that(resolved_folders).is_not_empty()
        assert_that(resolved_folders).is_length(2)
        
        # Check that both settings and tasks are present
        destinations = [folder.destination for folder in resolved_folders]
        assert_that(destinations).contains(".vscode/settings.json")
        assert_that(destinations).contains(".vscode/tasks.json")

    def test_resolve_folders_with_multiple_settings_sources(self):
        """Test that resolve_folders works correctly with multiple settings sources."""
        vscode_folder = VSCodeFolder(
            settings=[
                Folder({"python": [File("base")]}),
                Folder({"typescript": [File("config")]})
            ]
        )
        user_project = UserProject(
            path="/workspace/test-project",
            vscode=vscode_folder
        )
        
        resolved_folders = user_project.resolve_folders()
        
        assert_that(resolved_folders).is_not_empty()
        assert_that(resolved_folders).is_length(1)
        
        resolved_folder = resolved_folders[0]
        assert_that(resolved_folder.destination).is_equal_to(".vscode/settings.json")
        assert_that(resolved_folder.sources).contains("vscode/settings/python/base")
        assert_that(resolved_folder.sources).contains("vscode/settings/typescript/config")


class TestUserProjectEdgeCases:
    """Test cases for edge cases in UserProject."""

    def test_user_project_with_none_vscode(self):
        """Test that user project with None vscode is handled correctly."""
        user_project = UserProject(
            path="/workspace/test-project",
            vscode=None
        )
        
        assert_that(user_project.vscode).is_none()
        resolved_folders = user_project.resolve_folders()
        assert_that(resolved_folders).is_empty()

    def test_user_project_with_none_alias(self):
        """Test that user project with None alias is handled correctly."""
        user_project = UserProject(
            path="/workspace/test-project",
            alias=None
        )
        
        assert_that(user_project.alias).is_none()

    def test_user_project_with_complex_vscode_configuration(self):
        """Test that user project with complex VSCode configuration works correctly."""
        vscode_folder = VSCodeFolder(
            settings=[
                Folder({
                    "python": [File("base"), File("black")],
                    "typescript": [File("config")]
                }),
                Folder({"general": [File("base")]})
            ],
            tasks=[
                Folder({"poetry": [File("build"), File("test")]}),
                Folder({"npm": [File("start")]})
            ]
        )
        user_project = UserProject(
            path="/workspace/test-project",
            alias="complex-project",
            vscode=vscode_folder
        )
        
        resolved_folders = user_project.resolve_folders()
        
        assert_that(resolved_folders).is_length(2)
        
        # Check settings
        settings_folder = next(f for f in resolved_folders if f.destination == ".vscode/settings.json")
        assert_that(settings_folder.sources).contains("vscode/settings/python/base")
        assert_that(settings_folder.sources).contains("vscode/settings/python/black")
        assert_that(settings_folder.sources).contains("vscode/settings/typescript/config")
        assert_that(settings_folder.sources).contains("vscode/settings/general/base")
        
        # Check tasks
        tasks_folder = next(f for f in resolved_folders if f.destination == ".vscode/tasks.json")
        assert_that(tasks_folder.sources).contains("vscode/tasks/poetry/build")
        assert_that(tasks_folder.sources).contains("vscode/tasks/poetry/test")
        assert_that(tasks_folder.sources).contains("vscode/tasks/npm/start")

    def test_user_project_with_root_path(self):
        """Test that user project with root path is accepted."""
        user_project = UserProject(path="/")
        
        assert_that(user_project.path).is_equal_to("/")
        resolved_folders = user_project.resolve_folders()
        assert_that(resolved_folders).is_empty()


class TestUserProjectInheritance:
    """Test cases for UserProject inheritance and model behavior."""

    def test_user_project_inherits_from_basemodel(self):
        """Test that UserProject inherits from BaseModel."""
        user_project = UserProject(path="/workspace/test-project")
        
        # Check that it has BaseModel methods
        assert_that(hasattr(user_project, 'model_dump')).is_true()
        assert_that(hasattr(user_project, 'model_validate')).is_true()

    def test_user_project_model_dump(self):
        """Test that UserProject model_dump works correctly."""
        user_project = UserProject(
            path="/workspace/test-project",
            alias="my-project"
        )
        
        data = user_project.model_dump()
        
        assert_that(data).contains_key("path")
        assert_that(data).contains_key("alias")
        assert_that(data).contains_key("vscode")
        assert_that(data["path"]).is_equal_to("/workspace/test-project")
        assert_that(data["alias"]).is_equal_to("my-project")
        assert_that(data["vscode"]).is_none()

    def test_user_project_model_validate(self):
        """Test that UserProject model_validate works correctly."""
        data = {
            "path": "/workspace/test-project",
            "alias": "my-project"
        }
        
        user_project = UserProject.model_validate(data)
        
        assert_that(user_project.path).is_equal_to("/workspace/test-project")
        assert_that(user_project.alias).is_equal_to("my-project")
        assert_that(user_project.vscode).is_none()
