from langchain_core.tools import tool


@tool
async def rag_search(query: str, agent_name: str = "", top_k: int = 5) -> str:
    """在知识库中检索与查询相关的内容片段。

    Args:
        query: 搜索查询
        agent_name: 限定搜索的 Agent 名称（可选）
        top_k: 返回结果数量

    Returns:
        检索到的相关内容
    """
    return f"[RAG 检索结果 - 查询: {query}] 知识库检索功能待接入向量数据库后可用。"
