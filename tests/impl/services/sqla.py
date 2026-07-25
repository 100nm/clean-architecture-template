from collections.abc import AsyncIterator

from injection.testing import test_scoped
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.settings import DIScope


@test_scoped(DIScope.LIFESPAN)
async def _session_test_factory(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine) as session, session.begin() as transaction:
        try:
            yield session
        finally:
            await transaction.rollback()
