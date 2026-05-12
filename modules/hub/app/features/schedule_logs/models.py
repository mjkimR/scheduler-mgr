from datetime import datetime
from enum import StrEnum

from app.common.database import JSON_VARIANT
from app_base.base.models.mixin import Base, TimestampMixin, UUIDMixin
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class ScheduleLogStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"


class ScheduleLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "schedule_logs"

    schedule_config_id: Mapped[str] = mapped_column(
        ForeignKey("schedule_configs.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to the schedule config that triggered this log.",
    )
    status: Mapped[str] = mapped_column(
        nullable=False,
        comment="Execution status of the schedule. One of: success, failure.",
    )
    started_at: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="Timestamp when the task execution started.",
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="Timestamp when the task execution finished.",
    )
    payload: Mapped[dict] = mapped_column(
        JSON_VARIANT,
        nullable=False,
        default={},
        comment="Snapshot of the payload used during execution.",
    )
    error_message: Mapped[str | None] = mapped_column(
        nullable=True,
        comment="Error message if the task execution failed.",
    )
