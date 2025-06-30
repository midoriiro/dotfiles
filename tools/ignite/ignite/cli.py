import logging
import os
from pathlib import Path
from typing import Annotated, Any, List, Optional, override

import jsonschema
import pydantic
import typer
import yaml
import yaml.scanner
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from ignite.composers import Composer, ContainerComposer, WorkspaceComposer
from ignite.logging import (
    ComposerMessage,
    ConfigurationFileErrorMessage,
    JsonSchemaValidationErrorMessage,
    PydanticValidationErrorMessage,
    PydanticValidationErrorMessageList,
)
from ignite.models.config import Configuration
from ignite.resolvers import PathResolver
from ignite.utils import load_yaml_config

REPOSITORY_CONTEXT_ENV_VAR = "REPOSITORY_CONTEXT"

# Configure logger for CLI module
logger = logging.getLogger(__name__)


def __get_repository_context() -> Path:
    """Get the repository context from the environment variable."""
    repository_context = os.getenv(REPOSITORY_CONTEXT_ENV_VAR, None)
    if repository_context is None:
        load_dotenv()
        repository_context = os.getenv(REPOSITORY_CONTEXT_ENV_VAR)
    if repository_context is None:
        logger.error(f"Environment variable '{REPOSITORY_CONTEXT_ENV_VAR}' is not set")
        typer.echo(f"'{REPOSITORY_CONTEXT_ENV_VAR}' is not set", err=True)
        raise typer.Exit(1)
    return Path(repository_context)


def __handle_yaml_error(error: yaml.scanner.ScannerError) -> None:
    """Handle YAML parsing errors with structured logging."""
    message = ConfigurationFileErrorMessage.model_construct(
        line=error.problem_mark.line,
        column=error.problem_mark.column,
        problem=error.problem,
    )
    logger.error("YAML parsing failed", extra=message.model_dump())
    typer.echo(f"Configuration file is invalid:", err=True)
    typer.echo(f"  - Problem: {error.problem}", err=True)
    typer.echo(f"  - Line: {error.problem_mark.line}", err=True)
    typer.echo(f"  - Column: {error.problem_mark.column}", err=True)
    raise typer.Exit(1)


def __handle_schema_error(error: jsonschema.ValidationError) -> None:
    """Handle JSON Schema validation errors with structured logging."""
    message = JsonSchemaValidationErrorMessage.model_construct(
        json_path=error.json_path,
        error_message=error.message,
    )
    logger.error("JSON Schema validation failed", extra=message.model_dump())
    # Keep user-friendly output for CLI
    typer.echo(f"Configuration file is invalid:", err=True)
    typer.echo(f"  - Location: {error.json_path}", err=True)
    typer.echo(f"  - Message: {error.message}", err=True)
    raise typer.Exit(1)


def __handle_pydantic_error(error: pydantic.ValidationError) -> None:
    """Handle Pydantic validation errors with structured logging."""
    errors = []
    for error in error.errors():
        errors.append(
            PydanticValidationErrorMessage.model_construct(
                location=".".join(
                    str(item) for item in error.get("loc", "Unknown location")
                ),
                error_type=error.get("type", None),
                error_message=error.get("msg", None),
                input=error.get("input", None),
            )
        )

    message = PydanticValidationErrorMessageList.model_construct(errors=errors)

    logger.error("Pydantic validation failed", extra=message.model_dump())
    # Keep user-friendly output for CLI
    typer.echo("Configuration file is invalid:", err=True)
    for error in errors:
        typer.echo(f"  - Location: {error.location}", err=True)
        typer.echo(f"    Error Type: {error.error_type}", err=True)
        typer.echo(f"    Message: {error.error_message}", err=True)
        if error.input is not None:
            typer.echo(f"    Input: {error.input!r}", err=True)
    raise typer.Exit(1)


def __handle_composer_error(error: Exception, composer: Composer) -> None:
    """Handle composer errors with structured logging."""
    message = ComposerMessage.model_construct(
        composer_type=composer.__class__.__name__,
        error_type=error.__class__.__name__,
        error_message=str(error),
    )
    logger.error("Composer failed", extra=message.model_dump())
    # Keep user-friendly output for CLI
    typer.echo(f"Composer failed:", err=True)
    typer.echo(f"  - Composer Type: {composer.__class__.__name__}", err=True)
    typer.echo(f"  - Error Type: {error.__class__.__name__}", err=True)
    typer.echo(f"  - Error Message: {str(error)}", err=True)


cli = typer.Typer(no_args_is_help=True, add_completion=False)


class Command(BaseModel):
    configuration_path: Path = Field(default=Path("workspace.yml"))
    context_path: Path = Field(default=Path("."))


@cli.command(
    help="Development workspace environment management CLI tool.", no_args_is_help=True
)
def command(
    configuration: Path = typer.Option(
        Path("workspace.yml"),
        help="Path to the configuration file.",
        file_okay=True,
        dir_okay=False,
        exists=True,
        resolve_path=True,
    ),
    context: Path = typer.Argument(
        Path("."),
        help="Path to the context directory.",
        file_okay=False,
        dir_okay=True,
        exists=True,
        resolve_path=True,
    ),
):
    command = Command(configuration_path=configuration, context_path=context)
    schema = Configuration.model_json_schema()
    try:
        configuration_data = load_yaml_config(command.configuration_path, schema)
    except yaml.scanner.ScannerError as error:
        __handle_yaml_error(error)
    except jsonschema.ValidationError as error:
        __handle_schema_error(error)
    try:
        configuration: Configuration = Configuration(**configuration_data)
    except pydantic.ValidationError as error:
        __handle_pydantic_error(error)

    repository_context = __get_repository_context()
    user_context = Path(command.context_path)
    path_resolver = PathResolver(repository_context, user_context)
    polices = configuration.workspace.policies
    composer_raised_error = False

    try:
        container_composer = ContainerComposer(configuration.container)
        container_composer.compose()
        container_composer.save(user_context, polices)
    except Exception as error:
        __handle_composer_error(error, container_composer)
        composer_raised_error = True
    try:
        workspace_composer = WorkspaceComposer(configuration.workspace, path_resolver)
        workspace_composer.compose()
        workspace_composer.save(user_context, polices)
    except Exception as error:
        __handle_composer_error(error, workspace_composer)
        composer_raised_error = True

    if composer_raised_error:
        raise typer.Exit(1)
