from datetime import datetime
from uuid import UUID

from app.features.schedule_logs.models import ScheduleLogStatus
from app_base.base.schemas.mixin import TimestampSchemaMixin, UUIDSchemaMixin
from pydantic import BaseModel, ConfigDict, Field


class ScheduleLogCreate(BaseModel):
    schedule_config_id: UUID | None = Field(
        default=None, description="Reference to the schedule config that triggered this log."
    )
    status: ScheduleLogStatus = Field(description="Execution status of the schedule. One of: success, failure.")
    started_at: datetime = Field(description="Timestamp when the task execution started.")
    finished_at: datetime = Field(description="Timestamp when the task execution finished.")
    payload: dict = Field(default={}, description="Snapshot of the payload used during execution.")
    error_message: str | None = Field(default=None, description="Error message if the task execution failed.")


class ScheduleLogRead(UUIDSchemaMixin, TimestampSchemaMixin, ScheduleLogCreate):
    model_config = ConfigDict(from_attributes=True)
