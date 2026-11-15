from pydantic import BaseModel


class HistoryTurn(BaseModel):
    question: str
    answer: str


class QuestionRequest(BaseModel):
    question: str
    # Earlier question-and-answer pairs, oldest first. Checked in followup.py.
    history: list[HistoryTurn] | None = None


class RetrievedChunk(BaseModel):
    page: int
    chunk_index: int
    text: str


class ContextBlock(BaseModel):
    source: str
    chunks: list[RetrievedChunk]
    distance: float
