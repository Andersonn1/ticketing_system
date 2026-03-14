"""Custom SQLAlchemy column types used by the app."""

from __future__ import annotations

from sqlalchemy.types import UserDefinedType


class Vector(UserDefinedType):
    """PGVector column type for migrations and ORM models."""

    cache_ok = True
    __slots__ = "dimensions"

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_: object) -> str:
        return f"VECTOR({self.dimensions})"

    def bind_processor(self, dialect):
        del dialect

        def process(value: list[float] | tuple[float, ...] | str | None) -> str | None:
            if value is None:
                return None
            if isinstance(value, str):
                return value
            return "[" + ",".join(f"{float(item):.8f}" for item in value) + "]"

        return process

    def result_processor(self, dialect, coltype):
        del dialect, coltype

        def process(value: str | None) -> list[float] | None:
            if value is None:
                return None
            normalized = value.strip()
            if not normalized:
                return []
            if normalized[0] == "[" and normalized[-1] == "]":
                normalized = normalized[1:-1]
            if not normalized:
                return []
            return [float(item) for item in normalized.split(",")]

        return process
