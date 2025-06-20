from typing import Optional

import typer
from typer import Context

from compose.models import ContainerNetworkFeature


def validate_name(name: str) -> str:
    """Validate the network name."""
    if not name or not name.strip():
        raise typer.BadParameter("Network name must be provided and cannot be empty")
    return name


name_option = typer.Option(
    None,
    "--name",
    help="Name of the network",
    callback=validate_name
)


def command(
    ctx: Context,
    name: Optional[str] = name_option
):
    """Handle container network operations."""
    try:
        network_feature = ContainerNetworkFeature()
        if name:
            network_feature.name = name
        if network_feature.has_valid_fields():
            ctx.obj.features['network'] = network_feature
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) 