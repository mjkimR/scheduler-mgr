from app.features.schedule_logs.models import ScheduleLog
from app.features.schedule_logs.schemas import ScheduleLogCreate
from app_base.base.repos.base import BaseRepository


class ScheduleLogRepository(BaseRepository[ScheduleLog, ScheduleLogCreate, None, None]):
    model = ScheduleLog
