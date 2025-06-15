from pathlib import Path
from typing import Optional, Tuple

import typer
from typer import Option

from ..models import ConnectionURL, Env, ExposeFeature, MountPoint, MountType


def validate_socket(socket_path: Optional[str]):
    """Validate socket path in format 'host_path:container_path'."""
    if socket_path is None:
        return None
    parts = socket_path.split(":")
    if len(parts) != 2:
        raise typer.BadParameter("Socket path must be in format 'host_path:container_path'")
    host_path, container_path = parts
    if not host_path.strip():
        raise typer.BadParameter("Host socket path cannot be empty")
    if not Path(host_path).is_absolute():
        raise typer.BadParameter("Host socket path must be absolute")
    if not container_path.strip():
        raise typer.BadParameter("Container socket path cannot be empty")
    if not Path(container_path).is_absolute():
        raise typer.BadParameter("Container socket path must be absolute")
    return socket_path

def validate_address(address: Optional[str]):
    """Validate address format (ssh://, tcp://, unix://)."""
    if address is None:
        return None
    if not address.strip():
        raise typer.BadParameter("Address cannot be empty")
    valid_prefixes = ["ssh://", "tcp://", "unix://"]
    if not any(address.startswith(prefix) for prefix in valid_prefixes):
        raise typer.BadParameter(
            "Address must start with one of: " + ", ".join(valid_prefixes)
        )
    return address


socket_path_option = typer.Option(
    None,
    "--socket",
    help="Socket path in format 'host_path:container_path'",
    callback=validate_socket
)

address_option = typer.Option(
    None,
    "--address",
    help="Container host (ssh://, tcp://, unix://)",
    callback=validate_address
)


def command(
    ctx: typer.Context,
    socket: Optional[str] = socket_path_option,
    address: Optional[str] = address_option,
):
    """Configure container-out-container settings."""
    if socket is not None and address is not None:
        raise typer.BadParameter("Both socket and address cannot be provided")
    try:
        expose_feature = ExposeFeature()
        # Add socket mount if requested
        if socket:
            host_path, container_path = socket.split(":")
            expose_feature.socket = MountPoint(
                source=host_path,
                target=container_path,
                type=MountType.BIND,
                options="consistency=cached"
            )
        # Add address if specified
        if address:
            expose_feature.address = ConnectionURL.from_string(address)
        ctx.obj.features["expose"] = expose_feature
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) 