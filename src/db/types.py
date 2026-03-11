"""Custom SQLAlchemy column types used by the app."""

from __future__ import annotations

from sqlalchemy.types import UserDefinedType


class Vector(UserDefinedType):
    """PGVector column type for migrations and ORM models."""

    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_: object) -> str:
        return f"VECTOR({self.dimensions})"

    def bind_processor(self, dialect):
        del dialect
        return None

    def result_processor(self, dialect, coltype):
        del dialect, coltype
        return None
