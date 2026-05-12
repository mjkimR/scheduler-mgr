from typing import Any, Type, TypeVar, get_args

import pytest
from app_base.base.models.mixin import Base
from app_base.base.repos.base import BaseRepository
from httpx import AsyncClient
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from tests.utils.fastapi import resolve_dependency

T = TypeVar("T", bound=BaseModel)


@pytest.fixture
def make():
    """Pydantic model factory fixture.

    Usage: make(User, name="test")
    - model_class: Pydantic model class to create
    - kwargs: fields to override in the factory
    """

    def _make(model_class: Type[T], **kwargs: Any) -> T:
        factory = ModelFactory.create_factory(model_class)
        return factory.build(**kwargs)

    return _make


@pytest.fixture
def make_batch():
    """Pydantic model batch factory fixture.

    Usage: make_batch(User, 3, name="test")
    - model_class: Pydantic model class to create
    - _size: number of models to create (default: 3)
    - kwargs: fields to override in the factory
    """

    def _make_batch(model_class: Type[T], _size: int = 3, **kwargs: Any) -> list[T]:
        factory = ModelFactory.create_factory(model_class)
        return factory.batch(size=_size, **kwargs)

    return _make_batch


def _find_generic_args(repo_class: type[BaseRepository]) -> type[BaseModel]:
    """Extract generic type arguments from a BaseRepository subclass."""
    if not issubclass(repo_class, BaseRepository):
        raise ValueError(f"{repo_class.__name__} is not a subclass of BaseRepository.")
    if not hasattr(repo_class, "__orig_bases__"):
        raise ValueError(f"{repo_class.__name__} does not have __orig_bases__ attribute.")
    orig_bases = repo_class.__orig_bases__  # type: ignore
    generic_args = get_args(orig_bases[0])
    create_schema_type = generic_args[1]
    return create_schema_type


@pytest.fixture
def make_db(session: AsyncSession):
    """SQLAlchemy model factory fixture. (with repo creation)

    Usage: await make_db(UserRepository, name="test")
    - repo_class_or_instance: repo class or instance to use for creating the model (e.g., UserRepository)
    - kwargs: fields to override in the factory

    Returns the created SQLAlchemy model instance after saving to the database.
    """

    async def _make_db(repo_class_or_instance: type[BaseRepository] | BaseRepository, **kwargs: Any) -> Base:
        if not isinstance(repo_class_or_instance, type):
            repo_class = type(repo_class_or_instance)
            repo = repo_class_or_instance
        else:
            repo_class = repo_class_or_instance
            repo = resolve_dependency(repo_class_or_instance)
        create_schema_type = _find_generic_args(repo_class)
        factory = ModelFactory.create_factory(create_schema_type)
        data = factory.build()
        return await repo.create(session, data, **kwargs)

    return _make_db


@pytest.fixture
def make_db_batch(session: AsyncSession):
    """SQLAlchemy model batch factory fixture. (with repo creation)

    Usage: await make_db_batch(UserRepository, 3)
    - repo_class_or_instance: Repo class or instance to use for creating the models (e.g., UserRepository)
    - _size: number of models to create (default: 3)
    - kwargs: fields to override in the factory

    Returns a list of created SQLAlchemy model instances after saving to the database.
    """

    async def _make_db_batch(
        repo_class_or_instance: BaseRepository | type[BaseRepository], _size: int = 3, **kwargs: Any
    ) -> list[Base]:
        if not isinstance(repo_class_or_instance, type):
            repo_class = type(repo_class_or_instance)
            repo = repo_class_or_instance
        else:
            repo_class = repo_class_or_instance
            repo = resolve_dependency(repo_class_or_instance)
        create_schema_type = _find_generic_args(repo_class)
        factory = ModelFactory.create_factory(create_schema_type)
        data_list = factory.batch(size=_size)
        results = []
        for data in data_list:
            results.append(await repo.create(session, data, **kwargs))
        return results

    return _make_db_batch


@pytest.fixture
def make_api(client: AsyncClient):
    """API model factory fixture.

    Usage: await make_api("/users/", UserCreate, name="test")
    - endpoint: API endpoint to create the model
    - model_class: Pydantic model class for the request body
    - kwargs: fields to override in the factory
    """

    async def _make_api(endpoint: str, model_class: Type[T], **kwargs: Any) -> T:
        factory = ModelFactory.create_factory(model_class)
        data = factory.build(**kwargs)
        response = await client.post(endpoint, json=data.model_dump())
        response.raise_for_status()
        return model_class.model_validate(response.json())

    return _make_api


@pytest.fixture
def make_api_batch(client: AsyncClient):
    """API model batch factory fixture.

    Usage: await make_api_batch("/users/batch", UserCreate, 3, name="test")
    - endpoint: API endpoint to create the models
    - model_class: Pydantic model class for the request body
    - _size: number of models to create (default: 3)
    - kwargs: fields to override in the factory
    """

    async def _make_api_batch(endpoint: str, model_class: Type[T], _size: int = 3, **kwargs: Any) -> list[T]:
        factory = ModelFactory.create_factory(model_class)
        data_list = factory.batch(size=_size, **kwargs)
        payload = [data.model_dump() for data in data_list]
        response = await client.post(endpoint, json=payload)
        response.raise_for_status()
        return [model_class.model_validate(item) for item in response.json()]

    return _make_api_batch
