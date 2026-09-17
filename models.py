from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str


class ContextBlock(BaseModel):
    source: str
    start_page: int
    end_page: int
    start_chunk_index: int
    end_chunk_index: int
    text: str
    distance: float
