from pydantic import BaseModel

from domain.enums import AppMode


class ModeResponse(BaseModel):
    mode: AppMode
