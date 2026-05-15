# Scheduler Manager

## Overview

This is a personal project. Its primary purpose is for personal use, future reference, and to provide context to AI assistants.

It provides a lightweight hub for dispatching scheduled jobs dynamically, supporting both cron-based and interval-based task executions.

## Key Features & Architecture

The project follows Clean Architecture principles (API -> UseCase -> Service -> Repository):

*   **Dynamic Task Discovery**: Tasks are automatically discovered on application startup via `tasks.autodiscover()`.
*   **Atomic Dispatching**: Uses `AsyncTransaction` and `FOR UPDATE SKIP LOCKED` pattern when fetching due schedules. This guarantees that even if multiple dispatchers are triggered simultaneously (e.g., Cloud Run scaling), no task is executed twice.
*   **Resilience & Retries**: Built-in logic retrieves and automatically retries previously failed jobs, clearing past error messages to ensure fault tolerance.
*   **Flexible Scheduling**: Supports both `cron_expression` and `interval_seconds`, with JSON-based `payload` parameters to pass context into tasks.
*   **Task Specification API**: Exposes `/api/v1/tasks/specs` which provides auto-generated JSON schemas for all registered task payloads, facilitating front-end integration or manual triggering.
*   **System Configuration**: Includes a `SystemConfig` store for managing global application state or feature flags without code changes.

## Observability & Tracing

*   **Context-Aware Logging**: Uses `Loguru` integrated with `ContextVars`. The `task_logger` automatically binds `config_id`, `config_name`, and `run_id` to every log record within a task execution, enabling seamless tracing in Google Cloud Logging.
*   **Execution History**: Every dispatch attempt is recorded in `ScheduleJob` with status, timing, and full traceback on failure.

## Task Development Guide

To add a new task, simply decorate an async function with `@task()`:

```python
from app.features.tasks import task
from app.features.tasks.core.log import logger
from pydantic import BaseModel

class MyPayload(BaseModel):
    user_id: int

@task(name="custom.my_task")
async def my_task(payload: MyPayload):
    logger.info(f"Processing user {payload.user_id}")
    # ... business logic ...
```

Tasks are automatically registered if they reside within the `app.features.tasks` package (or submodules).

## Testing Strategy

We follow the **Test Trophy** model, prioritizing **Integration** and **E2E** tests for high refactoring resilience.

*   **E2E Tests**: Verify the full API-to-DB flow using `httpx.AsyncClient`.
*   **Integration Tests**: Test core logic (e.g., `DispatcherService`) with a real in-memory SQLite database.
*   **Unit Tests**: Reserved for complex isolated logic like schedule calculations.

See [modules/hub/tests/GUIDE.md](modules/hub/tests/GUIDE.md) for the full testing philosophy and tool usage (`make_db`, `resolve_dependency`).

## Stack

*   **Language**: Python 3.13
*   **Framework**: FastAPI
*   **Database & ORM**: SQLAlchemy 2.0 (Async), Alembic migrations, PostgreSQL (Production) / SQLite (Testing)
*   **Tooling**: `uv` (Package Management), `ruff` (Lint/Format), `pyright` (Type Checking)

## Local Development

```bash
# 1. Install dependencies using uv
uv sync

# 2. Run database migrations
cd modules/hub
alembic upgrade head

# 3. Start the local development server (Runs on port 8389)
fastapi dev app/main.py
```

## Cloud Architecture & Deployment

The application is designed to be deployed natively on **Google Cloud Platform (GCP)**:
*   **Backend Application**: Hosted on **Google Cloud Run**.
*   **Triggering Mechanism**: **Google Cloud Scheduler** periodically calls the `/api/v1/dispatchers/trigger` endpoint.

### ⚠️ Critical Deployment Note: Timeout Configuration

Because the HTTP response is blocked until all dispatched jobs complete, you **must align timeouts across three layers**:
1.  **Application Middleware**: Internal `timeout_middleware` in `app/main.py`.
2.  **Google Cloud Run**: Container timeout limit (e.g., 300s+).
3.  **Google Cloud Scheduler**: HTTP execution timeout.
