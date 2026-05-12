import asyncio
import functools
from datetime import datetime, timedelta, timezone

from app.features import tasks as task_registry
from app.features.schedule_configs.models import ScheduleConfig
from app.features.schedule_logs.models import ScheduleLog, ScheduleLogStatus
from app_base.core.log import logger
from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def _calc_next_run(config: ScheduleConfig, now: datetime) -> datetime:
    """Calculate the next run time based on cron expression or interval."""
    if config.cron_expression:
        return croniter(config.cron_expression, now).get_next(datetime)
    elif config.interval_seconds:
        return now + timedelta(seconds=config.interval_seconds)
    raise ValueError(f"ScheduleConfig {config.id} has neither cron_expression nor interval_seconds")


class DispatcherService:
    async def tick(self, session: AsyncSession) -> int:
        """Fetch due schedules using FOR UPDATE SKIP LOCKED and execute them. Returns the number of dispatched schedules."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        stmt = (
            select(ScheduleConfig)
            .where(
                ScheduleConfig.enabled.is_(True),
                (ScheduleConfig.next_run_at.is_(None)) | (ScheduleConfig.next_run_at <= now),
            )
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        due_configs = result.scalars().all()

        for config in due_configs:
            await self._dispatch(session, config, now)

        return len(due_configs)

    async def _dispatch(self, session: AsyncSession, config: ScheduleConfig, now: datetime) -> None:
        started_at = now
        next_run_at = _calc_next_run(config, now)

        status = ScheduleLogStatus.SUCCESS
        error_message: str | None = None

        try:
            func = task_registry.get(config.task_func)
            if asyncio.iscoroutinefunction(func):
                await func(**config.payload)
            else:
                await asyncio.get_event_loop().run_in_executor(None, functools.partial(func, **config.payload))
            logger.info("Dispatched schedule '{}' (id={})", config.name, config.id)
        except Exception as e:
            status = ScheduleLogStatus.FAILURE
            error_message = str(e)
            logger.error("Schedule '{}' (id={}) failed: {}", config.name, config.id, e)

        finished_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Update schedule timestamps within the same transaction while the lock is held
        config.last_run_at = started_at
        config.next_run_at = next_run_at

        session.add(
            ScheduleLog(
                schedule_config_id=str(config.id),
                status=status,
                started_at=started_at,
                finished_at=finished_at,
                payload=config.payload,
                error_message=error_message,
            )
        )
