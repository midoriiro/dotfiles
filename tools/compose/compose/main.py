from pathlib import Path
from typing import Optional

import typer

from compose.commands.build import command as build_command
from compose.commands.expose import command as expose_command
from compose.commands.image import command as image_command
from compose.commands.network import command as network_command
from compose.commands.runtime import command as runtime_command
from compose.commands.workspace import command as workspace_command
from compose.composer import Composer
from compose.context import Context

# Global options
output_option = typer.Option(
    None, "--output", "-o", help="Output path for the devcontainer.json file"
)
dry_run_option = typer.Option(
    False,
    "--dry-run",
    help="Print the configuration to stdout instead of writing to file",
)

class App:
    __typer: typer.Typer
    __context: Context
    def __init__(self):
        self.__context = Context()
        self.__typer = typer.Typer(chain=True, result_callback=self.__finalize_context)
        self.__typer.command(name="runtime")(runtime_command)
        self.__typer.command(name="workspace")(workspace_command)
        self.__typer.command(name="expose")(expose_command)
        self.__typer.command(name="image")(image_command)
        self.__typer.command(name="build")(build_command)
        self.__typer.command(name="network")(network_command)

    def register(self):
        @self.__typer.callback(invoke_without_command=True)
        def callback(
            ctx: typer.Context, 
            output: Optional[Path] = output_option, 
            dry_run: Optional[bool] = dry_run_option
        ):
            self.__init_context(ctx, output, dry_run)

    def __call__(self):
        self.__typer()


    def __init_context(
        self,
        ctx: typer.Context, 
        output: Optional[Path] = output_option, 
        dry_run: Optional[bool] = dry_run_option
    ):
        """Initialize the context with global options."""
        self.__context = Context()
        self.__context.output = output
        self.__context.dry_run = dry_run
        ctx.obj = self.__context

    def __finalize_context(self, *args, **kwargs):
        """Finalize the context by composing all features and saving the configuration."""
        composer = Composer(self.__context)
        composer.compose()
        composer.save()

    @property
    def context(self) -> Context:
        return self.__context

    @property
    def typer(self) -> typer.Typer:
        return self.__typer

# Create the app instance at module level
app = App()
app.register()

if __name__ == "__main__":
    app()
