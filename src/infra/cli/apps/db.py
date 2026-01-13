from typing import Annotated

from sqlalchemy import Executable, NullPool, quoted_name, text
from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.ext.asyncio import create_async_engine
from typer import Argument, Typer, colors, confirm, echo, style

from src.infra.entrypoint import main
from src.settings import Settings

app = Typer(name="db")


@app.command("create")
def create_db(database_name: Annotated[str | None, Argument()] = None) -> None:
    @main(autocall=True)
    async def _(settings: Settings) -> None:
        name = database_name or settings.db.name.get_secret_value()
        stmt = text(f"CREATE DATABASE {quoted_name(name, quote=True)}")
        try:
            await _template1_execute(stmt, settings)
        except ProgrammingError:
            _echo_styled(f'"{name}" database already exists.', colors.YELLOW)
        else:
            _echo_styled(
                f'"{name}" database has been successfully created.',
                colors.GREEN,
            )


@app.command("drop")
def drop_db(database_name: Annotated[str | None, Argument()] = None) -> None:
    @main(autocall=True)
    async def _(settings: Settings) -> None:
        name = database_name or settings.db.name.get_secret_value()

        if not confirm(f'Are you sure you want to delete "{name}" database?'):
            return

        stmt = text(f"DROP DATABASE {quoted_name(name, quote=True)}")
        try:
            await _template1_execute(stmt, settings)
        except DBAPIError:
            _echo_styled(f'"{name}" database doesn\'t exist.', colors.YELLOW)
        else:
            _echo_styled(
                f'"{name}" database has been successfully deleted.',
                colors.GREEN,
            )


def _echo_styled(message: str, color: str) -> None:
    echo(style(message, fg=color, bold=True))


async def _template1_execute(statement: Executable, settings: Settings) -> None:
    engine = create_async_engine(
        settings.db.get_url("template1"),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )

    async with engine.connect() as connection:
        await connection.execute(statement)
