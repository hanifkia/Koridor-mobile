from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total_count: int
    total_pages: int
    current_page: int
    per_page: int
    has_next: bool
    has_previous: bool
