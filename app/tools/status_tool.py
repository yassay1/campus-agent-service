from langchain_core.tools import tool


@tool
async def get_agent_run_status(run_id: str) -> str:
    """获取 Agent 运行记录的状态。

    Args:
        run_id: 运行记录 ID

    Returns:
        运行状态信息
    """
    return f"[Agent 运行记录 - {run_id}] 状态查询结果。"
