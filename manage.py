#!/usr/bin/env python
import typer
import uvicorn

cli = typer.Typer()


@cli.command("runserver")
def _runserver(
    host: str = typer.Option("127.0.0.1"), port: int = typer.Option(8000)
) -> None:
    """
    Run development server
    """

    uvicorn.run("config.asgi:app", reload=True, host=host, port=port)


if __name__ == "__main__":
    cli()
