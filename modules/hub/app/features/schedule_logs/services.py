from typing import Annotated

from app.features.schedule_logs.models import ScheduleLog
from app.features.schedule_logs.repos import ScheduleLogRepository
from app.features.schedule_logs.schemas import ScheduleLogCreate
from app_base.base.services.base import (
    BaseContextKwargs,
    BaseCreateServiceMixin,
    BaseDeleteServiceMixin,
    BaseGetMultiServiceMixin,
    BaseGetServiceMixin,
)
from fastapi import Depends


class ScheduleLogContextKwargs(BaseContextKwargs):
    pass


class ScheduleLogService(
    BaseCreateServiceMixin[ScheduleLogRepository, ScheduleLog, ScheduleLogCreate, ScheduleLogContextKwargs],
    BaseGetMultiServiceMixin[ScheduleLogRepository, ScheduleLog, ScheduleLogContextKwargs],
    BaseGetServiceMixin[ScheduleLogRepository, ScheduleLog, ScheduleLogContextKwargs],
    BaseDeleteServiceMixin[ScheduleLogRepository, ScheduleLog, ScheduleLogContextKwargs],
):
    def __init__(self, repo: Annotated[ScheduleLogRepository, Depends()]):
        self._repo = repo

    @property
    def repo(self) -> ScheduleLogRepository:
        return self._repo

    @property
    def context_model(self):
        return ScheduleLogContextKwargs
