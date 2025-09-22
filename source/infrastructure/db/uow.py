from sqlalchemy.ext.asyncio import AsyncSession

from source.application.repositories.base import IUnitOfWork


class UnitOfWork(IUnitOfWork):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def __aenter__(self):
        self._transaction = self._session.begin()
        await self._transaction.__aenter__()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._transaction.__aexit__(exc_type, exc_val, exc_tb)
