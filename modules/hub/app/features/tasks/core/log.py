"""Task-aware logger that automatically includes :class:`TaskMeta` in every log record.

Usage inside a task function::

    from app.features.tasks.base.log import task_logger

    async def my_task(**payload):
        task_logger.info("Processing started")
        # => logs will include config_id, config_name, run_id from the current context
"""

from __future__ import annotations

from app.features.tasks.core.context import get_task_meta
from app_base.core.log import logger as core_logger


class _TaskLogger:
    """Thin wrapper around the global loguru ``logger``.

    Every log call reads :func:`get_task_meta` from the current
    :class:`~contextvars.ContextVar` and binds ``config_id``,
    ``config_name``, and ``run_id`` to the log record via
    :meth:`loguru.Logger.bind`.

    If no :class:`TaskMeta` is set (i.e. the code is running outside a
    dispatched task), the underlying logger is used as-is.
    """

    __slots__ = ()

    def _bound_logger(self):
        meta = get_task_meta()
        if meta is None:
            return core_logger
        return core_logger.bind(
            config_id=str(meta.config_id),
            config_name=meta.config_name,
            run_id=str(meta.run_id),
        )

    @staticmethod
    def _prefix() -> str:
        meta = get_task_meta()
        if meta is None:
            return ""
        return f"[{meta.config_name}][run:{meta.run_id}] "

    def debug(self, message: str, *args, **kwargs):
        self._bound_logger().opt(depth=1).debug(self._prefix() + message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self._bound_logger().opt(depth=1).info(self._prefix() + message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self._bound_logger().opt(depth=1).warning(self._prefix() + message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self._bound_logger().opt(depth=1).error(self._prefix() + message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        self._bound_logger().opt(depth=1).critical(self._prefix() + message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        self._bound_logger().opt(depth=1).exception(self._prefix() + message, *args, **kwargs)


logger = _TaskLogger()
