from typing import Annotated

from app.features.tasks.core.schemas import TaskSpecResponse
from app.features.tasks.usecases.task_spec import GetTaskSpecUseCase
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/tasks", tags=["Task"], dependencies=[])


@router.get("/specs", status_code=status.HTTP_200_OK, response_model=list[TaskSpecResponse])
async def get_task_specs(
    use_case: Annotated[GetTaskSpecUseCase, Depends()],
):
    """Retrieve all registered task specifications."""
    return await use_case.execute()
