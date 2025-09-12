from pydantic import BaseModel


class MessageRequest(BaseModel):
    message: str
    user_id: str


class MessageResponse(BaseModel):
    response: str
    processing_time: float
