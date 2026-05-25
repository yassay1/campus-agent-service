from pydantic import BaseModel, Field
from typing import Optional


class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2048)
    agent_name: Optional[str] = Field(None, description="限定搜索的 Agent 知识库范围")
    top_k: int = Field(default=5, ge=1, le=20)


class RAGChunkResult(BaseModel):
    doc_id: str
    doc_title: str
    chunk_index: int
    content: str
    score: float


class RAGSearchResponse(BaseModel):
    query: str
    results: list[RAGChunkResult]
    answer: Optional[str] = Field(None, description="LLM 基于检索结果生成的回答")
