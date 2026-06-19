from typing import List

from pydantic import BaseModel

from app.api.v1.schemas.terminal_schemas import ShiftResponseSchema


class HubShiftResponseSchema(BaseModel):
    terminal_id: str
    shifts_count: int
    shifts: List[ShiftResponseSchema]
