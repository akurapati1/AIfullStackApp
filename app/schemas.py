from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str


class Message(BaseModel):
    role: str
    content: str
    created_at: str


class Conversation(BaseModel):
    id: str
    title: str
    created_at: str
