import logging
from pathlib import Path
import sys
from typing import Optional
import typer

from poexy import poetry
from poexy.pyproject import Pyproject, PyprojectError
from poexy.safe_print import safe_print_done, safe_print_info, safe_print_start
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


def _entry_point_parser(value: str) -> str:
    if value.endswith(".py"):
        return value
    return f"{value}.py"


def _validate_path(poetry_project_path: Path, module_path: Path) -> Path:
    path = poetry_project_path / module_path
    if not path.exists():
        raise typer.BadParameter(f"Module path '{path}' does not exist.")


app = typer.Typer(
    name="poexy",
    help="A CLI for building and packaging Poetry project as executable.",
    no_args_is_help=True, 
    add_completion=False
)


@app.command(
    help="Build and package Poetry project as executable.", 
    no_args_is_help=True
)
def command(
    poetry_project_path: Optional[Path] = typer.Option(
        None,
        help="Path to the Poetry project where pyproject.toml is located.",
        file_okay=False,
        dir_okay=True,
        exists=True,
        resolve_path=True,
    ),
    package_path: Optional[Path] = typer.Option(
        None,
        help="Relative path to the package in the project path (e.g. 'poexy' or 'src/poexy').",
        file_okay=False,
        dir_okay=True,
        exists=False,
        resolve_path=False,
    ),
    entry_point: Optional[str] = typer.Option(
        None,
        help="Module entry point (e.g. 'main.py' or 'main').",
        callback=_entry_point_parser,
    ),
    executable_name: Optional[str] = typer.Option(
        None,
        help="Name of the executable to build (e.g. 'poexy' or 'my-executable').",
    ),
    clean: bool = typer.Option(
        False,
        help="Clean the build directory.",
    ),
):
    _validate_path(poetry_project_path, package_path)
    
    pyproject = Pyproject(poetry_project_path)

    try:
        project_name = pyproject.project_name
        project_version = pyproject.project_version
        package_path = pyproject.package_path if package_path is None else package_path
        entry_point = pyproject.entry_point if entry_point is None else entry_point
        executable_name = pyproject.executable_name if executable_name is None else executable_name
    except PyprojectError as e:
        console.print_exception(show_locals=True)
        raise typer.Exit(1) from e
    finally:
        logger.info(f"Poetry project path: {poetry_project_path}")
        logger.info(f"Project name: {project_name}")
        logger.info(f"Project version: {project_version}")
        logger.info(f"Package path: {package_path}")
        logger.info(f"Entry point: {entry_point}")
        logger.info(f"Executable name: {executable_name}")

    try:
        if clean:
            safe_print_start(
                f"Cleaning build directory...", 
                printer=logger.info
            )
            poetry.clean_directories(poetry_project_path)
            safe_print_done("Build directory cleaned", printer=logger.info)

        safe_print_start(
            f"Building project...", 
            printer=logger.info
        )

        poetry.build_executable(
            project_path=poetry_project_path,
            executable_name=executable_name,
            package_path=package_path,
            entry_point=entry_point
        )

        poetry.build(project_path=poetry_project_path)

        poetry.package_wheel(
            project_path=poetry_project_path,
            project_name=project_name,
            project_version=project_version,
            executable_name=executable_name,
        )

        executable_path = poetry_project_path / "dist" / executable_name

        safe_print_info(
            f"Executable path: {executable_path}", 
            printer=logger.info
        )

        executable_size = poetry.get_executable_size(
            project_path=poetry_project_path,
            executable_name=executable_name
        )

        executable_size_kb = executable_size / 1024
        executable_size_mb = executable_size / 1024 / 1024

        if executable_size_kb < 1024:
            executable_size_str = f"{executable_size_kb:.2f} KB"
        else:
            executable_size_str = f"{executable_size_mb:.2f} MB"

        safe_print_info(
            f"Executable size: {executable_size_str}", 
            printer=logger.info
        )

        safe_print_done("Project built successfully", printer=logger.info)
    except poetry.PoetryProjectError as e:
        console.print_exception(show_locals=True)
        raise typer.Exit(1)
    except Exception as e:
        console.print_exception(show_locals=True)
        raise

    