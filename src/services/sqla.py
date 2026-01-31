from collections.abc import AsyncIterator

from injection import scoped
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from src.settings import Scope, Settings


@scoped(Scope.LIFESPAN)
async def _engine_factory(settings: Settings) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(settings.db.get_url())

    try:
        yield engine
    finally:
        await engine.dispose()


@scoped(Scope.REQUEST)
async def _session_factory(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
