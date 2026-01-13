from injection import find_instance

from src.infra.api.builder import FastAPIBuilder
from src.infra.cli.apps import db
from src.infra.cli.builder import TyperBuilder

if __name__ == "__main__":
    cli = (
        find_instance(TyperBuilder)
        .include_apps(
            db.app,
            # Add your typer apps here.
        )
        .build()
    )
    cli()

else:
    app = (
        find_instance(FastAPIBuilder)
        .include_routers(
            # Add your routers here.
        )
        .build()
    )
