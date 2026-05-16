
with open("modules/hub/tests/unit/test_dispatchers/test_dispatcher_services.py", "r") as f:
    content = f.read()

content = content.replace("job_obj.retry_attempts = 0", "")
content = content.replace("job_obj = self._mock_job_obj()", "")
content = content.replace("job_obj", "job")

with open("modules/hub/tests/unit/test_dispatchers/test_dispatcher_services.py", "w") as f:
    f.write(content)
