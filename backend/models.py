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
    # Distance of the match this chunk came from (neighbours inherit it).
    # Only used to decide what to trim when a block is too big.
    distance: float = 0.0


class ContextBlock(BaseModel):
    source: str
    chunks: list[RetrievedChunk]
    distance: float
