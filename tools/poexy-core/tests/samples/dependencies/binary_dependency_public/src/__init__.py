import typer

app = typer.Typer(
    name="mutex",
    help="A CLI for mutex in CICD pipelines using database as a lock store.",
    no_args_is_help=True,
    add_completion=False,
)


@app.command(name="message", help="Print a message.", no_args_is_help=True)
def message(text: str = typer.Option(..., help="The message to print.")):
    print(text)


if __name__ == "__main__":
    app()
