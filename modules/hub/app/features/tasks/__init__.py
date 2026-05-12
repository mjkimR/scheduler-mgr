import importlib
import pkgutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

_registry: dict[str, Callable[..., Any]] = {}


def task(name: str | None = None) -> Callable:
    """Register a function as a dispatchable task.

    Usage:
        @task()
        async def my_task(foo: str, bar: int = 0): ...

        @task(name="custom.name")
        async def my_task(foo: str): ...
    """

    def decorator(fn: Callable) -> Callable:
        key = name if name is not None else fn.__name__
        if key in _registry:
            raise ValueError(f"Task '{key}' is already registered.")
        _registry[key] = fn
        return fn

    return decorator


def get(name: str) -> Callable:
    """Look up a registered task by name. Raises KeyError if not found."""
    if name not in _registry:
        raise KeyError(f"Task '{name}' is not registered. Available tasks: {list(_registry)}")
    return _registry[name]


def all_tasks() -> dict[str, Callable]:
    """Return a copy of the full registry."""
    return dict(_registry)


def autodiscover() -> None:
    """Import all modules in the tasks package so that @task decorators are registered.

    Call this once at application startup (e.g. in lifespan):
        from app.features import tasks
        tasks.autodiscover()
    """
    package_dir = Path(__file__).parent
    package_name = __name__

    for module_info in pkgutil.iter_modules([str(package_dir)]):
        importlib.import_module(f"{package_name}.{module_info.name}")
