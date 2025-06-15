import typer

from devcc.context import Context

from .build import command as build_command
from .image import command as image_command

app = typer.Typer(chain=True)
app.command(name="image")(image_command)
app.command(name="build")(build_command)