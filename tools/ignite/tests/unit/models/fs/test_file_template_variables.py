import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.fs import FileTemplateVariables


class TestFileTemplateVariablesCreation:
    """Tests for FileTemplateVariables object creation and validation."""

    def test_creation_with_valid_project_name(self):
        """Test creating FileTemplateVariables with valid project name."""
        variables = FileTemplateVariables(project_name="my-project")
        assert_that(variables.project_name).is_equal_to("my-project")

    def test_creation_with_empty_project_name(self):
        """Test creating FileTemplateVariables with empty project name."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            FileTemplateVariables(project_name="")

    def test_creation_with_special_characters(self):
        """
        Test creating FileTemplateVariables with special characters in project name.
        """
        variables = FileTemplateVariables(project_name="my-project_123")
        assert_that(variables.project_name).is_equal_to("my-project_123")

    def test_creation_with_too_long_project_name(self):
        """Test creating FileTemplateVariables with too long project name."""
        with pytest.raises(ValidationError, match="should have at most 50 characters"):
            FileTemplateVariables(project_name="a" * 51)

    def test_creation_without_project_name_raises_error(self):
        """
        Test that creating FileTemplateVariables without project_name raises
        ValidationError.
        """
        with pytest.raises(ValidationError):
            FileTemplateVariables()


class TestFileTemplateVariablesResolve:
    """Tests for FileTemplateVariables.resolve() method functionality."""

    def test_resolve_method_with_project_name_variable(self):
        """Test resolve method replaces ${projectName} variable."""
        variables = FileTemplateVariables(project_name="test-project")
        template = "Hello ${project-name}!"
        result = variables.resolve(template)
        assert_that(result).is_equal_to("Hello test-project!")

    def test_resolve_method_with_multiple_project_name_variables(self):
        """Test resolve method replaces multiple ${projectName} variables."""
        variables = FileTemplateVariables(project_name="my-app")
        template = "Project: ${project-name}, Name: ${project-name}"
        result = variables.resolve(template)
        assert_that(result).is_equal_to("Project: my-app, Name: my-app")

    def test_resolve_method_with_preserved_template_structure(self):
        """Test resolve method preserves template structure."""
        variables = FileTemplateVariables(project_name="test-project")
        template = "Hello ${project-name}!\nThis is a test.\n"
        result = variables.resolve(template)
        assert_that(result).is_equal_to("Hello test-project!\nThis is a test.\n")
        assert_that(template).is_equal_to("Hello ${project-name}!\nThis is a test.\n")

    def test_resolve_method_with_no_variables(self):
        """Test resolve method returns template unchanged when no variables present."""
        variables = FileTemplateVariables(project_name="test")
        template = "Hello World!"
        result = variables.resolve(template)
        assert_that(result).is_equal_to("Hello World!")

    def test_resolve_method_with_wrong_variable_name(self):
        """Test resolve method returns template unchanged when no variables present."""
        variables = FileTemplateVariables(project_name="test")
        template = "Hello ${project_name}!"
        result = variables.resolve(template)
        assert_that(result).is_equal_to("Hello ${project_name}!")


class TestFileTemplateVariablesResolveValidation:
    """Tests for FileTemplateVariables.resolve() method input validation."""

    def test_resolve_method_with_empty_template(self):
        """Test resolve method with empty template."""
        variables = FileTemplateVariables(project_name="test-project")
        template = ""

        with pytest.raises(ValueError, match="Template cannot be empty"):
            variables.resolve(template)

    def test_resolve_method_with_none_template(self):
        """Test resolve method with empty template."""
        variables = FileTemplateVariables(project_name="test-project")
        template = None

        with pytest.raises(ValueError, match="Template cannot be empty"):
            variables.resolve(template)

    def test_resolve_method_with_whitespace_template(self):
        """Test resolve method with empty template."""
        variables = FileTemplateVariables(project_name="test-project")
        template = "   "

        with pytest.raises(ValueError, match="Template cannot be empty"):
            variables.resolve(template)
