from dataclasses import dataclass, field
from typing import Self

from injection import injectable
from typer import Typer


@injectable
@dataclass(frozen=True)
class TyperBuilder:
    apps: list[Typer] = field(default_factory=list, init=False)

    def build(self) -> Typer:
        cli = Typer()

        for app in self.apps:
            cli.add_typer(app)

        return cli

    def include_apps(self, *apps: Typer) -> Self:
        self.apps.extend(apps)
        return self
