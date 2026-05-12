# Testing Guide for Hub Module

This guide outlines the conventions and best practices for writing tests within the Hub module. Adhering to these guidelines ensures consistency, maintainability, and clarity across our test suite.

## 1. Test Strategy & Priorities

### 1.1 Test Trophy Model (Not Pyramid)

We follow the **Test Trophy** model over the traditional Test Pyramid. This prioritizes **refactoring resilience** and **ROI** over sheer test count.

- E2E (critical flows)
- Integration (primary focus, core)
- Unit (selective)

### 1.2 Test Type Selection Guide

| Scenario                                          | Recommended Test   | Reason                                         |
| ------------------------------------------------- | ------------------ | ---------------------------------------------- |
| CRUD API                                          | E2E                | Interface-based, stable across refactoring     |
| Multiple services/components                      | Integration        | Real interaction verification, minimal mocking |
| Complex business logic (calculations, validation) | Unit               | Only for pure, isolated functions              |
| External API integration                          | Integration + Mock | Isolate only external dependencies             |
| Simple delegation/proxy logic                     | Skip               | Low ROI                                        |

### 1.3 Unit Test: When to Write (and When NOT to)

**✅ DO write Unit Tests when:**

- Complex conditional business logic (pricing calculations, permission checks, etc.)
- Pure utility/helper functions with no external dependencies
- Algorithms requiring rapid verification of diverse input combinations

**❌ DO NOT write Unit Tests when:**

- Simple CRUD operations (E2E is sufficient)
- Service → Repository simple delegation (Integration is sufficient)
- Tests tightly coupled to implementation details (breaks on refactoring)
- Tests requiring 3+ mocks (consider switching to Integration)

### 1.4 Refactoring Resilience Principle

**A good test = A test that doesn't break when you refactor**

- **Test the interface (API contract)**, not the implementation
- If a test breaks when you change internal method signatures, it's coupled to implementation
- E2E/Integration tests are based on public interfaces, so they have high refactoring resilience

### 1.5 Priority Order for New Features

Test writing priority when developing new features:

1. **E2E**: Critical user flows (Happy path + major error cases)
2. **Integration**: Service layer with complex business logic
3. **Unit**: Complex logic isolated into pure functions (selective)

> ⚠️ **When requesting tests from AI**: If test type is not specified, E2E or Integration will be recommended based on the above priorities.

---

## 2. Test Directory Structure

Tests are organized by their scope and the module they belong to. For the `tasks` module, the structure is as follows:

```
tests/
├── unit/
│   └── test_tasks/
│       ├── test_task_histories/
│       │   └── test_task_histories_usecases.py
│       └── ... (other task submodules unit tests)
├── integrate/
│   └── test_tasks/
│       ├── test_task_histories/
│       │   ├── test_create_task_history.py
│       │   └── test_get_task_history.py
│       ├── test_tasks/
│       │   ├── test_create_task.py
│       │   ├── test_update_task.py
│       │   └── test_get_task.py
│       └── ...
└── e2e/
    └── test_tasks/
        ├── test_task_histories/
        │   └── test_task_histories_api.py
        └── ...
```

- **`unit/`**:
  - **Purpose**: Tests individual components (e.g., use cases, services, repositories) in isolation.
  - **Characteristics**: Heavily relies on mocking dependencies to ensure only the target component's logic is tested. The database is typically mocked or not involved.
  - **Naming**: `test_<component_name>_usecases.py`, `test_<component_name>_services.py`, etc.

- **`integrate/`**:
  - **Purpose**: Tests the interaction between several components, typically involving the database.
  - **Characteristics**: Uses a real database session (provided by the `session` fixture). Dependencies _within_ the tested flow are usually real, while external services might still be mocked.
  - **Naming**: `test_<component_name>_service.py` (e.g., service and repo interaction).

- **`e2e/`**:
  - **Purpose**: Tests the entire application flow from the API endpoint down to the database.
  - **Characteristics**: Uses an HTTP client (`client` fixture) to make requests to the FastAPI application. Involves the full stack, including routing, dependency injection, services, and the database.
  - **Naming**: `test_<component_name>_api.py`.

## 3. Naming Conventions

- **Test Files**:
  - **Unit/E2E**: `test_<module_or_submodule_name>_<scope>.py` (e.g., `test_task_histories_api.py`).
  - **Integration (Preferred)**: `test_<operation>_<entity>.py` (e.g., `test_create_task.py`, `test_update_task_tag.py`).
- **Test Classes**: `Test<Operation><Entity>` (e.g., `TestCreateTask`, `TestUpdateTaskTag`).
- **Test Functions**: `test_<action_being_tested>_<expected_outcome>` (e.g., `test_create_task_history_success`).

## 4. Fixtures Usage

We leverage a rich set of pytest fixtures defined in `tests/conftest.py` and `tests/fixtures/`.

- **`session: AsyncSession`**: (from `tests/fixtures/db.py`)
  - Provides an asynchronous SQLAlchemy session connected to the test database.
  - **Use in**: Integration and E2E tests (implicitly by the app/client setup, or explicitly for direct DB interaction).
  - **Behavior**: Each test gets a fresh session, and changes are committed at the end of the test.

- **`client: AsyncClient`**: (from `tests/fixtures/clients.py`)
  - An `httpx.AsyncClient` configured to interact with the FastAPI application directly, bypassing network calls. It's pre-configured to use the test database session.
  - **Use in**: E2E tests for making API requests.

- **`make: Callable`**: (from `tests/fixtures/data_factory.py`)
  - A factory for creating Pydantic models. Does NOT interact with the database.
  - **Usage**: `make(MyPydanticSchema, field_name="value")`

- **`make_batch: Callable`**: (from `tests/fixtures/data_factory.py`)
  - A factory for creating a batch of Pydantic models. Does NOT interact with the database.
  - **Usage**: `make_batch(MyPydanticSchema, _size=5, field_name="value")`

- **`make_db: Callable`**: (from `tests/fixtures/data_factory.py`)
  - A factory for creating SQLAlchemy models via Repository, adding them to the test database session.
  - **Usage**: `await make_db(MyRepository, field_name="value")` or `await make_db(repo_instance, field_name="value")`
  - Takes a Repository class or instance, automatically extracts the CreateSchema type from the repository's generic arguments.
  - Returns the created SQLAlchemy model instance after saving to the database.

- **`make_db_batch: Callable`**: (from `tests/fixtures/data_factory.py`)
  - A factory for creating a batch of SQLAlchemy models via Repository and adding them to the test database session.
  - **Usage**: `await make_db_batch(MyRepository, _size=5, field_name="value")`
  - Takes a Repository class or instance, automatically extracts the CreateSchema type from the repository's generic arguments.
  - Returns a list of created SQLAlchemy model instances.

## 5. Assertion Helpers (`tests/utils/assertions.py`)

Always prefer using the assertion helpers provided in `tests/utils/assertions.py` for common checks:

- **`assert_status_code(response, expected_status)`**: Checks HTTP status code.
- **`assert_json_contains(response, expected_dict)`**: Checks if a JSON response contains specific key-value pairs.
- **`assert_paginated_response(response, min_items=0)`**: Validates the structure of a paginated API response.
- **`assert_error_response(response, status_code, error_type=None)`**: Validates the structure of an API error response.
- **`assert_model_fields(obj, expected_dict)`**: Checks specific fields of a Pydantic or SQLAlchemy model object.

## 6. Mocking (for Unit Tests)

For unit tests, use `unittest.mock` or `pytest-mock` to isolate the component under test.

- Mock dependencies injected via FastAPI's `Depends` (e.g., services, repositories).
- Use `AsyncMock` for async functions.
- Configure `return_value` or `side_effect` for mock objects to simulate behavior.

## 7. Dependency Resolution Helper (`resolve_dependency`)

### 7.1 Purpose

The `resolve_dependency` function (located in `tests/utils/fastapi.py`) is a test utility that automatically resolves FastAPI dependency injection trees. This eliminates the need to manually instantiate services, repositories, and use cases with their dependencies.

### 7.2 Key Benefits

- **Automatic Dependency Resolution**: Recursively resolves all `Depends()` declarations in constructors
- **Cleaner Test Code**: No need to manually create dependency chains
- **Refactoring Resilience**: Tests don't break when you add/remove dependencies
- **Flexibility**: Supports overriding specific dependencies with mocks when needed

### 7.3 Basic Usage

**Before (Manual Instantiation):**

```python
# ❌ Manually creating all dependencies
service = TaskTagService(repo=None, repo_workspace=None)
use_case = CreateTaskTagUseCase(service=service)
```

**After (Using resolve_dependency):**

```python
# ✅ Automatic dependency resolution
from tests.utils.fastapi import resolve_dependency

use_case = resolve_dependency(CreateTaskTagUseCase)
```

### 7.4 Advanced Usage: Overriding Dependencies

For integration tests where you need to inject specific objects (e.g., mock session, test database):

```python
from tests.utils.fastapi import resolve_dependency

# Override specific dependencies
use_case = resolve_dependency(
    CreateTaskUseCase,
    state={"db": session},  # Inject request.state values
    overrides={get_db: mock_session}  # Replace specific dependency functions
)
```

### 7.5 When to Use

- **✅ DO use** in Integration and Unit tests when instantiating services/use cases
- **✅ DO use** when you want to test with real dependency chains
- **❌ DON'T use** in E2E tests (use `client` fixture instead, which handles DI automatically)
- **❌ DON'T use** if you need to mock ALL dependencies (use direct mocking instead)

### 7.6 How It Works

The function inspects the target class/function signature and:

1. Checks for `overrides` dictionary first (highest priority)
2. Detects `Request` objects and injects `MockRequest` with state
3. Resolves `Annotated[Type, Depends(...)]` patterns
4. Resolves `Depends(...)` default values
5. Recursively resolves nested dependencies
6. Returns a fully instantiated object

For more details, see the implementation in `tests/utils/fastapi.py`.

## 8. Guide for AI (When Requesting New Tests)

When asking the AI to write new tests, please provide the following information:

- **Target Module/Resource**: Clearly specify which part of the application needs testing (e.g., `app/tasks/tasks`, `app/tasks/task_tags`, `app/agents/configured_agents`).
- **Test Type**: Specify whether you need `unit`, `integrate`, or `e2e` tests. If unsure, describe the scope, and the AI can recommend.
- **Endpoints/Functions to Test**: For E2E, list the HTTP methods and paths (e.g., `POST /workspace/{workspace_id}/tasks`). For unit/integration, specify the class and method (e.g., `CreateTaskUseCase.execute`).
- **Expected Behavior**: Describe the successful outcomes, including expected data, status codes, and database changes.
- **Edge Cases/Error Scenarios**: Provide details on invalid inputs, missing resources, authorization failures, or other error conditions, along with their expected error responses.
- **Existing Dependencies**: Mention any special setup required, e.g., "This test requires an existing Workspace and Task."
- **Special Data Needs**: If the test requires specific data values or relationships, describe them.

### Example Request for AI:

"Please create an E2E test for `app/tasks/task_tags`.
Test the `POST /workspace/{workspace_id}/task_tags` endpoint.
**Expected Success**:

- Creates a new tag with a unique name in the given workspace.
- Returns 201 status code and the created tag object.
  **Edge Cases**:
- Attempting to create a tag with a name that already exists in the same workspace should return a 409 Conflict.
- Attempting to create a tag without authentication should return 401 Unauthorized."

### E2E Test Best Practices (Important!)

When writing E2E API tests, follow these critical conventions:

1. **API Path Prefix**: All API paths MUST start with `/api/v[version]/...`

   ```python
   # ✅ Correct
   response = await client.post(f"/api/v1/workspace/{workspace.id}/tasks", ...)

   # ❌ Wrong
   response = await client.post(f"/workspace/{workspace.id}/tasks", ...)
   ```

2. **Use Repository Classes in `make_db`, NOT SQLAlchemy Models directly**

   ```python
   # ✅ Correct - Use Repository class for DB fixtures
   from app.tasks.tasks.repos import TaskRepository
   task: Task = await make_db(TaskRepository, workspace_id=workspace.id, title="Test Task")

   # ✅ Also correct - Use Repository instance
   repo = resolve_dependency(TaskRepository)
   task: Task = await make_db(repo, workspace_id=workspace.id)

   # ❌ Wrong - Don't use Pydantic schemas with make_db
   from app.tasks.tasks.schemas import TaskRead  # Pydantic schema
   task: TaskRead = await make_db(TaskRead, ...)  # This will fail!
   ```

3. **Workspace Creation**: Always create non-default workspaces in tests

   ```python
   # ✅ Correct
   from app.platform.workspaces.repos import WorkspaceRepository
   workspace: Workspace = await make_db(WorkspaceRepository, is_default=False)

   # ❌ Avoid (unless testing default workspace behavior)
   workspace: Workspace = await make_db(WorkspaceRepository)  # Might create default workspace
   ```

4. **DELETE Response Validation**: Check the `identity` field, not just the message

   ```python
   # ✅ Correct - Verify identity field
   response = await client.delete(f"/api/v1/workspace/{workspace.id}/tasks/{task.id}")
   assert_status_code(response, 200)
   response_json = response.json()
   assert "message" in response_json
   assert response_json["identity"] == str(task.id)  # Verify the deleted resource ID

   # ❌ Wrong - Only checking if ID is in message string
   assert str(task.id) in response_json["message"]  # Too vague
   ```

5. **Parent Resource Dependencies**: Always create required parent resources (workspace, task, etc.)

   ```python
   # ✅ Correct - Create full dependency chain using Repository classes
   from app.platform.workspaces.repos import WorkspaceRepository
   from app.tasks.tasks.repos import TaskRepository
   from app.tasks.task_histories.repos import TaskHistoryRepository

   workspace: Workspace = await make_db(WorkspaceRepository, is_default=False)
   task: Task = await make_db(TaskRepository, workspace_id=workspace.id)
   task_history: TaskHistory = await make_db(TaskHistoryRepository, workspace_id=workspace.id, task_id=task.id)
   ```

## 9. Common Pitfalls / Best Practices

- **Avoid over-mocking in integration/E2E tests**: Only mock external systems that are truly outside the scope of the integration.
- **Don't test framework specifics**: Avoid testing FastAPI's routing or Pydantic's validation directly; assume the framework works correctly.
- **Make tests readable**: Use clear variable names, comments where necessary, and separate test stages (Given, When, Then).
- **Test data setup**: Use `make_db` and `make_db_batch` with Repository classes (not SQLAlchemy models) to create realistic but minimal test data. The factory automatically extracts the CreateSchema from the repository's generic arguments. Avoid hardcoding IDs unless absolutely necessary.
- **Clean up**: The `session` fixture automatically handles transaction rollback, so explicit cleanup is rarely needed for DB state. For file system or other external resources, ensure proper teardown.

## 10. Database Session Caching & `inspect_session`

> ⚠️ **Critical for Integration Tests**: The `session` fixture shares the same SQLAlchemy Identity Map as the code under test (when using `resolve_dependency` with the test session).

**The Problem**:
When you update or delete an object using a Service/UseCase, the test `session` might still hold the **old, cached version** of the object. Calling `await session.get(...)` might return this stale object instead of fetching the new state from the DB (or returning None for deletions).

**The Solution**:
Use the `inspect_session` fixture for verification steps. This is a separate session intended solely for inspecting the database state, ensuring you see what was actually persisted (flushed) to the database.

**Example (Delete Test):**

```python
# ❌ Bad: Might return the cached, non-deleted object
await delete_use_case.execute(task.id, context=context)
db_task = await session.get(Task, task.id)
assert db_task is None  # Fails!

# ✅ Good: Use inspect_session to verify DB state
await delete_use_case.execute(task.id, context=context)
db_task = await inspect_session.get(Task, task.id)
assert db_task is None  # Passes
```

**Example (Update Test):**

```python
# Alternative: Use session.refresh() if reusing the same session
await update_use_case.execute(task.id, update_data, ...)
db_task = await session.get(Task, task.id)
await session.refresh(db_task) # Force reload
```
