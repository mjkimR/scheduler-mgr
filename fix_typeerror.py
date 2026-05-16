
with open("modules/hub/tests/unit/test_dispatchers/test_dispatcher_services.py", "r") as f:
    content = f.read()

content = content.replace(
    """    @pytest.mark.asyncio
    async def test_job_not_found_in_db_does_not_raise(self, service, job, config, run_id):
        \"\"\"Even if the job is not found in DB, it should complete without raising an exception.\"\"\"

        async def _async_task(**kwargs):
            pass

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
            service.job_repo.get_by_pk = AsyncMock(return_value=None)  # job not found

            # Should complete without raising an exception
            await service._run_dispatch(job, config, run_id=run_id)""",
    """    @pytest.mark.asyncio
    async def test_job_not_found_in_db_does_not_raise(self, service, job, config, run_id):
        \"\"\"Even if the job is not found in DB, it should complete without raising an exception.\"\"\"

        async def _async_task(**kwargs):
            pass

        patcher = patch('app.features.dispatchers.services.ScheduleJob')
        mock_sj = patcher.start()
        mock_sj.retry_attempts = 0

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
            mock_session.execute = AsyncMock(return_value=MagicMock(rowcount=0))

            # Should complete without raising an exception
            await service._run_dispatch(job, config, run_id=run_id)

        patcher.stop()""",
)

with open("modules/hub/tests/unit/test_dispatchers/test_dispatcher_services.py", "w") as f:
    f.write(content)
