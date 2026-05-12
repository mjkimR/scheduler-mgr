import uuid
from typing import Annotated, Any, Optional

from app.features.schedule_configs.models import ScheduleConfig
from app.features.schedule_configs.repos import ScheduleConfigRepository
from app.features.schedule_configs.schemas import ScheduleConfigCreate, ScheduleConfigPatch, ScheduleConfigPut
from app_base.base.repos.base import ModelType
from app_base.base.services.base import (
    BaseContextKwargs,
    BaseCreateServiceMixin,
    BaseDeleteServiceMixin,
    BaseGetMultiServiceMixin,
    BaseGetServiceMixin,
    BaseUpdateServiceMixin,
    TContextKwargs,
)
from app_base.base.services.exists_check_hook import ExistsCheckHooksMixin
from app_base.base.services.unique_constraints_hook import UniqueConstraintHooksMixin
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


class ScheduleConfigContextKwargs(BaseContextKwargs):
    pass


class ScheduleConfigService(
    UniqueConstraintHooksMixin,  # Ensure unique constraints before create/update
    ExistsCheckHooksMixin,  # Ensure existence checks before operations
    BaseCreateServiceMixin[ScheduleConfigRepository, ScheduleConfig, ScheduleConfigCreate, ScheduleConfigContextKwargs],
    BaseGetMultiServiceMixin[ScheduleConfigRepository, ScheduleConfig, ScheduleConfigContextKwargs],
    BaseGetServiceMixin[ScheduleConfigRepository, ScheduleConfig, ScheduleConfigContextKwargs],
    BaseUpdateServiceMixin[
        ScheduleConfigRepository, ScheduleConfig, ScheduleConfigPut, ScheduleConfigPatch, ScheduleConfigContextKwargs
    ],
    BaseDeleteServiceMixin[ScheduleConfigRepository, ScheduleConfig, ScheduleConfigContextKwargs],
):
    def __init__(self, repo: Annotated[ScheduleConfigRepository, Depends()]):
        self._repo = repo

    @property
    def repo(self) -> ScheduleConfigRepository:
        return self._repo

    @property
    def context_model(self):
        return ScheduleConfigContextKwargs

    async def _unique_constraints(
        self,
        obj_data: ScheduleConfigCreate | ScheduleConfigPut | ScheduleConfigPatch,
        context: ScheduleConfigContextKwargs,
    ):
        if obj_data.key:
            yield self.repo.model.name == obj_data.name, "ScheduleConfig name must be unique."

    async def put(
        self,
        session: AsyncSession,
        obj_id: uuid.UUID,
        obj_data: ScheduleConfigPut,
        context: Optional[TContextKwargs] = None,
        **update_fields: Any,
    ) -> ModelType | None:
        exists = await self.repo.get_by_pk(session, obj_id)
        if not exists:
            raise ValueError(f"ScheduleConfig with id {obj_id} does not exist for PUT operation.")
        if (obj_data.cron_expression and obj_data.cron_expression != exists.cron_expression) or (
            obj_data.interval_seconds and obj_data.interval_seconds != exists.interval_seconds
        ):
            update_fields["next_run_at"] = None  # Reset next_run_at to trigger recalculation based on new schedule
        return await super().put(session, obj_id, obj_data, context, **update_fields)

    async def patch(
        self,
        session: AsyncSession,
        obj_id: uuid.UUID,
        obj_data: ScheduleConfigPatch,
        context: Optional[TContextKwargs] = None,
        **update_fields: Any,
    ) -> ModelType | None:
        if obj_data.cron_expression or obj_data.interval_seconds:
            update_fields["next_run_at"] = None  # Reset next_run_at to trigger recalculation based on new schedule
        return await super().patch(session, obj_id, obj_data, context, **update_fields)
