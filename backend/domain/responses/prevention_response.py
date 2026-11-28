from pydantic import BaseModel


class PreventionResponse(BaseModel):
    enabled: bool
