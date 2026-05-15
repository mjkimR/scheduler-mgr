import pytest
from app.features.schedule_configs.schemas import ScheduleConfigCreate, ScheduleConfigPatch


def test_schedule_config_create_invalid_cron():
    with pytest.raises(ValueError) as exc:
        ScheduleConfigCreate(
            name="Invalid Cron",
            task_func="tasks.dummy",
            cron_expression="invalid cron expression",
        )
    assert "Invalid cron_expression" in str(exc.value)


def test_schedule_config_create_mutually_exclusive_triggers():
    with pytest.raises(ValueError) as exc:
        ScheduleConfigCreate(
            name="Both Triggers",
            task_func="tasks.dummy",
            cron_expression="0 0 * * *",
            interval_seconds=60,
        )
    assert "cron_expression and interval_seconds are mutually exclusive." in str(exc.value)


def test_schedule_config_create_missing_triggers():
    with pytest.raises(ValueError) as exc:
        ScheduleConfigCreate(
            name="No Triggers",
            task_func="tasks.dummy",
        )
    assert "Either cron_expression or interval_seconds must be provided." in str(exc.value)


def test_schedule_config_patch_invalid_cron():
    with pytest.raises(ValueError) as exc:
        ScheduleConfigPatch(
            cron_expression="invalid cron expression",
        )
    assert "Invalid cron_expression" in str(exc.value)


def test_schedule_config_patch_mutually_exclusive_triggers():
    with pytest.raises(ValueError) as exc:
        ScheduleConfigPatch(
            cron_expression="0 0 * * *",
            interval_seconds=60,
        )
    assert "cron_expression and interval_seconds are mutually exclusive." in str(exc.value)
