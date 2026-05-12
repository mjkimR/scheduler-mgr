from typing import Annotated
from uuid import UUID

from app.features.schedule_logs.schemas import ScheduleLogCreate, ScheduleLogRead
from app.features.schedule_logs.usecases.crud import (
    CreateScheduleLogUseCase,
    DeleteScheduleLogUseCase,
    GetMultiScheduleLogUseCase,
    GetScheduleLogUseCase,
)
from app_base.base.deps.params.page import PaginationParam
from app_base.base.exceptions.basic import NotFoundException
from app_base.base.schemas.delete_resp import DeleteResponse
from app_base.base.schemas.paginated import PaginatedList
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/schedule_logs", tags=["ScheduleLog"], dependencies=[])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ScheduleLogRead)
async def create_schedule_log(
    use_case: Annotated[CreateScheduleLogUseCase, Depends()],
    schedule_log_in: ScheduleLogCreate,
):
    return await use_case.execute(schedule_log_in)


@router.get("", response_model=PaginatedList[ScheduleLogRead])
async def get_schedule_logs(
    use_case: Annotated[GetMultiScheduleLogUseCase, Depends()],
    pagination: PaginationParam,
):
    return await use_case.execute(**pagination)


@router.get("/{schedule_log_id}", response_model=ScheduleLogRead)
async def get_schedule_log(
    use_case: Annotated[GetScheduleLogUseCase, Depends()],
    schedule_log_id: UUID,
):
    schedule_log = await use_case.execute(schedule_log_id)
    if not schedule_log:
        raise NotFoundException()
    return schedule_log


@router.delete("/{schedule_log_id}", response_model=DeleteResponse)
async def delete_schedule_log(
    use_case: Annotated[DeleteScheduleLogUseCase, Depends()],
    schedule_log_id: UUID,
):
    return await use_case.execute(schedule_log_id)
