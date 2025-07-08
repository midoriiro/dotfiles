import logging
from pathlib import Path

import typer
from poexy.cli import app, command
from rich.console import Console


console = Console()


class ConsoleHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            console.log(msg, emoji=True)
        except Exception:
            self.handleError(record)
            typer.Exit(1)


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create and configure the TyperHandler
console_handler = ConsoleHandler()
console_handler.setFormatter(logging.Formatter("%(message)s"))
logger.handlers.clear()
logger.addHandler(console_handler)

def self_build():
    poetry_project_path = Path(__file__).parent.parent
    command(
        poetry_project_path=poetry_project_path,
        package_path="poexy",
        entry_point="main.py",
        executable_name="poexy",
        clean=True
    )

def main():
    app()

if __name__ == "__main__":
    main()