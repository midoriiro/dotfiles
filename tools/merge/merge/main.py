import configparser
import json
import logging
from enum import Enum
from pathlib import Path
from typing import List, Optional

import typer
import yaml

from merge.handlers import IniHandler, JsonHandler, YamlHandler


# Create a custom handler that uses typer.echo
class TyperHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            typer.echo(msg, err=True)
        except Exception:
            self.handleError(record)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = True

# Create and configure the TyperHandler
typer_handler = TyperHandler()
typer_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(typer_handler)

def write_to_file(output_data: str, output: Path):
    with open(output, 'w') as f:
        f.write(output_data)


class Format(str, Enum):
    JSON = "json"
    YAML = "yaml"
    INI = "ini"

    @staticmethod
    def get_extensions() -> List[str]:
        """Generate a list of file extensions for each format, with special handling for YAML."""
        extensions = []
        for fmt in Format:
            if fmt == Format.YAML:
                extensions.extend([".yaml", ".yml"])
            else:
                extensions.append(f".{fmt.value}")
        return extensions

    
def validate_path_format(path: Path):
    extensions = Format.get_extensions()
    if path.suffix.lower() not in extensions:
        raise typer.BadParameter(f"Unsupported file format for {path}. Valid formats are: {', '.join(extensions)}")
    
def validate_sources(sources: List[Path]) -> None:
    if not sources or len(sources) < 2:
        raise typer.BadParameter("At least two source files must be provided.")
    # Check if all paths in sources have the same extension
    extensions = {src.suffix.lower() for src in sources}
    if len(extensions) > 1:
        raise typer.BadParameter("All source files must have the same format.")
    for src in sources:
        if not src.exists():
            raise typer.BadParameter(f"Source file does not exist: {src}")
        if not src.is_file():
            raise typer.BadParameter(f"Source path is not a file: {src}")
        validate_path_format(src)
    return sources


def validate_output(output: Path) -> Path:
    """
    Validate the destination path to ensure it is a valid file path.
    
    Args:
        destination (Path): The destination file path.
    
    Returns:
        Path: The validated destination path.
    
    Raises:
        typer.BadParameter: If the destination path is not valid.
    """
    if output is None:
        return None
    if output.exists():
        raise typer.BadParameter(f"Output file already exists: {output}")
    validate_path_format(output)
    return output


app = typer.Typer(help="merge: Development management CLI tool.")

sources_argument: List[Path] = typer.Argument(
    ..., 
    help="List of source files to merge.",
    callback=validate_sources
)

output_option: Optional[Path] = typer.Option(
    None,
    "--output",
    help="Specify the output file for the merged content.",
    callback=validate_output
)

format_option: Format = typer.Option(
    None, 
    "--format",
    help="Output format (json, yaml, or ini). If not specified, will use the source files format.",
)

std_output_option: bool = typer.Option(
    False,
    "--std-output",
    help="Output merged data to standard output without writing to a file."
)


@app.command()
def merge(
    std_output: Optional[bool] = std_output_option,
    output: Optional[Path] = output_option,
    sources: List[Path] = sources_argument,
    format: Optional[Format] = format_option
):
    """
    Merge multiple source files into a single destination file. 
    All source files must be of the same format (json, yaml, or ini).
    """
    
    if format is None:
        extension = sources[0].suffix.lower()
        if extension == '.json':
            format = Format.JSON
        elif extension in ['.yaml', '.yml']:
            format = Format.YAML
        elif extension == '.ini':
            format = Format.INI
        logger.debug(f"Detected format: {format}")

    if format == Format.JSON:
        handler = JsonHandler()
    elif format == Format.YAML:
        handler = YamlHandler()
    elif format == Format.INI:
        handler = IniHandler()

    merged_data = handler.merge(sources)

    if output is None:
        output_callback = lambda output_data: typer.echo(output_data)
    else:
        output_callback = lambda output_data: write_to_file(output_data, output)

    handler.write(merged_data, output_callback)

    if output is not None:
        typer.echo(f"Merged {len(sources)} files into {output}.")


if __name__ == "__main__":
    app()
