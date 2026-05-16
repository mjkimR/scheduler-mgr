"""Unit tests for DispatcherService.

Covers:
- calc_next_run: delegation to the shared utility (smoke test only —
  full behavioural tests live in tests/unit/test_common/test_calc_schedule.py)
- _run_dispatch: complex error-handling logic (success, unregistered task,
  non-async callable, TimeoutError, CancelledError, generic exception)
"""

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.features.dispatchers.services import DispatcherService
from app.features.schedule_configs.models import ScheduleConfig
from app.features.schedule_configs.schemas import ScheduleConfigRead
from app.features.schedule_jobs.models import ScheduleJobStatus
from app.features.schedule_jobs.schemas import ScheduleJobRead

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_schedule_config(**kwargs) -> MagicMock:
    """Create a minimal ScheduleConfig stub (no DB required)."""
    config = MagicMock(spec=ScheduleConfig)
    config.id = kwargs.get("id", uuid.uuid4())
    config.name = kwargs.get("name", "test-schedule")
    config.cron_expression = kwargs.get("cron_expression", None)
    config.interval_seconds = kwargs.get("interval_seconds", None)
    return config


def _make_schedule_config_read(**kwargs) -> ScheduleConfigRead:
    """Create a minimal ScheduleConfigRead DTO."""
    now = datetime.now(timezone.utc)
    return ScheduleConfigRead(
        id=kwargs.get("id", uuid.uuid4()),
        name=kwargs.get("name", "test-schedule"),
        task_func=kwargs.get("task_func", "hello_world"),
        cron_expression=kwargs.get("cron_expression", None),
        interval_seconds=kwargs.get("interval_seconds", 60),
        payload=kwargs.get("payload", {}),
        enabled=True,
        start_at=None,
        end_at=None,
        last_run_at=None,
        next_run_at=None,
        created_at=now,
        updated_at=now,
    )


def _make_schedule_job_read(**kwargs) -> ScheduleJobRead:
    """Create a minimal ScheduleJobRead DTO."""
    now = datetime.now(timezone.utc)
    return ScheduleJobRead(
        id=kwargs.get("id", uuid.uuid4()),
        name=kwargs.get("name", "test-schedule"),
        schedule_config_id=kwargs.get("schedule_config_id", uuid.uuid4()),
        dispatcher_run_id=kwargs.get("dispatcher_run_id", uuid.uuid4()),
        status=ScheduleJobStatus.PENDING,
        started_at=now,
        finished_at=None,
        payload={},
        error_message=None,
        created_at=now,
        updated_at=now,
    )


def _mock_session() -> AsyncMock:
    """Create a mock AsyncSession where synchronous methods (e.g. add) are plain MagicMock."""
    session = AsyncMock()
    session.add = MagicMock()  # synchronous in SQLAlchemy
    session.add_all = MagicMock()  # synchronous in SQLAlchemy
    return session


def _make_service() -> DispatcherService:
    """Create a DispatcherService with mocked dependencies."""
    settings = MagicMock()
    settings.effective_timeout = 30
    settings.MAX_CONCURRENT_TASKS = 10
    service = DispatcherService.__new__(DispatcherService)
    service.settings = settings
    service.global_timeout = settings.effective_timeout
    service.job_repo = AsyncMock()
    service._semaphore = asyncio.Semaphore(10)
    return service


# ---------------------------------------------------------------------------
# TestCalcNextRun
# ---------------------------------------------------------------------------


class TestCalcNextRun:
    """Smoke tests for DispatcherService.calc_next_run.

    Detailed behavioural coverage lives in
    ``tests/unit/test_common/test_calc_schedule.py``.
    These tests only verify that the classmethod correctly delegates to
    :func:`app.common.utils.calc_schedule.calc_next_run`.
    """

    def test_delegates_to_shared_utility(self):
        """calc_next_run should produce the same result as the shared utility."""
        from app.common.utils.calc_schedule import calc_next_run as util_calc_next_run

        config = _make_schedule_config(interval_seconds=300)
        now = datetime(2026, 5, 13, 12, 0, 0, tzinfo=timezone.utc)

        expected = util_calc_next_run(config.cron_expression, config.interval_seconds, now)
        result = DispatcherService.calc_next_run(config, now)

        assert result == expected


# ---------------------------------------------------------------------------
# TestRunDispatch
# ---------------------------------------------------------------------------


class TestRunDispatch:
    """Tests for DispatcherService._run_dispatch (task execution + DB update)."""

    @pytest.fixture
    def service(self) -> DispatcherService:
        return _make_service()

    @pytest.fixture
    def job(self) -> ScheduleJobRead:
        return _make_schedule_job_read()

    @pytest.fixture
    def config(self) -> ScheduleConfigRead:
        return _make_schedule_config_read(task_func="hello_world", payload={})

    @pytest.fixture
    def run_id(self) -> uuid.UUID:
        return uuid.uuid4()

    def _mock_job(self):
        """Mock DB job object returned by job_repo.get_by_pk."""
        job = MagicMock()

        return job

    @pytest.mark.asyncio
    async def test_success_updates_job_as_success(self, service, job, config, run_id):
        """If the task executes successfully, the ScheduleJob status should be updated to SUCCESS."""

        async def _async_task(**kwargs):
            pass

        patcher = patch("app.features.dispatchers.services.ScheduleJob")
        mock_sj = patcher.start()
        mock_sj.retry_attempts = 0
        service.job_repo.get_by_pk = AsyncMock(return_value=job)

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
        ):
            mock_registry.get.return_value = _async_task
            mock_session = _mock_session()
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(rowcount=1))

            await service._run_dispatch(job, config, run_id=run_id)

        patcher.stop()
        mock_update.assert_called_once()
        args, kwargs = mock_update.return_value.where.return_value.values.call_args
        assert kwargs["status"] == ScheduleJobStatus.SUCCESS
        assert kwargs["error_message"] is None
        assert kwargs["retry_need"] is False

    @pytest.mark.asyncio
    async def test_unregistered_task_func_sets_failure(self, service, job, config, run_id):
        """If task_func is not registered, status should be FAILURE with an error message."""
        patcher = patch("app.features.dispatchers.services.ScheduleJob")
        mock_sj = patcher.start()
        mock_sj.retry_attempts = 0
        service.job_repo.get_by_pk = AsyncMock(return_value=job)

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
        ):
            mock_registry.get.return_value = None  # Unregistered task
            mock_session = _mock_session()
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(rowcount=1))

            await service._run_dispatch(job, config, run_id=run_id)

        patcher.stop()
        mock_update.assert_called_once()
        args, kwargs = mock_update.return_value.where.return_value.values.call_args
        assert kwargs["status"] == ScheduleJobStatus.FAILURE
        assert "not registered" in kwargs["error_message"]
        assert kwargs["retry_need"] is False

    @pytest.mark.asyncio
    async def test_sync_task_func_sets_failure(self, service, job, config, run_id):
        """If a synchronous function is registered, a TypeError should be raised and handled as FAILURE."""

        def _sync_task(**kwargs):
            pass  # Synchronous function (not async)

        patcher = patch("app.features.dispatchers.services.ScheduleJob")
        mock_sj = patcher.start()
        mock_sj.retry_attempts = 0

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
        ):
            mock_registry.get.return_value = _sync_task
            mock_session = _mock_session()
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(rowcount=1))

            await service._run_dispatch(job, config, run_id=run_id)

        patcher.stop()
        mock_update.assert_called_once()
        args, kwargs = mock_update.return_value.where.return_value.values.call_args
        assert kwargs["status"] == ScheduleJobStatus.FAILURE
        assert "must be an async function" in kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_timeout_error_sets_failure_and_retry(self, service, job, config, run_id):
        """On asyncio.TimeoutError, status should be FAILURE and retry_need should be True."""

        async def _timeout_task(**kwargs):
            raise asyncio.TimeoutError

        patcher = patch("app.features.dispatchers.services.ScheduleJob")
        mock_sj = patcher.start()
        mock_sj.retry_attempts = 0

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
        ):
            mock_registry.get.return_value = _timeout_task
            mock_session = _mock_session()
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(rowcount=1))

            await service._run_dispatch(job, config, run_id=run_id)

        patcher.stop()
        mock_update.assert_called_once()
        args, kwargs = mock_update.return_value.where.return_value.values.call_args
        assert kwargs["status"] == ScheduleJobStatus.FAILURE
        assert kwargs["retry_need"] is True
        assert "timed out" in kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_cancelled_error_sets_failure_and_reraises(self, service, job, config, run_id):
        """On asyncio.CancelledError, status should be FAILURE + retry_need=True, and CancelledError should be re-raised."""

        async def _cancelled_task(**kwargs):
            raise asyncio.CancelledError

        patcher = patch("app.features.dispatchers.services.ScheduleJob")
        mock_sj = patcher.start()
        mock_sj.retry_attempts = 0

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
        ):
            mock_registry.get.return_value = _cancelled_task
            mock_session = _mock_session()
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(rowcount=1))

            with pytest.raises(asyncio.CancelledError):
                await service._run_dispatch(job, config, run_id=run_id)

        patcher.stop()
        mock_update.assert_called_once()
        args, kwargs = mock_update.return_value.where.return_value.values.call_args
        assert kwargs["status"] == ScheduleJobStatus.FAILURE
        assert kwargs["retry_need"] is True

    @pytest.mark.asyncio
    async def test_generic_exception_sets_failure_with_error_message(self, service, job, config, run_id):
        """On a generic exception, status should be FAILURE and error_message should contain the exception message."""
        error_msg = "Something went wrong"

        async def _failing_task(**kwargs):
            raise RuntimeError(error_msg)

        patcher = patch("app.features.dispatchers.services.ScheduleJob")
        mock_sj = patcher.start()
        mock_sj.retry_attempts = 0

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
        ):
            mock_registry.get.return_value = _failing_task
            mock_session = _mock_session()
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(rowcount=1))

            await service._run_dispatch(job, config, run_id=run_id)

        patcher.stop()
        mock_update.assert_called_once()
        args, kwargs = mock_update.return_value.where.return_value.values.call_args
        assert kwargs["status"] == ScheduleJobStatus.FAILURE
        assert error_msg in kwargs["error_message"]
        assert kwargs["retry_need"] is False

    @pytest.mark.asyncio
    async def test_job_not_found_in_db_does_not_raise(self, service, job, config, run_id):
        """Even if the job is not found in DB, it should complete without raising an exception."""

        async def _async_task(**kwargs):
            pass

        patcher = patch("app.features.dispatchers.services.ScheduleJob")
        mock_sj = patcher.start()
        mock_sj.retry_attempts = 0

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update"),
        ):
            mock_registry.get.return_value = _async_task
            mock_session = _mock_session()
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(rowcount=0))

            # Should complete without raising an exception
            await service._run_dispatch(job, config, run_id=run_id)

        patcher.stop()
