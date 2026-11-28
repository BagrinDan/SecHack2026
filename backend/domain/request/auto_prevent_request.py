from pydantic import BaseModel


class AutoPreventRequest(BaseModel):
    enabled: bool
