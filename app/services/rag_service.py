"""Real RAG service using pgvector + OpenAI embeddings."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config.settings import get_settings
from app.services.llm_service import check_llm_configured

logger = logging.getLogger(__name__)


async def _get_embedding(text: str) -> list[float]:
    """使用 OpenAI embeddings 获取文本向量。"""
    from openai import AsyncOpenAI

    settings = get_settings()
    client = AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_api_base,
    )
    resp = await client.embeddings.create(model="text-embedding-3-small", input=text)
    return resp.data[0].embedding


async def search_knowledge(
    db: AsyncSession,
    query: str,
    agent_name: str = "",
    top_k: int = 5,
) -> list[dict]:
    """向量检索知识库，按 agent_name 过滤。"""
    if not check_llm_configured():
        logger.warning("LLM not configured, RAG search skipped")
        return []

    try:
        embedding = await _get_embedding(query)
    except Exception as e:
        logger.error("Failed to get embedding: %s", e)
        return []

    try:
        vector_str = "[" + ",".join(str(v) for v in embedding) + "]"
        stmt = text("""
            SELECT
                kc.id,
                kc.content,
                kc.chunk_index,
                kd.title AS doc_title,
                kd.source_url,
                kd.source_type,
                kc.metadata,
                1 - (kc.embedding <=> CAST(:vec AS vector)) AS similarity
            FROM knowledge_chunks kc
            JOIN knowledge_docs kd ON kc.doc_id = kd.id
            WHERE (:agent = '' OR kd.agent_name = :agent)
            ORDER BY kc.embedding <=> CAST(:vec2 AS vector)
            LIMIT :limit
        """)
        result = await db.execute(stmt, {
            "vec": vector_str,
            "vec2": vector_str,
            "agent": agent_name,
            "limit": top_k,
        })
        rows = result.fetchall()

        return [
            {
                "doc_id": row.id,
                "doc_title": row.doc_title,
                "source_url": row.source_url,
                "source_type": row.source_type,
                "chunk_index": row.chunk_index,
                "content": row.content,
                "section": row.metadata.get("section_title") if row.metadata else None,
                "score": round(float(row.similarity), 4),
            }
            for row in rows
            if row.similarity is not None and float(row.similarity) > 0.5
        ]
    except Exception as e:
        logger.error("RAG search failed: %s", e)
        return []


async def import_knowledge_doc(
    db: AsyncSession,
    title: str,
    content: str,
    agent_name: str = "",
    source_url: str | None = None,
    source_type: str = "manual",
) -> str:
    """导入知识文档并自动切片（简单按段落分块）。"""
    import uuid
    from app.db.models import KnowledgeDoc, KnowledgeChunk

    doc_id = str(uuid.uuid4())
    doc = KnowledgeDoc(
        id=doc_id,
        title=title,
        source_type=source_type,
        source_url=source_url,
        agent_name=agent_name,
        status="active",
    )
    db.add(doc)

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    for idx, para in enumerate(paragraphs):
        chunk = KnowledgeChunk(
            id=str(uuid.uuid4()),
            doc_id=doc_id,
            chunk_index=idx,
            content=para,
        )
        db.add(chunk)

        # 尝试生成 embedding（非阻塞，失败不中断导入）
        if check_llm_configured():
            try:
                chunk.embedding = await _get_embedding(para)
            except Exception as e:
                logger.warning("Embedding generation failed for chunk %d: %s", idx, e)

    await db.flush()
    return doc_id
