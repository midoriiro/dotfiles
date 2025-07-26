import pathlib

import pytest
from assertpy import assert_that

from ignite.models.fs import File, Folder


class TestFolderCreation:
    """Test basic folder creation with valid data."""

    def test_create_simple_folder_with_files(self):
        """Test creating a folder with simple files."""
        folder = Folder({"config": [File("config"), File(".env")]})
        assert_that(folder.root).is_equal_to({"config": [File("config"), File(".env")]})

    def test_create_folder_with_subfolders(self):
        """Test creating a folder with nested subfolders."""
        folder = Folder({"src": [File("main"), Folder({"utils": [File("helper")]})]})
        assert_that(folder.root).is_equal_to(
            {"src": [File("main"), Folder({"utils": [File("helper")]})]}
        )

    def test_create_complex_nested_structure(self):
        """Test creating a complex nested folder structure."""
        folder = Folder(
            {
                "src": [
                    File("main"),
                    File("$ref"),
                    Folder(
                        {
                            "utils": [
                                File("helper"),
                                File(".config"),
                                Folder({"internal": [File("$all")]}),
                            ]
                        }
                    ),
                ],
                "tests": [
                    File("test_main"),
                    Folder(
                        {
                            "unit": [File("test_utils")],
                            "integration": [File("test_api")],
                        }
                    ),
                ],
            }
        )
        assert_that(len(folder.root)).is_equal_to(2)
        assert_that("src" in folder.root).is_true()
        assert_that("tests" in folder.root).is_true()


class TestFolderValidation:
    """Test folder validation rules."""

    def test_folder_must_contain_at_least_one_file(self):
        """Test that folder must contain at least one file."""
        with pytest.raises(
            ValueError, match="Folder must contain at least one file or one subfolder"
        ):
            Folder({"empty": []})

    def test_folder_with_only_subfolders_raises_error(self):
        """Test that folder with only subfolders raises error."""
        with pytest.raises(
            ValueError, match="Folder must contain at least one file or one subfolder"
        ):
            Folder({"src": [Folder({"utils": []})]})

    def test_reserved_keywords_cannot_be_folder_names(self):
        """Test that reserved keywords cannot be used as folder names."""
        with pytest.raises(ValueError, match="should match pattern"):
            Folder(
                {
                    "src": [
                        File("main"),
                        Folder({"$ref": [File("config")]}),
                        Folder({"$all": [File("data")]}),
                    ]
                }
            )

    def test_folder_names_must_be_unique(self):
        """Test that folder names must be unique within the same level."""
        with pytest.raises(ValueError, match="Folder names must be unique"):
            Folder(
                {
                    "src": [
                        File("main"),
                        Folder({"utils": [File("helper")]}),
                        Folder({"utils": [File("another")]}),
                    ]
                }
            )

    def test_file_names_must_be_unique(self):
        """Test that file names must be unique (excluding reserved keywords)."""
        with pytest.raises(ValueError, match="File names must be unique"):
            Folder({"src": [File("main"), File("main")]})

    def test_user_files_must_be_unique(self):
        """Test that user files (starting with dot) must be unique."""
        with pytest.raises(ValueError, match="File names must be unique"):
            Folder({"config": [File(".env"), File(".env")]})

    def test_repository_files_must_be_unique(self):
        """Test that repository files must be unique."""
        with pytest.raises(ValueError, match="File names must be unique"):
            Folder({"src": [File("config"), File("config")]})


class TestReservedKeywordsValidation:
    """Test validation rules for reserved keywords."""

    def test_ref_cannot_be_defined_more_than_once(self):
        """Test that $ref cannot be defined more than once."""
        with pytest.raises(ValueError, match="\\$ref cannot be defined more than once"):
            Folder({"src": [File("$ref"), File("$ref")]})

    def test_all_cannot_be_defined_more_than_once(self):
        """Test that $all cannot be defined more than once."""
        with pytest.raises(
            ValueError, match="'\\$all' cannot be defined more than once"
        ):
            Folder({"src": [File("$all"), File("$all")]})

    def test_ref_and_all_cannot_be_defined_simultaneously(self):
        """Test that $ref and $all cannot be defined simultaneously."""
        with pytest.raises(
            ValueError, match="'\\$ref' and '\\$all' cannot be defined simultaneously"
        ):
            Folder({"src": [File("$ref"), File("$all")]})

    def test_all_cannot_be_defined_with_repository_files(self):
        """Test that $all cannot be defined simultaneously with repository files."""
        with pytest.raises(
            ValueError,
            match="'\\$all' cannot be defined simultaneously with repository files",
        ):
            Folder({"src": [File("$all"), File("config")]})

    def test_all_can_be_defined_with_user_files(self):
        """Test that $all can be defined with user files."""
        folder = Folder({"src": [File("$all"), File(".env")]})
        assert_that(folder.root).is_equal_to({"src": [File("$all"), File(".env")]})

    def test_ref_can_be_defined_with_repository_files(self):
        """Test that $ref can be defined with repository files."""
        folder = Folder({"src": [File("$ref"), File("config")]})
        assert_that(folder.root).is_equal_to({"src": [File("$ref"), File("config")]})

    def test_ref_can_be_defined_with_user_files(self):
        """Test that $ref can be defined with user files."""
        folder = Folder({"src": [File("$ref"), File(".env")]})
        assert_that(folder.root).is_equal_to({"src": [File("$ref"), File(".env")]})


class TestFolderResolve:
    """Test the resolve method of Folder class."""

    def test_resolve_simple_folder(self):
        """Test resolving a simple folder with files."""
        folder = Folder({"config": [File("config"), File(".env")]})
        paths = folder.resolve()
        expected_paths = [
            pathlib.Path("config", "config"),
            pathlib.Path("config", ".env"),
        ]
        assert_that(paths).is_equal_to(expected_paths)

    def test_resolve_folder_with_subfolders(self):
        """Test resolving a folder with nested subfolders."""
        folder = Folder({"src": [File("main"), Folder({"utils": [File("helper")]})]})
        paths = folder.resolve()
        expected_paths = [
            pathlib.Path("src", "main"),
            pathlib.Path("src", "utils", "helper"),
        ]
        assert_that(paths).is_equal_to(expected_paths)

    def test_resolve_complex_nested_structure(self):
        """Test resolving a complex nested folder structure."""
        folder = Folder(
            {
                "src": [
                    File("main"),
                    Folder(
                        {
                            "utils": [
                                File("helper"),
                                Folder({"internal": [File("core")]}),
                            ]
                        }
                    ),
                ],
                "tests": [
                    File("test_main"),
                    Folder(
                        {
                            "unit": [File("test_utils")],
                            "integration": [File("test_api")],
                        }
                    ),
                ],
            }
        )
        paths = folder.resolve()
        expected_paths = [
            pathlib.Path("src", "main"),
            pathlib.Path("src", "utils", "helper"),
            pathlib.Path("src", "utils", "internal", "core"),
            pathlib.Path("tests", "test_main"),
            pathlib.Path("tests", "unit", "test_utils"),
            pathlib.Path("tests", "integration", "test_api"),
        ]
        assert_that(paths).is_equal_to(expected_paths)

    def test_resolve_with_ref_reserved_keywords(self):
        """Test resolving a folder with ref reserved keyword."""
        folder = Folder({"src": [File("$ref"), File("config")]})
        paths = folder.resolve()
        expected_paths = [pathlib.Path("src", "$ref"), pathlib.Path("src", "config")]
        assert_that(paths).is_equal_to(expected_paths)

    def test_resolve_with_all_reserved_keyword(self):
        """Test resolving a folder with all reserved keyword."""
        folder = Folder(
            {
                "src": [
                    File("$all"),
                ]
            }
        )
        paths = folder.resolve()
        expected_paths = [
            pathlib.Path("src", "$all"),
        ]
        assert_that(paths).is_equal_to(expected_paths)

    def test_resolve_multiple_folders(self):
        """Test resolving multiple folders at the same level."""
        folder = Folder(
            {
                "src": [File("main")],
                "tests": [File("test_main")],
                "docs": [File("README")],
            }
        )
        paths = folder.resolve()
        expected_paths = [
            pathlib.Path("src", "main"),
            pathlib.Path("tests", "test_main"),
            pathlib.Path("docs", "README"),
        ]
        assert_that(paths).is_equal_to(expected_paths)


class TestFolderEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_folder_with_mixed_file_types(self):
        """Test folder with mixed file types (repository, user, reserved)."""
        folder = Folder(
            {
                "config": [
                    File("config"),  # repository file
                    File(".env"),  # user file
                    File("$ref"),  # reserved file
                ]
            }
        )
        paths = folder.resolve()
        expected_paths = [
            pathlib.Path("config", "config"),
            pathlib.Path("config", ".env"),
            pathlib.Path("config", "$ref"),
        ]
        assert_that(paths).is_equal_to(expected_paths)

    def test_deep_nested_structure(self):
        """Test very deep nested folder structure."""
        folder = Folder(
            {
                "level1": [
                    Folder(
                        {
                            "level2": [
                                Folder(
                                    {
                                        "level3": [
                                            Folder({"level4": [File("deep_file")]})
                                        ]
                                    }
                                )
                            ]
                        }
                    )
                ]
            }
        )
        paths = folder.resolve()
        expected_paths = [
            pathlib.Path("level1", "level2", "level3", "level4", "deep_file")
        ]
        assert_that(paths).is_equal_to(expected_paths)

    def test_folder_with_special_characters_in_names(self):
        """Test folder with special characters in file names."""
        folder = Folder(
            {"src": [File("main-file"), File("config_file"), File(".env_file")]}
        )
        paths = folder.resolve()
        expected_paths = [
            pathlib.Path("src", "main-file"),
            pathlib.Path("src", "config_file"),
            pathlib.Path("src", ".env_file"),
        ]
        assert_that(paths).is_equal_to(expected_paths)

    def test_empty_folder_validation(self):
        """Test that empty folder raises validation error."""
        with pytest.raises(ValueError, match="Folder must contain at least one file"):
            Folder({})

    def test_folder_with_only_empty_subfolders(self):
        """Test folder with only empty subfolders raises error."""
        with pytest.raises(ValueError, match="Folder must contain at least one file"):
            Folder({"src": [Folder({"utils": []})]})


class TestFolderModelBehavior:
    """Test Folder model behavior and properties."""

    def test_folder_root_property(self):
        """Test that folder.root returns the underlying dictionary."""
        data = {"src": [File("main")], "tests": [File("test_main")]}
        folder = Folder(data)
        assert_that(folder.root).is_equal_to(data)

    def test_folder_equality(self):
        """Test folder equality comparison."""
        folder1 = Folder({"src": [File("main")]})
        folder2 = Folder({"src": [File("main")]})
        assert_that(folder1).is_equal_to(folder2)

    def test_folder_inequality(self):
        """Test folder inequality comparison."""
        folder1 = Folder({"src": [File("main")]})
        folder2 = Folder({"src": [File("different")]})
        assert_that(folder1).is_not_equal_to(folder2)

    def test_folder_string_representation(self):
        """Test folder string representation."""
        folder = Folder({"src": [File("main")]})
        # The string representation should contain the folder structure
        str_repr = str(folder)
        assert_that(str_repr).contains("src")
        assert_that(str_repr).contains("main")
