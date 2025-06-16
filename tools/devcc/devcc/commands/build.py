from pathlib import Path
from typing import Optional

import typer

from devcc.models import ContainerBuildFeature


def validate_container_file(container_file: Optional[str]) -> Optional[str]:
    """Validate the container file path.
    
    Args:
        container_file: The path to the container file
        
    Returns:
        The validated container file path
        
    Raises:
        typer.BadParameter: If the container file path is invalid
    """
    if not container_file or not container_file.strip():
        raise typer.BadParameter("Container file path must be provided and cannot be empty")
    
    path = Path(container_file)
    if not path.exists():
        raise typer.BadParameter(f"Container file does not exist: {container_file}")
    
    return str(container_file)


def validate_context(context: Optional[str]) -> Optional[str]:
    """Validate the build context path.
    
    Args:
        context: The path to the build context
        
    Returns:
        The validated context path
        
    Raises:
        typer.BadParameter: If the context path is invalid
    """
    if not context:
        return None
    if not context.strip():
        raise typer.BadParameter("Build context path must be provided and cannot be empty")
    
    path = Path(context)
    if not path.exists():
        raise typer.BadParameter(f"Build context does not exist: {context}")
    
    return str(context)


def validate_target(target: Optional[str]) -> Optional[str]:
    """Validate the target build stage.
    
    Args:
        target: The target build stage
        
    Returns:
        The validated target build stage
        
    Raises:
        typer.BadParameter: If the target build stage is invalid
    """
    if not target:
        return None
    if not target.strip():
        raise typer.BadParameter("Target build stage cannot be empty")
    
    return target


container_file_option = typer.Option(
    None,
    "--container-file",
    help="Path to the container file",
    callback=validate_container_file
)

context_option = typer.Option(
    None,
    "--context",
    help="Path to the build context",
    callback=validate_context
)

target_option = typer.Option(
    None,
    "--target",
    help="Target build stage",
    callback=validate_target
)


def command(
    ctx: typer.Context,
    container_file: Optional[str] = container_file_option,
    context: Optional[str] = context_option,
    target: Optional[str] = target_option
):
    """Handle container build operations."""
    try:
        build_feature = ContainerBuildFeature()
        if container_file is not None:
            build_feature.container_file = container_file
        if context is not None:
            build_feature.context = context
        if target is not None:
            build_feature.target = target
        if build_feature.has_valid_fields():
            ctx.obj.features['build'] = build_feature
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)