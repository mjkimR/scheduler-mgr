import uuid
from datetime import datetime, timezone
from typing import Annotated

from app.features.dispatchers.services import DispatcherService
from app.features.schedule_configs.schemas import ScheduleConfigRead
from app.features.schedule_jobs.models import ScheduleJobStatus
from app.features.schedule_jobs.schemas import ScheduleJobCreate, ScheduleJobRead
from app.features.schedule_jobs.services import ScheduleJobService
from app_base.core.database.transaction import AsyncTransaction
from fastapi import Depends


class DispatchUseCase:
    def __init__(
        self,
        service: Annotated[DispatcherService, Depends()],
        job_service: Annotated[ScheduleJobService, Depends()],
    ) -> None:
        self.service = service
        self.job_service = job_service

    async def execute(self) -> int:
        """Receive a trigger request, execute due schedules, and return the number of dispatched schedules."""
        now = datetime.now(timezone.utc)
        run_id = uuid.uuid4()
        schedule_jobs = []

        # Use a transaction to fetch due schedules with FOR UPDATE SKIP LOCKED, create corresponding ScheduleJobs, and update ScheduleConfigs atomically.
        async with AsyncTransaction() as session:
            # Process due schedule configs
            due_configs = await self.service.get_schedule_configs(session, now=now)
            for config in due_configs:
                job = await self.job_service.create(
                    session,
                    ScheduleJobCreate(
                        name=config.name,
                        schedule_config_id=config.id,
                        dispatcher_run_id=run_id,
                        status=ScheduleJobStatus.PENDING,
                        started_at=now,
                        payload=config.payload,
                    ),
                )
                job_dto = ScheduleJobRead.model_validate(job)
                config_dto = ScheduleConfigRead.model_validate(config)

                schedule_jobs.append((job_dto, config_dto))
                config.last_run_at = now
                config.next_run_at = self.service.calc_next_run(config, now)

            # Process retry jobs for failed schedule jobs that are due for retry
            retry_jobs = await self.service.get_retry_jobs(session, [config.id for config in due_configs])
            for job in retry_jobs:
                job.started_at = now
                job.status = ScheduleJobStatus.PENDING
                job.dispatcher_run_id = run_id
                job.error_message = None  # Clear previous error message for retry

                job_dto = ScheduleJobRead.model_validate(job)
                config_dto = ScheduleConfigRead.model_validate(job.schedule_config)

                schedule_jobs.append((job_dto, config_dto))

            # Persist all changes to ScheduleConfigs and ScheduleJobs in a single transaction
            session.add_all(due_configs)
            session.add_all(retry_jobs)

            await session.commit()

        # Run the schedule jobs
        if schedule_jobs:
            await self.service.dispatch_jobs(schedule_jobs, run_id=run_id)

        return len(schedule_jobs)
