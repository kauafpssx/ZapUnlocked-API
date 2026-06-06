from pydantic import BaseModel


class AiAskRequest(BaseModel):
    message: str


class AiImagineRequest(BaseModel):
    prompt: str
