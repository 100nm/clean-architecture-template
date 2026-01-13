from collections.abc import AsyncIterator

from injection.testing import test_scoped
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.settings import Scope


@test_scoped(Scope.LIFESPAN)
async def _session_test_factory(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine) as session:
        async with session.begin() as transaction:
            try:
                yield session
            finally:
                await transaction.rollback()
