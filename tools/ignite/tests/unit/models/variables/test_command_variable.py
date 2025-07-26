import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.variables import CommandVariable


class TestValidCommandVariables:
    """Test cases for valid command variable patterns."""

    @pytest.mark.parametrize(
        "value",
        [
            "$shell:bash(echo hello)",
            "$shell:sh(pwd)",
            "$shell:pwsh(Get-Location)",
            "$shell:bash(ls -la)",
            "$shell:sh(whoami)",
        ],
    )
    def test_shell_specific_commands(self, value):
        """Test that valid shell-specific command variables are accepted."""
        variable = CommandVariable(value)
        assert_that(variable.root).is_equal_to(value)

    @pytest.mark.parametrize(
        "value",
        [
            "$(echo hello)",
            "$(pwd)",
            "$(ls -la)",
            "$(whoami)",
            "$(date)",
        ],
    )
    def test_default_shell_commands(self, value):
        """Test that valid default shell command variables are accepted."""
        variable = CommandVariable(value)
        assert_that(variable.root).is_equal_to(value)

    @pytest.mark.parametrize(
        "value",
        [
            "$shell:bash(echo 'hello world')",
            '$shell:sh(echo "test value")',
            "$shell:pwsh(Write-Host 'PowerShell test')",
            "$(echo 'complex command with spaces')",
        ],
    )
    def test_commands_with_quotes(self, value):
        """Test that command variables with quotes are accepted."""
        variable = CommandVariable(value)
        assert_that(variable.root).is_equal_to(value)

    @pytest.mark.parametrize(
        "value",
        [
            "$shell:bash(echo hello && echo world)",
            "$shell:sh(ls | wc -l)",
            "$shell:pwsh(Get-Process | Select-Object Name)",
            "$(echo test; echo done)",
        ],
    )
    def test_complex_commands(self, value):
        """Test that complex command variables with operators are accepted."""
        variable = CommandVariable(value)
        assert_that(variable.root).is_equal_to(value)


class TestInvalidCommandVariables:
    """Test cases for invalid command variable patterns."""

    @pytest.mark.parametrize(
        "value",
        [
            "echo hello",
            "shell:bash(echo hello)",
            "$bash(echo hello)",
            "$sh(echo hello)",
            "$pwsh(echo hello)",
        ],
    )
    def test_missing_required_prefix(self, value):
        """Test that command variables without proper prefix are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            CommandVariable(value)

    @pytest.mark.parametrize(
        "value",
        [
            "$shell:bash echo hello)",
            "$shell:sh(echo hello",
            "$shell:pwsh echo hello",
            "$(echo hello",
            "$echo hello)",
        ],
    )
    def test_missing_parentheses(self, value):
        """Test that command variables without proper parentheses are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            CommandVariable(value)

    @pytest.mark.parametrize(
        "value",
        [
            "$shell:invalid(echo hello)",
            "$shell:zsh(echo hello)",
            "$shell:fish(echo hello)",
            "$shell:cmd(echo hello)",
        ],
    )
    def test_invalid_shell_types(self, value):
        """Test that command variables with invalid shell types are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            CommandVariable(value)

    @pytest.mark.parametrize(
        "value",
        [
            "$shell:(echo hello)",
            "$shell:bash()",
            "$shell:sh()",
            "$()",
        ],
    )
    def test_empty_commands(self, value):
        """Test that command variables with empty commands are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            CommandVariable(value)

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "$",
            "$(",
            "$shell:",
            "$shell:bash",
        ],
    )
    def test_incomplete_patterns(self, value):
        """Test that incomplete command variable patterns are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            CommandVariable(value)


class TestCommandVariableResolve:
    """Test cases for command variable resolution."""

    @patch("ignite.models.variables.subprocess.run")
    def test_resolve_bash_command(self, mock_run):
        """Test resolving a bash command variable."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "hello world\n"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        variable = CommandVariable("$shell:bash(echo hello world)")
        result = variable.resolve()

        assert_that(result).is_equal_to("hello world")
        mock_run.assert_called_once_with(
            ["bash", "-c", '"echo', "hello", 'world"'],
            text=True,
            capture_output=True,
            env={
                "PATH": os.environ["PATH"],
            },
            shell=False,
        )

    @patch("ignite.models.variables.subprocess.run")
    def test_resolve_sh_command(self, mock_run):
        """Test resolving a sh command variable."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "/home/user\n"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        variable = CommandVariable("$shell:sh(pwd)")
        result = variable.resolve()

        assert_that(result).is_equal_to("/home/user")
        mock_run.assert_called_once_with(
            ["sh", "-c", '"pwd"'],
            text=True,
            capture_output=True,
            env={
                "PATH": os.environ["PATH"],
            },
            shell=False,
        )

    @patch("ignite.models.variables.subprocess.run")
    def test_resolve_pwsh_command(self, mock_run):
        """Test resolving a PowerShell command variable."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "C:\\Users\\test\n"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        variable = CommandVariable("$shell:pwsh(Get-Location)")
        result = variable.resolve()

        assert_that(result).is_equal_to("C:\\Users\\test")
        mock_run.assert_called_once_with(
            ["pwsh", "-command", '"Get-Location"'],
            text=True,
            capture_output=True,
            env={
                "PATH": os.environ["PATH"],
            },
            shell=False,
        )

    @patch("ignite.models.variables.subprocess.run")
    def test_resolve_default_shell_command(self, mock_run):
        """Test resolving a default shell command variable."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "test output\n"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        variable = CommandVariable("$(echo test output)")
        result = variable.resolve()

        assert_that(result).is_equal_to("test output")
        mock_run.assert_called_once_with(
            "echo test output",
            text=True,
            capture_output=True,
            env={
                "PATH": os.environ["PATH"],
            },
            shell=True,
        )

    @patch("ignite.models.variables.subprocess.run")
    def test_resolve_command_with_spaces(self, mock_run):
        """Test resolving a command with spaces in arguments."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "hello world test\n"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        variable = CommandVariable("$shell:bash(echo hello world test)")
        result = variable.resolve()

        assert_that(result).is_equal_to("hello world test")
        mock_run.assert_called_once_with(
            ["bash", "-c", '"echo', "hello", "world", 'test"'],
            text=True,
            capture_output=True,
            env={
                "PATH": os.environ["PATH"],
            },
            shell=False,
        )

    @patch("ignite.models.variables.subprocess.run")
    def test_resolve_strips_whitespace(self, mock_run):
        """Test that resolve strips whitespace from command output."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "  output with spaces  \n\n"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        variable = CommandVariable("$(echo output)")
        result = variable.resolve()

        assert_that(result).is_equal_to("output with spaces")

    @patch("ignite.models.variables.subprocess.run")
    def test_resolve_with_current_working_directory(self, mock_run):
        """Test resolving a command with a current working directory."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "/home/user\n"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        variable = CommandVariable("$shell:sh(pwd)")
        result = variable.resolve(Path("/home/user"))

        assert_that(result).is_equal_to("/home/user")
        mock_run.assert_called_once_with(
            ["sh", "-c", '"pwd"'],
            text=True,
            capture_output=True,
            env={
                "PATH": os.environ["PATH"],
            },
            cwd=Path("/home/user").resolve(),
            shell=False,
        )


class TestCommandVariableErrors:
    """Test cases for command variable error handling."""

    @patch("ignite.models.variables.subprocess.run")
    def test_resolve_command_failure(self, mock_run):
        """Test that resolve raises ValueError when command fails."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "command not found\n"
        mock_run.return_value = mock_process

        variable = CommandVariable("$(invalid_command)")

        with pytest.raises(ValueError, match="Command failed"):
            variable.resolve()

    @patch("ignite.models.variables.subprocess.run")
    def test_resolve_command_with_error_message(self, mock_run):
        """Test that resolve includes error message in exception."""
        mock_process = Mock()
        mock_process.returncode = 127
        mock_process.stdout = ""
        mock_process.stderr = "bash: nonexistent: command not found\n"
        mock_run.return_value = mock_process

        variable = CommandVariable("$shell:bash(nonexistent)")

        with pytest.raises(ValueError, match="bash: nonexistent: command not found"):
            variable.resolve()

    def test_resolve_invalid_format_raises_error(self):
        """
        Test that resolve raises ValueError for invalid format (should not happen
        with valid CommandVariable).
        """
        # This tests the internal error handling, though it shouldn't be reachable
        # with a properly validated CommandVariable
        variable = CommandVariable("$(echo test)")
        # Manually corrupt the root value to test error handling
        variable.root = "invalid format"

        with pytest.raises(ValueError, match="Invalid command variable"):
            variable.resolve()


class TestCommandVariableEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    @patch("ignite.models.variables.subprocess.run")
    def test_resolve_empty_output(self, mock_run):
        """Test resolving a command that produces no output."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        variable = CommandVariable("$(true)")

        with pytest.raises(ValueError, match="stdout is empty"):
            variable.resolve()

    @patch("ignite.models.variables.subprocess.run")
    def test_resolve_multiline_output(self, mock_run):
        """Test resolving a command with multiline output."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "line1\nline2\nline3\n"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        variable = CommandVariable("$(echo -e 'line1\\nline2\\nline3')")
        result = variable.resolve()

        assert_that(result).is_equal_to("line1\nline2\nline3")

    def test_command_variable_with_special_characters(self):
        """Test that command variables can contain special characters in commands."""
        special_commands = [
            "$shell:bash(echo 'test@email.com')",
            '$shell:sh(echo "value=123")',
            "$(echo 'path/to/file')",
            "$shell:pwsh(Write-Host 'C:\\\\temp\\\\file.txt')",
        ]

        for command in special_commands:
            variable = CommandVariable(command)
            assert_that(variable.root).is_equal_to(command)
