from typing import Annotated

from app.features.dispatchers.services import DispatcherService
from app_base.core.database.engine import get_session_maker
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DispatchUseCase:
    def __init__(
        self,
        service: Annotated[DispatcherService, Depends()],
        session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)],
    ) -> None:
        self._service = service
        self._session_factory = session_factory

    async def execute(self) -> int:
        """Receive a trigger request, execute due schedules, and return the number of dispatched schedules."""
        async with self._session_factory() as session:
            async with session.begin():
                count = await self._service.tick(session)
        return int(count)
