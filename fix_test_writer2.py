import re

with open("modules/hub/tests/unit/test_dispatchers/test_dispatcher_services.py", "r") as f:
    content = f.read()

import textwrap

new_test = textwrap.dedent('''
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

    def _mock_job_obj(self):
        job_obj = MagicMock()
        job_obj.retry_attempts = 0
        return job_obj

    @pytest.mark.asyncio
    async def test_success_updates_job_as_success(self, service, job, config, run_id):
        async def _async_task(**kwargs):
            pass

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
        ):
            mock_registry.get.return_value = _async_task
            mock_session = _mock_session()
            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()

            # Fix sqlalchemy MagicMock error by preventing update from using ScheduleJob table
            mock_update.return_value.where.return_value.values.return_value = "mocked_stmt"

            # Fix TypeError with AsyncMock > int by mocking the ScheduleJob object inside the services
            with patch("app.features.dispatchers.services.ScheduleJob") as mock_sj:
                mock_sj.id = MagicMock()
                mock_sj.retry_attempts = 0
                await service._run_dispatch(job, config, run_id=run_id)

            mock_session.execute.assert_called_once_with("mocked_stmt")
            mock_session.commit.assert_called_once()
            args, kwargs = mock_update.return_value.where.return_value.values.call_args
            assert kwargs["status"] == ScheduleJobStatus.SUCCESS
            assert kwargs["error_message"] is None
            assert kwargs["retry_need"] is False

    @pytest.mark.asyncio
    async def test_unregistered_task_func_sets_failure(self, service, job, config, run_id):
        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
        ):
            mock_registry.get.return_value = None
            mock_session = _mock_session()
            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()

            mock_update.return_value.where.return_value.values.return_value = "mocked_stmt"

            with patch("app.features.dispatchers.services.ScheduleJob") as mock_sj:
                mock_sj.id = MagicMock()
                mock_sj.retry_attempts = 0
                await service._run_dispatch(job, config, run_id=run_id)

            mock_session.execute.assert_called_once_with("mocked_stmt")
            mock_session.commit.assert_called_once()
            args, kwargs = mock_update.return_value.where.return_value.values.call_args
            assert kwargs["status"] == ScheduleJobStatus.FAILURE
            assert "not registered" in kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_sync_task_func_sets_failure(self, service, job, config, run_id):
        def _sync_task(**kwargs):
            pass

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
        ):
            mock_registry.get.return_value = _sync_task
            mock_session = _mock_session()
            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()

            mock_update.return_value.where.return_value.values.return_value = "mocked_stmt"

            with patch("app.features.dispatchers.services.ScheduleJob") as mock_sj:
                mock_sj.id = MagicMock()
                mock_sj.retry_attempts = 0
                await service._run_dispatch(job, config, run_id=run_id)

            mock_session.execute.assert_called_once_with("mocked_stmt")
            mock_session.commit.assert_called_once()
            args, kwargs = mock_update.return_value.where.return_value.values.call_args
            assert kwargs["status"] == ScheduleJobStatus.FAILURE
            assert "must be an async function" in kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_timeout_error_sets_failure_and_retry(self, service, job, config, run_id):
        async def _timeout_task(**kwargs):
            raise asyncio.TimeoutError

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
        ):
            mock_registry.get.return_value = _timeout_task
            mock_session = _mock_session()
            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()

            mock_update.return_value.where.return_value.values.return_value = "mocked_stmt"

            with patch("app.features.dispatchers.services.ScheduleJob") as mock_sj:
                mock_sj.id = MagicMock()
                mock_sj.retry_attempts = 0
                await service._run_dispatch(job, config, run_id=run_id)

            mock_session.execute.assert_called_once_with("mocked_stmt")
            mock_session.commit.assert_called_once()
            args, kwargs = mock_update.return_value.where.return_value.values.call_args
            assert kwargs["status"] == ScheduleJobStatus.FAILURE
            assert kwargs["retry_need"] is True
            assert "timed out" in kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_cancelled_error_sets_failure_and_reraises(self, service, job, config, run_id):
        async def _cancelled_task(**kwargs):
            raise asyncio.CancelledError

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
        ):
            mock_registry.get.return_value = _cancelled_task
            mock_session = _mock_session()
            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()

            mock_update.return_value.where.return_value.values.return_value = "mocked_stmt"

            with patch("app.features.dispatchers.services.ScheduleJob") as mock_sj:
                mock_sj.id = MagicMock()
                mock_sj.retry_attempts = 0
                with pytest.raises(asyncio.CancelledError):
                    await service._run_dispatch(job, config, run_id=run_id)

            mock_session.execute.assert_called_once_with("mocked_stmt")
            mock_session.commit.assert_called_once()
            args, kwargs = mock_update.return_value.where.return_value.values.call_args
            assert kwargs["status"] == ScheduleJobStatus.FAILURE
            assert kwargs["retry_need"] is True

    @pytest.mark.asyncio
    async def test_generic_exception_sets_failure_with_error_message(self, service, job, config, run_id):
        error_msg = "Something went wrong"

        async def _failing_task(**kwargs):
            raise RuntimeError(error_msg)

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
        ):
            mock_registry.get.return_value = _failing_task
            mock_session = _mock_session()
            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()

            mock_update.return_value.where.return_value.values.return_value = "mocked_stmt"

            with patch("app.features.dispatchers.services.ScheduleJob") as mock_sj:
                mock_sj.id = MagicMock()
                mock_sj.retry_attempts = 0
                await service._run_dispatch(job, config, run_id=run_id)

            mock_session.execute.assert_called_once_with("mocked_stmt")
            mock_session.commit.assert_called_once()
            args, kwargs = mock_update.return_value.where.return_value.values.call_args
            assert kwargs["status"] == ScheduleJobStatus.FAILURE
            assert error_msg in kwargs["error_message"]
            assert kwargs["retry_need"] is False

    @pytest.mark.asyncio
    async def test_job_not_found_in_db_does_not_raise(self, service, job, config, run_id):
        async def _async_task(**kwargs):
            pass

        with (
            patch("app.features.dispatchers.services.task_registry") as mock_registry,
            patch("app.features.dispatchers.services.AsyncTransaction") as mock_tx,
            patch("app.features.dispatchers.services.update") as mock_update,
            patch("app.features.dispatchers.services.logger") as mock_logger,
        ):
            mock_registry.get.return_value = _async_task
            mock_session = _mock_session()
            mock_result = MagicMock()
            mock_result.rowcount = 0
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_tx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.commit = AsyncMock()

            mock_update.return_value.where.return_value.values.return_value = "mocked_stmt"

            short_id = str(config.id).split("-")[0]
            prefix = f"[sch:{config.name}|{short_id}]"

            with patch("app.features.dispatchers.services.ScheduleJob") as mock_sj:
                mock_sj.id = MagicMock()
                mock_sj.retry_attempts = 0
                await service._run_dispatch(job, config, run_id=run_id)

            mock_logger.error.assert_called_with(f"{prefix} Failed to update ScheduleJob - not found")
''')


content = re.sub(
    r"class TestRunDispatch:.*?# ---------------------------------------------------------------------------",
    new_test + "\n\n# ---------------------------------------------------------------------------",
    content,
    flags=re.DOTALL,
)

with open("modules/hub/tests/unit/test_dispatchers/test_dispatcher_services.py", "w") as f:
    f.write(content)
