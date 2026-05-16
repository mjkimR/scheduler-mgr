
with open("modules/hub/tests/unit/test_dispatchers/test_dispatcher_services.py", "r") as f:
    content = f.read()

content = content.replace(
    "job_obj = self._mock_job_obj()",
    "job_obj = self._mock_job_obj()\n        patcher = patch('app.features.dispatchers.services.ScheduleJob')\n        mock_sj = patcher.start()\n        mock_sj.retry_attempts = 0",
)
content = content.replace("assert job_obj.status", "patcher.stop()\n        assert job_obj.status")

with open("modules/hub/tests/unit/test_dispatchers/test_dispatcher_services.py", "w") as f:
    f.write(content)
