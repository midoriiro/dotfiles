from typing import Optional

import typer
from typer import Option

from ..models import MountPoint, MountType, WorkspaceFeature


def validate_name(name: Optional[str]):
    if name is None:
        return None
    if not name.strip():
        raise typer.BadParameter("Name cannot be empty")
    if len(name) < 3:
        raise typer.BadParameter("Name must be at least 3 characters long")
    if not name.isalnum():
        raise typer.BadParameter("Name must be alphanumeric")
    return name


def validate_volume_name(volume_name: Optional[str]):
    if volume_name is None:
        return None
    if not volume_name.strip():
        raise typer.BadParameter("Volume name cannot be empty")
    if len(volume_name) < 3:
        raise typer.BadParameter("Volume name must be at least 3 characters long")
    if not volume_name[0].isalpha():
        raise typer.BadParameter("Volume name must start with a letter")
    if not all(c.isalnum() or c in ['_', '-'] for c in volume_name):
        raise typer.BadParameter("Volume name can only contain letters, numbers, underscores and dashes")
    return volume_name


name_option = typer.Option(
    None,
    "--name",
    "-n",
    help="Workspace name",
    callback=validate_name
)

volume_name_option = typer.Option(
    None,
    "--volume-name",
    "-v",
    help="Workspace volume name",
    callback=validate_volume_name
)


def command(
    ctx: typer.Context,
    name: Optional[str] = name_option,
    volume_name: Optional[str] = volume_name_option,
):
    """Configure workspace settings."""
    try:
        workspace_feature = WorkspaceFeature()

        if name is not None:
            workspace_feature.name = name

        if volume_name is not None:
            workspace_feature.workspaceMount = MountPoint(
                source=volume_name,
                target="/workspace",
                type=MountType.VOLUME,
                options="consistency=cached"
            )

        ctx.obj.features["workspace"] = workspace_feature
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) 