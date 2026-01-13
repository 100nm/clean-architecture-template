from collections.abc import AsyncIterator

from injection import injectable, scoped
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from src.settings import Scope, Settings


@injectable
def _engine_factory(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.db.get_url())


@scoped(Scope.REQUEST)
async def _session_factory(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
