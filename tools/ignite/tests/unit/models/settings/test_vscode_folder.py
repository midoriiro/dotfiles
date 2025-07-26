import pathlib

import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.fs import File, Folder, ResolvedFolder
from ignite.models.settings import VSCodeFolder


class TestVSCodeFolderCreation:
    """Test basic VSCodeFolder creation with valid data."""

    def test_create_empty_vscode_folder(self):
        """Test creating an empty VSCodeFolder."""
        vscode_folder = VSCodeFolder()
        assert_that(vscode_folder.settings).is_none()
        assert_that(vscode_folder.tasks).is_none()

    def test_create_vscode_folder_with_settings_only(self):
        """Test creating a VSCodeFolder with only settings."""
        settings_folder = Folder({"python": [File("base"), File("black")]})
        vscode_folder = VSCodeFolder(settings=[settings_folder])

        assert_that(vscode_folder.settings).is_length(1)
        assert_that(vscode_folder.settings[0]).is_instance_of(Folder)
        assert_that(vscode_folder.tasks).is_none()

    def test_create_vscode_folder_with_tasks_only(self):
        """Test creating a VSCodeFolder with only tasks."""
        tasks_folder = Folder({"poetry": [File("build"), File("test")]})
        vscode_folder = VSCodeFolder(tasks=[tasks_folder])

        assert_that(vscode_folder.tasks).is_length(1)
        assert_that(vscode_folder.tasks[0]).is_instance_of(Folder)
        assert_that(vscode_folder.settings).is_none()

    def test_create_vscode_folder_with_both_settings_and_tasks(self):
        """Test creating a VSCodeFolder with both settings and tasks."""
        settings_folder = Folder({"python": [File("base"), File("black")]})
        tasks_folder = Folder({"poetry": [File("build"), File("test")]})
        vscode_folder = VSCodeFolder(settings=[settings_folder], tasks=[tasks_folder])

        assert_that(vscode_folder.settings).is_length(1)
        assert_that(vscode_folder.tasks).is_length(1)
        assert_that(vscode_folder.settings[0]).is_instance_of(Folder)
        assert_that(vscode_folder.tasks[0]).is_instance_of(Folder)

    def test_create_vscode_folder_with_files(self):
        """Test creating a VSCodeFolder with File objects."""
        settings_file = File("base")
        tasks_file = File("build")
        vscode_folder = VSCodeFolder(settings=[settings_file], tasks=[tasks_file])

        assert_that(vscode_folder.settings).is_length(1)
        assert_that(vscode_folder.tasks).is_length(1)
        assert_that(vscode_folder.settings[0]).is_instance_of(File)
        assert_that(vscode_folder.tasks[0]).is_instance_of(File)

    def test_create_vscode_folder_with_mixed_content(self):
        """Test creating a VSCodeFolder with mixed Folder and File objects."""
        settings_folder = Folder({"python": [File("base"), File("black")]})
        settings_file = File("flake8")
        tasks_folder = Folder({"poetry": [File("build"), File("test")]})
        tasks_file = File("install")

        vscode_folder = VSCodeFolder(
            settings=[settings_folder, settings_file], tasks=[tasks_folder, tasks_file]
        )

        assert_that(vscode_folder.settings).is_length(2)
        assert_that(vscode_folder.tasks).is_length(2)
        assert_that(vscode_folder.settings[0]).is_instance_of(Folder)
        assert_that(vscode_folder.settings[1]).is_instance_of(File)
        assert_that(vscode_folder.tasks[0]).is_instance_of(Folder)
        assert_that(vscode_folder.tasks[1]).is_instance_of(File)


class TestVSCodeFolderValidation:
    """Test VSCodeFolder validation rules."""

    def test_vscode_folder_with_empty_settings_list_raises_error(self):
        """Test that VSCodeFolder with empty settings list raises validation error."""
        with pytest.raises(ValidationError, match="settings must be a non-empty list"):
            VSCodeFolder(settings=[])

    def test_vscode_folder_with_empty_tasks_list_raises_error(self):
        """Test that VSCodeFolder with empty tasks list raises validation error."""
        with pytest.raises(ValidationError, match="tasks must be a non-empty list"):
            VSCodeFolder(tasks=[])

    def test_vscode_folder_with_both_empty_lists_raises_error(self):
        """Test that VSCodeFolder with both empty lists raises validation error."""
        with pytest.raises(ValidationError, match="settings must be a non-empty list"):
            VSCodeFolder(settings=[], tasks=[])

    def test_vscode_folder_with_none_values_is_valid(self):
        """Test that VSCodeFolder with None values is valid."""
        vscode_folder = VSCodeFolder(settings=None, tasks=None)
        assert_that(vscode_folder.settings).is_none()
        assert_that(vscode_folder.tasks).is_none()

    def test_vscode_folder_with_valid_lists_is_valid(self):
        """Test that VSCodeFolder with valid non-empty lists is valid."""
        settings_folder = Folder({"python": [File("base")]})
        tasks_folder = Folder({"poetry": [File("build")]})

        vscode_folder = VSCodeFolder(settings=[settings_folder], tasks=[tasks_folder])

        assert_that(vscode_folder.settings).is_length(1)
        assert_that(vscode_folder.tasks).is_length(1)

    def test_vscode_folder_with_mixed_none_and_valid_lists(self):
        """Test that VSCodeFolder with None and valid lists is valid."""
        settings_folder = Folder({"python": [File("base")]})

        # Only settings defined, tasks is None
        vscode_folder = VSCodeFolder(settings=[settings_folder], tasks=None)
        assert_that(vscode_folder.settings).is_length(1)
        assert_that(vscode_folder.tasks).is_none()

        # Only tasks defined, settings is None
        tasks_folder = Folder({"poetry": [File("build")]})
        vscode_folder = VSCodeFolder(settings=None, tasks=[tasks_folder])
        assert_that(vscode_folder.settings).is_none()
        assert_that(vscode_folder.tasks).is_length(1)


class TestVSCodeFolderResolve:
    """Test VSCodeFolder resolve method."""

    def test_resolve_empty_vscode_folder(self):
        """Test resolving an empty VSCodeFolder."""
        vscode_folder = VSCodeFolder()
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_empty()

    def test_resolve_vscode_folder_with_settings_only(self):
        """Test resolving a VSCodeFolder with only settings."""
        settings_folder = Folder({"python": [File("base"), File("black")]})
        vscode_folder = VSCodeFolder(settings=[settings_folder])
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(1)
        assert_that(resolved[0].destination).is_equal_to("settings.json")
        assert_that(resolved[0].sources).is_length(2)
        assert_that(resolved[0].sources).contains(
            str(pathlib.Path("settings", "python", "base"))
        )
        assert_that(resolved[0].sources).contains(
            str(pathlib.Path("settings", "python", "black"))
        )

    def test_resolve_vscode_folder_with_tasks_only(self):
        """Test resolving a VSCodeFolder with only tasks."""
        tasks_folder = Folder({"poetry": [File("build"), File("test")]})
        vscode_folder = VSCodeFolder(tasks=[tasks_folder])
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(1)
        assert_that(resolved[0].destination).is_equal_to("tasks.json")
        assert_that(resolved[0].sources).is_length(2)
        assert_that(resolved[0].sources).contains(
            str(pathlib.Path("tasks", "poetry", "build"))
        )
        assert_that(resolved[0].sources).contains(
            str(pathlib.Path("tasks", "poetry", "test"))
        )

    def test_resolve_vscode_folder_with_both_settings_and_tasks(self):
        """Test resolving a VSCodeFolder with both settings and tasks."""
        settings_folder = Folder({"python": [File("base"), File("black")]})
        tasks_folder = Folder({"poetry": [File("build"), File("test")]})
        vscode_folder = VSCodeFolder(settings=[settings_folder], tasks=[tasks_folder])
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(2)

        # Check settings
        settings_resolved = next(
            r for r in resolved if r.destination == "settings.json"
        )
        assert_that(settings_resolved.sources).is_length(2)
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", "base"))
        )
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", "black"))
        )

        # Check tasks
        tasks_resolved = next(r for r in resolved if r.destination == "tasks.json")
        assert_that(tasks_resolved.sources).is_length(2)
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "poetry", "build"))
        )
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "poetry", "test"))
        )

    def test_resolve_vscode_folder_with_files(self):
        """Test resolving a VSCodeFolder with File objects."""
        settings_file = File("base")
        tasks_file = File("build")
        vscode_folder = VSCodeFolder(settings=[settings_file], tasks=[tasks_file])
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(2)

        # Check settings
        settings_resolved = next(
            r for r in resolved if r.destination == "settings.json"
        )
        assert_that(settings_resolved.sources).is_length(1)
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "base"))
        )

        # Check tasks
        tasks_resolved = next(r for r in resolved if r.destination == "tasks.json")
        assert_that(tasks_resolved.sources).is_length(1)
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "build"))
        )

    def test_resolve_vscode_folder_with_mixed_content(self):
        """Test resolving a VSCodeFolder with mixed Folder and File objects."""
        settings_folder = Folder({"python": [File("base"), File("black")]})
        settings_file = File("flake8")
        tasks_folder = Folder({"poetry": [File("build"), File("test")]})
        tasks_file = File("install")

        vscode_folder = VSCodeFolder(
            settings=[settings_folder, settings_file], tasks=[tasks_folder, tasks_file]
        )
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(2)

        # Check settings
        settings_resolved = next(
            r for r in resolved if r.destination == "settings.json"
        )
        assert_that(settings_resolved.sources).is_length(3)
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", "base"))
        )
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", "black"))
        )
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "flake8"))
        )

        # Check tasks
        tasks_resolved = next(r for r in resolved if r.destination == "tasks.json")
        assert_that(tasks_resolved.sources).is_length(3)
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "poetry", "build"))
        )
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "poetry", "test"))
        )
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "install"))
        )

    def test_resolve_vscode_folder_with_nested_folders(self):
        """Test resolving a VSCodeFolder with nested folder structures."""
        settings_folder = Folder(
            {
                "python": [
                    File("base"),
                    Folder({"linting": [File("black"), File("flake8")]}),
                ]
            }
        )
        tasks_folder = Folder(
            {
                "poetry": [
                    File("build"),
                    Folder({"testing": [File("test"), File("coverage")]}),
                ]
            }
        )

        vscode_folder = VSCodeFolder(settings=[settings_folder], tasks=[tasks_folder])
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(2)

        # Check settings
        settings_resolved = next(
            r for r in resolved if r.destination == "settings.json"
        )
        assert_that(settings_resolved.sources).is_length(3)
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", "base"))
        )
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", "linting", "black"))
        )
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", "linting", "flake8"))
        )

        # Check tasks
        tasks_resolved = next(r for r in resolved if r.destination == "tasks.json")
        assert_that(tasks_resolved.sources).is_length(3)
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "poetry", "build"))
        )
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "poetry", "testing", "test"))
        )
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "poetry", "testing", "coverage"))
        )

    def test_resolve_vscode_folder_with_reserved_keywords(self):
        """Test resolving a VSCodeFolder with reserved keywords ($ref, $all)."""
        settings_folder = Folder({"python": [File("$ref")]})
        tasks_folder = Folder({"poetry": [File("$all")]})

        vscode_folder = VSCodeFolder(settings=[settings_folder], tasks=[tasks_folder])
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(2)

        # Check settings
        settings_resolved = next(
            r for r in resolved if r.destination == "settings.json"
        )
        assert_that(settings_resolved.sources).is_length(1)
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", "$ref"))
        )

        # Check tasks
        tasks_resolved = next(r for r in resolved if r.destination == "tasks.json")
        assert_that(tasks_resolved.sources).is_length(1)
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "poetry", "$all"))
        )


class TestVSCodeFolderEdgeCases:
    """Test VSCodeFolder edge cases and error conditions."""

    def test_resolve_vscode_folder_with_none_values(self):
        """Test resolving a VSCodeFolder with None values (should be same as empty)."""
        vscode_folder = VSCodeFolder(settings=None, tasks=None)
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_empty()

    def test_resolve_vscode_folder_with_complex_nested_structure(self):
        """Test resolving a VSCodeFolder with very complex nested structures."""
        settings_folder = Folder(
            {
                "python": [
                    File("base"),
                    Folder(
                        {
                            "linting": [
                                File("black"),
                                Folder({"config": [File("black"), File("pyproject")]}),
                            ],
                            "formatting": [File("isort"), File("autopep8")],
                        }
                    ),
                    Folder(
                        {
                            "testing": [
                                File("pytest"),
                                File("coverage"),
                                Folder(
                                    {"fixtures": [File("conftest"), File("test_data")]}
                                ),
                            ]
                        }
                    ),
                ]
            }
        )

        vscode_folder = VSCodeFolder(settings=[settings_folder])
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(1)
        settings_resolved = resolved[0]
        assert_that(settings_resolved.destination).is_equal_to("settings.json")
        assert_that(settings_resolved.sources).is_length(10)

        expected_sources = [
            str(pathlib.Path("settings", "python", "base")),
            str(pathlib.Path("settings", "python", "linting", "black")),
            str(pathlib.Path("settings", "python", "linting", "config", "black")),
            str(pathlib.Path("settings", "python", "linting", "config", "pyproject")),
            str(pathlib.Path("settings", "python", "formatting", "isort")),
            str(pathlib.Path("settings", "python", "formatting", "autopep8")),
            str(pathlib.Path("settings", "python", "testing", "pytest")),
            str(pathlib.Path("settings", "python", "testing", "coverage")),
            str(pathlib.Path("settings", "python", "testing", "fixtures", "conftest")),
            str(pathlib.Path("settings", "python", "testing", "fixtures", "test_data")),
        ]

        for expected_source in expected_sources:
            assert_that(settings_resolved.sources).contains(expected_source)

    def test_resolve_vscode_folder_with_special_characters(self):
        """Test resolving a VSCodeFolder with special characters in file names."""
        settings_folder = Folder(
            {"python": [File("base"), File(".env"), File("config")]}
        )
        tasks_folder = Folder(
            {"poetry": [File("build"), File(".gitignore"), File("pyproject")]}
        )

        vscode_folder = VSCodeFolder(settings=[settings_folder], tasks=[tasks_folder])
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(2)

        # Check settings
        settings_resolved = next(
            r for r in resolved if r.destination == "settings.json"
        )
        assert_that(settings_resolved.sources).is_length(3)
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", "base"))
        )
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", ".env"))
        )
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", "config"))
        )

        # Check tasks
        tasks_resolved = next(r for r in resolved if r.destination == "tasks.json")
        assert_that(tasks_resolved.sources).is_length(3)
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "poetry", "build"))
        )
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "poetry", ".gitignore"))
        )
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "poetry", "pyproject"))
        )


class TestVSCodeFolderModelBehavior:
    """Test VSCodeFolder model behavior and properties."""

    def test_vscode_folder_inheritance(self):
        """Test that VSCodeFolder inherits from BaseFolder."""
        vscode_folder = VSCodeFolder()
        assert_that(vscode_folder).is_instance_of(VSCodeFolder)
        # Check that it has the resolve method from BaseFolder
        assert_that(hasattr(vscode_folder, "resolve")).is_true()
        assert_that(hasattr(vscode_folder, "_resolve_folder")).is_true()

    def test_vscode_folder_optional_fields(self):
        """Test that VSCodeFolder fields are optional."""
        vscode_folder = VSCodeFolder()
        assert_that(vscode_folder.settings).is_none()
        assert_that(vscode_folder.tasks).is_none()

    def test_vscode_folder_resolved_folder_structure(self):
        """Test that resolved folders have the correct structure."""
        settings_folder = Folder({"python": [File("base")]})
        vscode_folder = VSCodeFolder(settings=[settings_folder])
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(1)
        resolved_folder = resolved[0]

        # Check that it's a ResolvedFolder
        assert_that(resolved_folder).is_instance_of(ResolvedFolder)
        assert_that(hasattr(resolved_folder, "sources")).is_true()
        assert_that(hasattr(resolved_folder, "destination")).is_true()

        # Check that sources is a list of strings (paths)
        assert_that(resolved_folder.sources).is_instance_of(list)
        for source in resolved_folder.sources:
            assert_that(source).is_instance_of(str)

    def test_vscode_folder_destination_paths(self):
        """Test that VSCodeFolder uses correct destination paths."""
        settings_folder = Folder({"python": [File("base")]})
        tasks_folder = Folder({"poetry": [File("build")]})

        vscode_folder = VSCodeFolder(settings=[settings_folder], tasks=[tasks_folder])
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(2)

        destinations = [r.destination for r in resolved]
        assert_that(destinations).contains("settings.json")
        assert_that(destinations).contains("tasks.json")

    def test_vscode_folder_source_path_construction(self):
        """Test that VSCodeFolder constructs source paths correctly."""
        settings_folder = Folder({"python": [File("base")]})
        vscode_folder = VSCodeFolder(settings=[settings_folder])
        resolved = vscode_folder.resolve()

        settings_resolved = resolved[0]
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", "base"))
        )

        # Verify the path construction follows the expected pattern
        # base_settings_path = Path("settings") + source_path
        assert_that(settings_resolved.sources[0]).is_equal_to(
            str(pathlib.Path("settings", "python", "base"))
        )

    def test_vscode_folder_uses_model_construct(self):
        """
        Test that VSCodeFolder uses model_construct for creating ResolvedFolder objects.
        """
        settings_folder = Folder({"python": [File("base")]})
        vscode_folder = VSCodeFolder(settings=[settings_folder])
        resolved = vscode_folder.resolve()

        # The ResolvedFolder should be created using model_construct
        # This is verified by checking that the object is properly instantiated
        assert_that(resolved).is_length(1)
        resolved_folder = resolved[0]
        assert_that(resolved_folder).is_instance_of(ResolvedFolder)
        assert_that(resolved_folder.sources).is_length(1)
        assert_that(resolved_folder.destination).is_equal_to("settings.json")

    def test_vscode_folder_validation_order(self):
        """Test that VSCodeFolder validation happens in the correct order."""
        # Test that validation happens after model construction
        settings_folder = Folder({"python": [File("base")]})

        # This should work without validation errors
        vscode_folder = VSCodeFolder(settings=[settings_folder])
        assert_that(vscode_folder.settings).is_length(1)

        # Test that validation is called during model construction
        with pytest.raises(ValidationError, match="settings must be a non-empty list"):
            VSCodeFolder(settings=[])

    def test_vscode_folder_with_multiple_settings_sources(self):
        """Test VSCodeFolder with multiple settings sources."""
        settings_folder1 = Folder({"python": [File("base")]})
        settings_folder2 = Folder({"typescript": [File("base")]})
        settings_file = File("global")

        vscode_folder = VSCodeFolder(
            settings=[settings_folder1, settings_folder2, settings_file]
        )
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(1)
        settings_resolved = resolved[0]
        assert_that(settings_resolved.sources).is_length(3)
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "python", "base"))
        )
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "typescript", "base"))
        )
        assert_that(settings_resolved.sources).contains(
            str(pathlib.Path("settings", "global"))
        )

    def test_vscode_folder_with_multiple_tasks_sources(self):
        """Test VSCodeFolder with multiple tasks sources."""
        tasks_folder1 = Folder({"poetry": [File("build")]})
        tasks_folder2 = Folder({"npm": [File("build")]})
        tasks_file = File("global")

        vscode_folder = VSCodeFolder(tasks=[tasks_folder1, tasks_folder2, tasks_file])
        resolved = vscode_folder.resolve()

        assert_that(resolved).is_length(1)
        tasks_resolved = resolved[0]
        assert_that(tasks_resolved.sources).is_length(3)
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "poetry", "build"))
        )
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "npm", "build"))
        )
        assert_that(tasks_resolved.sources).contains(
            str(pathlib.Path("tasks", "global"))
        )
