from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvloop
from injection import adefine_scope
from injection.entrypoint import AsyncEntrypoint, Entrypoint, entrypointmaker
from injection.loaders import load_packages, load_profile

from src.settings import DIScope, Profile, Settings


@asynccontextmanager
async def lifespan(profile: Profile | None = None) -> AsyncIterator[None]:
    from src import core, services
    from src.infra import adapters, query_handlers

    load_packages(adapters, core, query_handlers, services)

    if profile is not None:
        load_profile(profile)

    async with adefine_scope(DIScope.LIFESPAN, kind="shared"):
        yield


@entrypointmaker
def main[**P, T](
    entrypoint: AsyncEntrypoint[P, T],
    settings: Settings,
) -> Entrypoint[P, T]:
    return (
        entrypoint.inject()
        .decorate(adefine_scope(DIScope.REQUEST))
        .decorate(lifespan(settings.profile))
        .async_to_sync(uvloop.run)
    )
