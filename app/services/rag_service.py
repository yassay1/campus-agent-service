from app.services.llm_service import check_llm_configured, LLM_NOT_CONFIGURED_MSG


async def search_knowledge(query: str, agent_name: str = "", top_k: int = 5) -> list[dict]:
    """知识库检索。当前返回占位结果，后续接入向量数据库。"""
    return [
        {
            "doc_id": "placeholder",
            "doc_title": "知识库待导入",
            "chunk_index": 0,
            "content": "知识库数据尚未导入，请先通过数据导入脚本添加文档。",
            "score": 1.0,
        }
    ]


async def import_knowledge_doc(title: str, content: str, agent_name: str = "") -> str:
    """导入知识文档。"""
    return f"文档 '{title}' 已导入，待切片处理。"
