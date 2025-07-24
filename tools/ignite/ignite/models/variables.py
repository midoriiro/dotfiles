import logging
import os
import subprocess
from pathlib import Path
from typing import Annotated, Dict, Optional, Union

from annotated_types import Len
from pydantic import RootModel, StringConstraints

logger = logging.getLogger(__name__)

StringVariableValuePattern = "[a-zA-Z0-9-_ ]*"
StringVariableValue = Annotated[
    str,
    StringConstraints(
        min_length=2, max_length=50, pattern=rf"^{StringVariableValuePattern}$"
    ),
]


class StringVariable(RootModel[StringVariableValue]):
    def resolve(self) -> str:
        return str(self.root)


CommandVariableValuePattern = "\\$(shell\\:(sh|bash|pwsh))?\\(.+\\)"
CommandVariableValue = Annotated[
    str,
    StringConstraints(pattern=rf"^{CommandVariableValuePattern}$"),
]


class CommandVariable(RootModel[CommandVariableValue]):
    def resolve(self, current_working_directory: Optional[Path] = None) -> str:
        command = str(self.root)
        if command.startswith("$shell:") and command.endswith(")"):
            command = command.replace("$shell:", "")
            command = command.replace(")", "")
            shell, command = command.split("(")
        elif command.startswith("$(") and command.endswith(")"):
            command = command.replace(")", "")
            command = command.replace("$(", "")
            shell = None
        else:
            raise ValueError(f"Invalid command variable: {self.root}")

        subprocess_arguments = {
            "text": True,
            "capture_output": True,
            "shell": False,
        }

        if shell and shell == "sh":
            command = f'sh -c "{command}"'
            process_command = command.split(" ")
        elif shell and shell == "bash":
            command = f'bash -c "{command}"'
            process_command = command.split(" ")
        elif shell and shell == "pwsh":
            command = f'pwsh -command "{command}"'
            process_command = command.split(" ")
        else:
            subprocess_arguments["shell"] = True
            process_command = command

        if current_working_directory:
            subprocess_arguments["cwd"] = current_working_directory.resolve()

        logger.info(
            f"Running command: {process_command} with arguments: {subprocess_arguments}"
        )

        process = subprocess.run(
            process_command,
            env={
                "PATH": os.environ["PATH"],
            },
            **subprocess_arguments,
        )

        if process.returncode != 0:
            raise ValueError(
                f"Command failed: {command} with error: {process.stderr.strip()}"
            )

        if not process.stdout:
            raise ValueError(f"Command {command} stdout is empty")

        return process.stdout.strip()


VariableIdentifierPattern = "[a-z]([a-z]+|-)+[a-z]"

VariableIdentifier = Annotated[
    str,
    StringConstraints(
        min_length=3, max_length=50, pattern=rf"^{VariableIdentifierPattern}$"
    ),
]

VariableTypes = Union[StringVariable, CommandVariable]

VariableRootType = Annotated[
    Dict[VariableIdentifier, VariableTypes],
    Len(min_length=1, max_length=100),
]

ResolvedVariables = Dict[VariableIdentifier, str]


class Variables(RootModel[VariableRootType]):
    def resolve(
        self, command_current_working_directory: Optional[Path] = None
    ) -> ResolvedVariables:
        variables: ResolvedVariables = {}
        for identifier, variable in self.root.items():
            if isinstance(variable, StringVariable):
                variables[identifier] = variable.resolve()
            elif isinstance(variable, CommandVariable):
                variables[identifier] = variable.resolve(
                    command_current_working_directory
                )
            else:
                raise ValueError(f"Invalid variable type: {type(variable)}")
        return variables
