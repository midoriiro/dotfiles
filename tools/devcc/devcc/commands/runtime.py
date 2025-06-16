from typing import List, Optional

import typer
from typer import Option
from typing_extensions import Annotated

from ..models import Env, MountPoint, MountType, RuntimeFeature


def validate_user(user: Optional[str]):
    if user is None:
        return
    parts = user.split(":")
    if len(parts) != 2 or parts[0] not in ["container", "remote"]:
        raise typer.BadParameter(
            "User must be in format 'container:user' or 'remote:user'"
        )
    if not parts[1].strip():
        raise typer.BadParameter("User cannot be empty")
    if not parts[1].isalnum():
        raise typer.BadParameter("User must be alphanumeric")
    if len(parts[1]) < 3:
        raise typer.BadParameter("User must be at least 3 characters long")
    if parts[1].lower() == "root":
        raise typer.BadParameter("User cannot be 'root'")
    if parts[1][0].isdigit():
        raise typer.BadParameter("User cannot start with a digit")
    return user

def validate_env(env: Optional[str]):
    if env is None:
        return
    if not env.strip():
        raise typer.BadParameter("Environment variable string cannot be empty")
    parts = env.split(":", 1)
    if len(parts) != 2 or parts[0] not in ["container", "remote"]:
        raise typer.BadParameter(
            f"Environment variable '{env}' must be in 'container:key=value' or 'remote:key=value' format"
        )
    env_part = parts[1]
    if "=" not in env_part:
        raise typer.BadParameter(
            f"Environment variable '{env_part}' must be in key=value format"
        )
    key, value = env_part.split("=", 1)
    if not key.strip():
        raise typer.BadParameter("Environment variable key cannot be empty")
    if not value.strip():
        raise typer.BadParameter("Environment variable value cannot be empty")
    return env

def validate_mounts(mounts: Optional[str]):
    if mounts is None:
        return
    if not mounts.strip():
        raise typer.BadParameter("Mount point string cannot be empty")
    parts = mounts.split(":")
    if len(parts) < 3:
        raise typer.BadParameter(
            f"Mount point '{mounts}' must be in source:target:type[:options] format"
        )

    source, target, mount_type = parts[:3]
    if not source.strip() or not target.strip() or not mount_type.strip():
        raise typer.BadParameter(
            f"Source, target, and type cannot be empty in '{mounts}'"
        )

    if mount_type not in [MountType.BIND.value, MountType.VOLUME.value]:
        raise typer.BadParameter(
            f"Mount type must be one of: {MountType.BIND.value}, {MountType.VOLUME.value}"
        )

    if len(parts) > 3 and not parts[3].strip():
        raise typer.BadParameter(
            f"Options cannot be empty if provided in '{mounts}'"
        )
    return mounts


user_option = typer.Option(
    None,
    "--user",
    help="Container user in format 'user:remote' or 'user:container'",
    callback=validate_user
)

env_option = typer.Option(
    None,
    "--env",
    help="Environment variables in 'container:key=value' or 'remote:key=value' format, separated by commas",
    callback=validate_env
)

mounts_option = typer.Option(
    None,
    "--mounts",
    help="Mount points in 'source:target:type[:options]' format, separated by commas",
    callback=validate_mounts
)


def command(
    ctx: typer.Context,
    user: Optional[str] = user_option,
    env: Optional[str] = env_option,
    mounts: Optional[str] = mounts_option,
):
    try:
        runtime_feature = RuntimeFeature()

        # Set user if provided
        if user:
            user_type, username = user.split(":")
            if user_type == "remote":
                runtime_feature.remoteUser = username
            else:
                runtime_feature.containerUser = username

        # Add environment variable
        if env:
            env_type, env_part = env.split(":", 1)
            key, var = env_part.split("=")
            env_var = Env(key=key, value=var)
            if env_type == "container":
                runtime_feature.containerEnv = [env_var]
            else:
                runtime_feature.remoteEnv = [env_var]

        # Add mount point
        if mounts:
            parts = mounts.split(":")
            source = parts[0]
            target = parts[1]
            mount_type = MountType(parts[2])
            options = parts[3] if len(parts) > 3 else None

            mount = MountPoint(
                source=source,
                target=target,
                type=mount_type,
                options=options
            )
            runtime_feature.mounts = [mount]

        ctx.obj.features["runtime"] = runtime_feature
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)