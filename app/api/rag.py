from fastapi import APIRouter

from app.schemas.rag import RAGSearchRequest, RAGSearchResponse, RAGChunkResult
from app.services.rag_service import search_knowledge
from app.chains.rag_answer_chain import generate_rag_answer
from app.services.llm_service import LLMNotConfiguredError, LLM_NOT_CONFIGURED_MSG

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/search", response_model=RAGSearchResponse)
async def rag_search(req: RAGSearchRequest):
    chunks = await search_knowledge(
        query=req.query,
        agent_name=req.agent_name or "",
        top_k=req.top_k,
    )

    results = [
        RAGChunkResult(
            doc_id=c["doc_id"],
            doc_title=c["doc_title"],
            chunk_index=c["chunk_index"],
            content=c["content"],
            score=c["score"],
        )
        for c in chunks
    ]

    answer = None
    try:
        answer = await generate_rag_answer(
            query=req.query,
            context_chunks=[c["content"] for c in chunks],
        )
    except LLMNotConfiguredError:
        answer = LLM_NOT_CONFIGURED_MSG

    return RAGSearchResponse(query=req.query, results=results, answer=answer)
