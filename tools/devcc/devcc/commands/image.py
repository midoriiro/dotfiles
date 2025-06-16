from pathlib import Path
from typing import Optional

import typer

from devcc.models import ContainerImageFeature


def validate_name(name: Optional[str]) -> Optional[str]:
    """Validate the image name.
    
    The image name should follow the format: [repository/]name[:tag]
    Examples:
        - test_image
        - test_image:latest
        - myrepo/test_image
        - myrepo/test_image:latest
    
    Args:
        name: The image name to validate
        
    Returns:
        The validated image name
        
    Raises:
        typer.BadParameter: If the image name is invalid
    """
    if not name or not name.strip():
        raise typer.BadParameter("Image name must be provided and cannot be empty")
    
    # Check if the name follows the expected format
    parts = name.split('/')
    if len(parts) > 2:
        raise typer.BadParameter("Image name format is invalid. Expected format: [repository/]name[:tag]")
    
    repository = parts[0] if len(parts) == 2 else None
    if repository is not None and not repository.strip():
        raise typer.BadParameter("Repository name must be non-empty")
    
    name_and_tag = parts[-1].split(':')
    if len(name_and_tag) > 2:
        raise typer.BadParameter("Image name format is invalid. Expected format: [repository/]name[:tag]")
    
    if not name_and_tag[0]:
        raise typer.BadParameter("Image name must be non-empty")
    
    return name
name_option = typer.Option(
    None, 
    "--name",
    help="Name of the image", 
    callback=validate_name
)

def command(
    ctx: typer.Context,
    name: Optional[str] = name_option
):
    """Handle image-related operations."""
    try:
        image_feature = ContainerImageFeature()
        if name:
            image_feature.name = name
        if image_feature.has_valid_fields():
            ctx.obj.features['image'] = image_feature
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)