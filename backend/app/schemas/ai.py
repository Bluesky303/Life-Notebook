from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    provider: str = Field(default="codex", description="codex/openai-compatible/ollama")
    session_id: str | None = None
    prompt: str


class AIChatResponse(BaseModel):
    provider: str
    session_id: str
    reply: str


class AIParseRecordRequest(BaseModel):
    text: str


class AIParseRecordResponse(BaseModel):
    detected_type: str
    suggested_category: str
    normalized_text: str
    extracted_amount: str | None = None
    extracted_time: str | None = None
