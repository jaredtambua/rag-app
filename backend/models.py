from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str


class RetrievedChunk(BaseModel):
    page: int
    chunk_index: int
    text: str


class ContextBlock(BaseModel):
    source: str
    chunks: list[RetrievedChunk]
    distance: float
