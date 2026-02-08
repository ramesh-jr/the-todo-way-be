"""Generic API response wrapper."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata included in list responses."""

    total: int
    page: int
    per_page: int
    total_pages: int


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response envelope wrapping all endpoint responses."""

    data: T
    error: str | None = None
    meta: PaginationMeta | None = None
