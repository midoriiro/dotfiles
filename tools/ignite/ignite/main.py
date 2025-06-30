import logging

import typer

from ignite.cli import cli


class TyperHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            if record.levelno in [logging.INFO, logging.DEBUG]:
                err = False
            else:
                err = True
            typer.echo(msg, err=err)
        except Exception:
            self.handleError(record)


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create and configure the TyperHandler
typer_handler = TyperHandler()
typer_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(typer_handler)


def main():
    cli()


if __name__ == "__main__":
    main()
