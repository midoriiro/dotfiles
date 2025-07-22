import pytest
from assertpy import assert_that
from pydantic import BaseModel, ValidationError

from ignite.models.fs import AbsolutePath


class TestModel(BaseModel):
    """Test model with AbsolutePath field."""

    path: AbsolutePath


class TestValidAbsolutePaths:
    """Test valid absolute path structures and common use cases."""

    def test_valid_absolute_path_root(self):
        """Test that root path is valid."""
        model = TestModel(path="/")
        assert_that(model.path).is_equal_to("/")

    @pytest.mark.parametrize(
        "path",
        [
            "/home",
            "/usr",
            "/var",
            "/tmp",
            "/etc",
            "/bin",
            "/sbin",
            "/opt",
            "/data",
            "/workspace",
        ],
    )
    def test_valid_absolute_path_single_level(self, path):
        """Test that single level paths are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize(
        "path",
        [
            "/home/user",
            "/usr/local/bin",
            "/var/log/app",
            "/tmp/data/files",
            "/etc/nginx/conf.d",
            "/opt/applications/tools",
            "/data/projects/workspace",
            "/workspace/projects/src",
            "/home/user/documents/files",
            "/usr/share/applications",
        ],
    )
    def test_valid_absolute_path_multiple_levels(self, path):
        """Test that multi-level paths are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize(
        "path",
        [
            "/home/",
            "/usr/local/",
            "/var/log/",
            "/tmp/data/",
            "/etc/nginx/",
            "/opt/app/",
            "/data/project/",
            "/workspace/src/",
        ],
    )
    def test_valid_absolute_path_trailing_slash(self, path):
        """Test that trailing slash is valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize(
        "path",
        [
            "/home user",
            "/var log",
            "/tmp data",
            "/etc nginx",
            "/opt app",
            "/data project",
            "/workspace src",
            "/home/user name",
            "/var/log app name",
            "/tmp/data files",
            "/etc/nginx config",
            "/opt/my app",
            "/data/project name",
            "/workspace/src code",
        ],
    )
    def test_valid_absolute_path_spaces(self, path):
        """Test that paths with spaces are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize(
        "path",
        [
            "/hômé",
            "/üsér",
            "/vär",
            "/tëmp",
            "/étc",
            "/ôpt",
            "/dätä",
            "/wörkspäce",
            "/home/usér",
            "/var/lôg",
            "/tmp/dätä",
            "/etc/ngînx",
            "/opt/äpp",
            "/data/prôject",
            "/workspace/srç",
        ],
    )
    def test_valid_absolute_path_unicode_characters(self, path):
        """Test that paths with unicode characters are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)


class TestValidPathCharacters:
    """Test valid character types in path components."""

    @pytest.mark.parametrize(
        "path",
        [
            "/home/user123",
            "/var/log/app2",
            "/tmp/data2023",
            "/etc/nginx1",
            "/opt/app2",
            "/data/project1",
            "/workspace/v2",
            "/home/user/documents2023",
        ],
    )
    def test_valid_absolute_path_with_numbers(self, path):
        """Test that paths with numbers are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize(
        "path",
        [
            "/home/user_name",
            "/var/log/app_name",
            "/tmp/data_files",
            "/etc/nginx_config",
            "/opt/my_app",
            "/data/project_name",
            "/workspace/src_code",
            "/home/user/documents_backup",
        ],
    )
    def test_valid_absolute_path_with_underscores(self, path):
        """Test that paths with underscores are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize(
        "path",
        [
            "/home/user-name",
            "/var/log/app-name",
            "/tmp/data-files",
            "/etc/nginx-config",
            "/opt/my-app",
            "/data/project-name",
            "/workspace/src-code",
            "/home/user/documents-backup",
        ],
    )
    def test_valid_absolute_path_with_hyphens(self, path):
        """Test that paths with hyphens are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize(
        "path",
        [
            "/home/user.name",
            "/var/log/app.name",
            "/tmp/data.files",
            "/etc/nginx.config",
            "/opt/my.app",
            "/data/project.name",
            "/workspace/src.code",
            "/home/user/documents.backup",
        ],
    )
    def test_valid_absolute_path_with_dots(self, path):
        """Test that paths with dots are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize(
        "path",
        [
            "/home/user-name_123",
            "/var/log/app-name_v2",
            "/tmp/data-files_2023",
            "/etc/nginx-config.prod",
            "/opt/my-app_1.0",
            "/data/project-name_v1.2",
            "/workspace/src-code_alpha",
            "/home/user/documents-backup_2023",
        ],
    )
    def test_valid_absolute_path_mixed_characters(self, path):
        """Test that paths with mixed characters are valid."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)


class TestInvalidAbsolutePaths:
    """Test invalid absolute path structures and characters."""

    def test_invalid_absolute_path_empty_string(self):
        """Test that empty string is invalid."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            TestModel(path="")

    @pytest.mark.parametrize(
        "path",
        [
            "home",
            "usr/local",
            "var/log",
            "tmp/data",
            "etc/nginx",
            "opt/app",
            "data/project",
            "workspace/src",
        ],
    )
    def test_invalid_absolute_path_no_leading_slash(self, path):
        """Test that paths without leading slash are invalid."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(path=path)

    @pytest.mark.parametrize(
        "path",
        [
            "//",
            "//home",
            "/home//user",
            "/usr//local",
            "/var//log//app",
            "/tmp//data//files",
            "///etc",
            "/home///user",
        ],
    )
    def test_invalid_absolute_path_consecutive_slashes(self, path):
        """Test that consecutive slashes are invalid."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(path=path)

    @pytest.mark.parametrize(
        "path",
        [
            "/home@user",
            "/var#log",
            "/tmp$data",
            "/etc%nginx",
            "/opt&app",
            "/data*project",
            "/workspace+src",
            "/home=user",
            "/var?log",
            "/tmp!data",
            "/etc|nginx",
            "/opt~app",
            "/data`project",
            "/workspace'src",
            '/home"user',
            "/var(log)",
            "/tmp[data]",
            "/etc{nginx}",
            "/opt<app>",
            "/data;project",
            "/workspace:src",
            "/home,user",
        ],
    )
    def test_invalid_absolute_path_special_characters(self, path):
        """Test that paths with special characters are invalid."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(path=path)

    @pytest.mark.parametrize("path", [" ", "  ", "\t", "\n", "\r", " \t\n\r"])
    def test_invalid_absolute_path_whitespace_only(self, path):
        """Test that whitespace-only paths are invalid."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(path=path)

    def test_invalid_absolute_path_too_long(self):
        """Test that paths exceeding max_length (256) are invalid."""
        # Create a path that exceeds 256 characters
        long_component = "a" * 300
        long_path = f"/{long_component}"

        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            TestModel(path=long_path)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.parametrize("path", ["/a", "/a/b", "/a/b/c", "/x/y/z", "/1/2/3"])
    def test_edge_case_single_character_component(self, path):
        """Test edge case with single character components."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    @pytest.mark.parametrize(
        "path",
        [
            "/Home",
            "/User",
            "/MyApp",
            "/ProjectName",
            "/Workspace",
            "/home/User",
            "/usr/Local",
            "/var/Log",
            "/tmp/Data",
            "/etc/Nginx",
        ],
    )
    def test_edge_case_mixed_case(self, path):
        """Test edge case with mixed case components."""
        model = TestModel(path=path)
        assert_that(model.path).is_equal_to(path)

    def test_edge_case_minimum_length(self):
        """Test edge case with minimum valid length (2 characters)."""
        model = TestModel(path="/a")
        assert_that(model.path).is_equal_to("/a")

    def test_edge_case_maximum_length(self):
        """Test edge case with maximum valid length (256 characters)."""
        # Create a path that is exactly 256 characters
        component = "a" * 255
        max_path = f"/{component}"

        model = TestModel(path=max_path)
        assert_that(model.path).is_equal_to(max_path)
        assert_that(model.path).is_length(256)
