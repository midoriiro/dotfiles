import pytest
from pydantic import BaseModel, ValidationError
from assertpy import assert_that

from ignite.models.fs import RelativePath


class TestModel(BaseModel):
    """Test model with RelativePath field."""
    path: RelativePath


class TestValidRelativePaths:
    """Test valid relative path patterns."""

    @pytest.mark.parametrize("path", [
        "home",
        "usr",
        "var",
        "tmp",
        "etc",
        "bin",
        "sbin",
        "opt",
        "data",
        "workspace"
    ])
    def test_single_level(self, path):
        """Test that single level paths are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize("path", [
        "home/user",
        "usr/local/bin",
        "var/log/app",
        "tmp/data/files",
        "etc/nginx/conf.d",
        "opt/applications/tools",
        "data/projects/workspace",
        "workspace/projects/src",
        "home/user/documents/files",
        "usr/share/applications"
    ])
    def test_multiple_levels(self, path):
        """Test that multi-level paths are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize("path", [
        "home/user123",
        "var/log/app2",
        "tmp/data2023",
        "etc/nginx1",
        "opt/app2",
        "data/project1",
        "workspace/v2",
        "home/user/documents2023"
    ])
    def test_with_numbers(self, path):
        """Test that paths with numbers are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize("path", [
        "home/user_name",
        "var/log/app_name",
        "tmp/data_files",
        "etc/nginx_config",
        "opt/my_app",
        "data/project_name",
        "workspace/src_code",
        "home/user/documents_backup"
    ])
    def test_with_underscores(self, path):
        """Test that paths with underscores are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize("path", [
        "home/user-name",
        "var/log/app-name",
        "tmp/data-files",
        "etc/nginx-config",
        "opt/my-app",
        "data/project-name",
        "workspace/src-code",
        "home/user/documents-backup"
    ])
    def test_with_hyphens(self, path):
        """Test that paths with hyphens are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize("path", [
        "home/user.name",
        "var/log/app.name",
        "tmp/data.files",
        "etc/nginx.config",
        "opt/my.app",
        "data/project.name",
        "workspace/src.code",
        "home/user/documents.backup"
    ])
    def test_with_dots(self, path):
        """Test that paths with dots are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize("path", [
        "home/user-name_123",
        "var/log/app-name_v2",
        "tmp/data-files_2023",
        "etc/nginx-config.prod",
        "opt/my-app_1.0",
        "data/project-name_v1.2",
        "workspace/src-code_alpha",
        "home/user/documents-backup_2023"
    ])
    def test_mixed_characters(self, path):
        """Test that paths with mixed characters are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize("path", [
        "home user",
        "var log",
        "tmp data",
        "etc nginx",
        "opt app",
        "data project",
        "workspace src",
        "home/user name",
        "var/log app name",
        "tmp/data files",
        "etc/nginx config",
        "opt/my app",
        "data/project name",
        "workspace/src code"
    ])
    def test_with_spaces(self, path):
        """Test that paths with spaces are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize("path", [
        "hômé",
        "üsér",
        "vär",
        "tëmp",
        "étc",
        "ôpt",
        "dätä",
        "wörkspäce",
        "home/usér",
        "var/lôg",
        "tmp/dätä",
        "etc/ngînx",
        "opt/äpp",
        "data/prôject",
        "workspace/srç"
    ])
    def test_unicode_characters(self, path):
        """Test that paths with unicode characters are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize("path", [
        "home/",
        "usr/local/",
        "var/log/",
        "tmp/data/",
        "etc/nginx/",
        "opt/app/",
        "data/project/",
        "workspace/src/"
    ])
    def test_trailing_slash(self, path):
        """Test that trailing slash is valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)


class TestInvalidRelativePaths:
    """Test invalid relative path patterns."""

    def test_empty_string(self):
        """Test that empty string is invalid."""
        with pytest.raises(ValidationError, match="cannot be whitespace-only"):
            TestModel(path="")

    @pytest.mark.parametrize("path", [
        "/home",
        "/usr/local",
        "/var/log",
        "/tmp/data",
        "/etc/nginx",
        "/opt/app",
        "/data/project",
        "/workspace/src",
        "/",
        "//home",
        "/home//user"
    ])
    def test_leading_slash(self, path):
        """Test that paths with leading slash are invalid."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(path=path)

    @pytest.mark.parametrize("path", [
        "home@user",
        "var#log",
        "tmp$data",
        "etc%nginx",
        "opt&app",
        "data*project",
        "workspace+src",
        "home=user",
        "var?log",
        "tmp!data",
        "etc|nginx",
        "opt~app",
        "data`project",
        "workspace'src",
        'home"user',
        "var(log)",
        "tmp[data]",
        "etc{nginx}",
        "opt<app>",
        "data;project",
        "workspace:src",
        "home,user"
    ])
    def test_special_characters(self, path):
        """Test that paths with special characters are invalid."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(path=path)

    @pytest.mark.parametrize("path", [
        " ",
        "  ",
        "\t",
        "\n",
        "\r",
        " \t\n\r"
    ])
    def test_whitespace_only(self, path):
        """Test that whitespace-only paths are invalid."""
        with pytest.raises(ValidationError, match="cannot be whitespace-only"):
            TestModel(path=path)

    def test_too_long(self):
        """Test that paths exceeding max_length (256) are invalid."""
        # Create a path that exceeds 256 characters
        long_component = "a" * 300
        long_path = f"{long_component}"
        
        with pytest.raises(ValidationError, match="should have at most 256"):
            TestModel(path=long_path)


class TestEdgeCases:
    """Test edge cases for relative paths."""

    @pytest.mark.parametrize("path", [
        "a",
        "a/b",
        "a/b/c",
        "x/y/z",
        "1/2/3"
    ])
    def test_single_character_component(self, path):
        """Test edge case with single character components."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize("path", [
        "Home",
        "User",
        "MyApp",
        "ProjectName",
        "Workspace",
        "home/User",
        "usr/Local",
        "var/Log",
        "tmp/Data",
        "etc/Nginx"
    ])
    def test_mixed_case(self, path):
        """Test edge case with mixed case components."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    def test_minimum_length(self):
        """Test edge case with minimum valid length (1 character)."""
        model = TestModel(path="a")
        assert_that(model.path).is_equal_to("a")

    def test_maximum_length(self):
        """Test edge case with maximum valid length (256 characters)."""
        # Create a path that is exactly 256 characters
        component = "a" * 256
        max_path = f"{component}"
        
        model = TestModel(path=max_path)
        assert_that(model.path).is_equal_to(max_path)
        assert_that(len(model.path)).is_equal_to(256)


class TestSpecialPathPatterns:
    """Test special path patterns like dot files and directory references."""

    def test_dot_files(self):
        """Test that dot files are valid."""
        model = TestModel(path=".gitignore")
        assert_that(model.path).is_equal_to(".gitignore")

    @pytest.mark.parametrize("path", [
        ".env",
        ".config",
        ".cache",
        ".local",
        ".ssh",
        ".bashrc",
        ".profile",
        ".vimrc"
    ])
    def test_dot_files_variations(self, path):
        """Test various dot file patterns."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    def test_current_directory(self):
        """Test that current directory reference is valid."""
        model = TestModel(path=".")
        assert_that(model.path).is_equal_to(".")

    def test_parent_directory(self):
        """Test that parent directory reference is valid."""
        model = TestModel(path="..")
        assert_that(model.path).is_equal_to("..")

    @pytest.mark.parametrize("path", [
        "../parent",
        "../../grandparent",
        "../sibling",
        "../../cousin",
        "..//invalid",  # This should be invalid due to consecutive slashes
    ])
    def test_parent_references(self, path):
        """Test parent directory references."""
        if "//" in path:
            # Paths with consecutive slashes should be invalid
            with pytest.raises(ValidationError, match="should match pattern"):
                TestModel(path=path)
        else:
            model = TestModel(path=path)
            assert_that(model.path).is_equal_to(path)
