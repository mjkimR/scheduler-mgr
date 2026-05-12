from typing import Annotated

from app.features.schedule_logs.models import ScheduleLog
from app.features.schedule_logs.schemas import ScheduleLogCreate
from app.features.schedule_logs.services import ScheduleLogContextKwargs, ScheduleLogService
from app_base.base.usecases.crud import (
    BaseCreateUseCase,
    BaseDeleteUseCase,
    BaseGetMultiUseCase,
    BaseGetUseCase,
)
from fastapi import Depends


class GetScheduleLogUseCase(BaseGetUseCase[ScheduleLogService, ScheduleLog, ScheduleLogContextKwargs]):
    def __init__(self, service: Annotated[ScheduleLogService, Depends()]) -> None:
        super().__init__(service)


class GetMultiScheduleLogUseCase(BaseGetMultiUseCase[ScheduleLogService, ScheduleLog, ScheduleLogContextKwargs]):
    def __init__(self, service: Annotated[ScheduleLogService, Depends()]) -> None:
        super().__init__(service)


class CreateScheduleLogUseCase(
    BaseCreateUseCase[ScheduleLogService, ScheduleLog, ScheduleLogCreate, ScheduleLogContextKwargs]
):
    def __init__(self, service: Annotated[ScheduleLogService, Depends()]) -> None:
        super().__init__(service)


class DeleteScheduleLogUseCase(BaseDeleteUseCase[ScheduleLogService, ScheduleLog, ScheduleLogContextKwargs]):
    def __init__(self, service: Annotated[ScheduleLogService, Depends()]) -> None:
        super().__init__(service)
